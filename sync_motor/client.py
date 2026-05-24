"""
MikroApiClient — Mikro ERP API ile iletişim.
Referans: C:\\more-jumpbridge (MikroAPI.postman_collection_V17.json)

Gerçek API formatı:
  POST http://{SUNUCU}:{PORT}/Api/APIMethods/{endpoint}
  Body: {"Mikro": {"FirmaKodu":..., "CalismaYili":..., "KullaniciKodu":...,
                   "Sifre": MD5("YYYY-MM-DD sifre"), "ApiKey":...},
         ...ekstra params...}

HealthCheck: GET http://{SUNUCU}:{PORT}/Api/APIMethods/HealthCheck
"""

import hashlib
import logging
from datetime import date
from typing import Optional

import requests

logger = logging.getLogger("mikro_sync")


class MikroApiHatasi(Exception):
    """Mikro API bağlantı veya yanıt hatası."""
    pass


class MikroApiClient:
    """
    Mikro ERP REST API istemcisi.

    Kullanım:
        client = MikroApiClient(firma_ayar)
        faturalar = client.gelen_faturalar(date(2026,1,1), date(2026,1,31))
    """

    def __init__(self, firma_ayar, sunucu_ip: str = None):
        self.firma_ayar = firma_ayar
        _sunucu = sunucu_ip or firma_ayar.mikro_sunucu
        self.base_url = f"http://{_sunucu}:{firma_ayar.mikro_port}/Api/APIMethods"
        self.firma_kodu = firma_ayar.firma_kodu
        self.calisma_yili = firma_ayar.calisma_yili  # string: "2025"
        self.kullanici = firma_ayar.mikro_kullanici
        self.sifre = firma_ayar.sifre_al()
        self.api_key = firma_ayar.mikro_api_key
        self.timeout = 30  # saniye

    def _sifre_hash(self) -> str:
        """
        Günlük MD5 hash.
        Format: MD5("YYYY-MM-DD " + sifre)
        Referans: C:\\more-jumpbridge\\config\\.env.example
        """
        bugun = date.today().strftime("%Y-%m-%d")
        return hashlib.md5(f"{bugun} {self.sifre}".encode("utf-8")).hexdigest()

    def _mikro_obj(self, calisma_yili: str = None) -> dict:
        """Her istekte gönderilen kimlik nesnesi."""
        return {
            "ApiKey": self.api_key,
            "CalismaYili": calisma_yili or self.calisma_yili,
            "FirmaKodu": self.firma_kodu,
            "KullaniciKodu": self.kullanici,
            "Sifre": self._sifre_hash(),
            "FirmaNo": 0,
            "SubeNo": 0,
        }

    def _post(self, endpoint: str, ekstra_params: Optional[dict] = None, calisma_yili: str = None) -> dict:
        """
        Mikro API'ye POST isteği gönderir.
        ekstra_params: Mikro objesinin DIŞINA eklenen parametreler (IlkTarih, SonTarih vb.)
        calisma_yili: Varsayılanın üzerine yazmak için (evrak yılı farklıysa)
        """
        url = f"{self.base_url}/{endpoint}"
        payload = {"Mikro": self._mikro_obj(calisma_yili=calisma_yili)}
        if ekstra_params:
            payload.update(ekstra_params)

        logger.debug("Mikro API → %s", endpoint)

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise MikroApiHatasi(f"Mikro API bağlantı hatası ({self.firma_ayar.mikro_sunucu}): {e}") from e
        except requests.exceptions.Timeout:
            raise MikroApiHatasi(f"Mikro API zaman aşımı ({self.timeout}s)") from None
        except requests.exceptions.HTTPError as e:
            raise MikroApiHatasi(f"Mikro API HTTP hatası {response.status_code}: {e}") from e

        try:
            veri = response.json()
        except ValueError as e:
            raise MikroApiHatasi(f"Mikro API geçersiz JSON yanıtı: {e}") from e

        if isinstance(veri, dict) and veri.get("Hata"):
            raise MikroApiHatasi(f"Mikro API hatası: {veri.get('Hata')}")

        if isinstance(veri, list):
            logger.debug("Mikro API ← %s | liste, %d eleman", endpoint, len(veri))
        else:
            logger.debug("Mikro API ← %s | dict, anahtarlar=%s | içerik=%s", endpoint, list(veri.keys()) if isinstance(veri, dict) else "?", str(veri)[:500])
        return veri

    def baglanti_test(self) -> dict:
        """
        Bağlantıyı test eder. {'basarili': True/False, 'mesaj': str}
        HealthCheck endpoint'i GET ile çalışır, body gerektirmez.
        """
        try:
            url = f"{self.base_url}/HealthCheck"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return {"basarili": True, "mesaj": "Bağlantı başarılı"}
        except requests.exceptions.ConnectionError as e:
            return {"basarili": False, "mesaj": f"Bağlantı hatası: {e}"}
        except requests.exceptions.Timeout:
            return {"basarili": False, "mesaj": "Zaman aşımı"}
        except Exception as e:
            return {"basarili": False, "mesaj": str(e)}

    def gelen_faturalar(self, baslangic: date, bitis: date) -> list:
        """
        Gelen e-faturaları çeker (GelenFaturalarV2).
        Döner: [{"fat_Guid":..., "fat_evrak_seri":..., "fat_evrak_sira":...,
                  "fat_tarih":..., "fat_cari_kod":..., "fat_cari_unvan":...,
                  "fat_kdv_haric":..., "fat_kdv":..., "fat_toplam":...}, ...]
        """
        # CalismaYili evrak tarihinin yılına göre dinamik seçilir
        yil = str(baslangic.year)
        sonuc = self._post("GelenFaturalarV2", {
            "IlkTarih": baslangic.strftime("%Y-%m-%d"),
            "SonTarih": bitis.strftime("%Y-%m-%d"),
        }, calisma_yili=yil)
        # API ya liste ya da sarmalı dict döndürebilir
        if isinstance(sonuc, list):
            return sonuc
        if isinstance(sonuc, dict):
            # Bilinen anahtarları dene
            for key in ("Faturalar", "faturalar", "Data", "data", "Result", "result",
                        "Items", "items", "Liste", "liste", "Rows", "rows"):
                if key in sonuc and isinstance(sonuc[key], list):
                    logger.debug("GelenFaturalarV2: '%s' anahtarında %d fatura", key, len(sonuc[key]))
                    return sonuc[key]
            # Hiç list değer yoksa ilk list değeri dön
            for k, v in sonuc.items():
                if isinstance(v, list):
                    logger.debug("GelenFaturalarV2: fallback '%s' anahtarında %d fatura", k, len(v))
                    return v
            logger.warning("GelenFaturalarV2: dict yanıt liste içermiyor, anahtarlar=%s", list(sonuc.keys()))
        return []

    def fatura_xml(self, fat_guid: str) -> str:
        """Belirli bir faturanın e-Belge XML içeriğini çeker (EBelgeXmlV2)."""
        sonuc = self._post("EBelgeXmlV2", {"fat_Guid": fat_guid})
        if isinstance(sonuc, dict):
            return sonuc.get("Xml", sonuc.get("xml", ""))
        return str(sonuc)

    def fatura_pdf(self, fat_guid: str) -> bytes:
        """Belirli bir faturanın PDF içeriğini çeker (GelenFaturaPdfV2)."""
        import base64
        sonuc = self._post("GelenFaturaPdfV2", {"fat_Guid": fat_guid})
        if isinstance(sonuc, dict):
            pdf_b64 = sonuc.get("Pdf", sonuc.get("pdf", ""))
            return base64.b64decode(pdf_b64) if pdf_b64 else b""
        return b""

    def cari_hesaplar(self, arama: str = "") -> list:
        """
        Mikro cari hesap listesini çeker (CariListesiV2).
        Döner: [{"cari_kod":..., "cari_unvan1":..., "cari_vkn_vd":...}, ...]
        """
        where = "cari_baglanti_tipi=0"
        if arama:
            # Tek tırnak kaçışı — SQL injection koruması
            temiz = arama.replace("'", "''")
            where += f" and (cari_unvan1 like '%{temiz}%' or cari_kod like '%{temiz}%')"

        sonuc = self._post("CariListesiV2", {
            "FieldName": "cari_kod, cari_unvan1, cari_unvan2, cari_vkn_vd, cari_baglanti_tipi",
            "WhereStr": where,
            "Sort": "cari_unvan1",
            "Size": "1000",
            "Index": 0,
        })
        if isinstance(sonuc, list):
            return sonuc
        if isinstance(sonuc, dict):
            for key in ("Cariler", "cariler", "Data", "data"):
                if key in sonuc:
                    return sonuc[key]
        return []

    def sql_oku(self, sorgu: str) -> list:
        """
        Mikro veritabanında serbest SQL sorgusu çalıştırır (SqlVeriOkuV2).
        Döner: [{"kolon1": deger, "kolon2": deger, ...}, ...]
        """
        sonuc = self._post("SqlVeriOkuV2", {"SqlStr": sorgu})
        if isinstance(sonuc, list):
            return sonuc
        if isinstance(sonuc, dict):
            for key in ("Data", "data", "Rows", "rows", "Result", "result", "Liste", "liste"):
                if key in sonuc and isinstance(sonuc[key], list):
                    return sonuc[key]
        return []

    def stok_kartlari(self, arama: str = "") -> list:
        """
        Mikro stok kartı listesini çeker (StokListesiV2).
        Döner: [{"sto_kod":..., "sto_isim":..., "sto_birim1_ad":...}, ...]
        """
        sonuc = self._post("StokListesiV2", {
            "StokKod": arama,
            "TarihTipi": 2,
            "IlkTarih": "2020-01-01",
            "SonTarih": date.today().strftime("%Y-%m-%d"),
            "Sort": "sto_kod",
            "Size": "1000",
            "Index": 0,
        })
        if isinstance(sonuc, list):
            return sonuc
        if isinstance(sonuc, dict):
            for key in ("Stoklar", "stoklar", "Data", "data"):
                if key in sonuc:
                    return sonuc[key]
        return []


