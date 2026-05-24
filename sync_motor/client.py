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

    def _post(
        self, endpoint: str, ekstra_params: Optional[dict] = None, calisma_yili: str = None
    ) -> dict:
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
            raise MikroApiHatasi(
                f"Mikro API bağlantı hatası ({self.firma_ayar.mikro_sunucu}): {e}"
            ) from e
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
            logger.debug(
                "Mikro API ← %s | dict, anahtarlar=%s | içerik=%s",
                endpoint,
                list(veri.keys()) if isinstance(veri, dict) else "?",
                str(veri)[:500],
            )
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

    @staticmethod
    def _extract_list_response(
        sonuc,
        endpoint: str,
        tercih_anahtarlar: tuple[str, ...] = (
            "Data",
            "data",
            "Result",
            "result",
            "Items",
            "items",
            "Liste",
            "liste",
            "Rows",
            "rows",
        ),
    ) -> list:
        """Mikro API yanıtından liste içeriğini çıkarır.

        Yanıt doğrudan ``list`` ise döndürür. ``dict`` ise önce tercih
        anahtarlarını dener, sonra ilk ``list`` değerini fallback olarak alır.
        Hiçbir liste bulunamazsa boş liste döner ve uyarı loglanır.
        """
        if isinstance(sonuc, list):
            return sonuc
        if not isinstance(sonuc, dict):
            return []
        for key in tercih_anahtarlar:
            v = sonuc.get(key)
            if isinstance(v, list):
                return v
        # Fallback: ilk list değer
        for k, v in sonuc.items():
            if isinstance(v, list):
                logger.debug("%s: fallback '%s' anahtarında %d eleman", endpoint, k, len(v))
                return v
        logger.warning(
            "%s: dict yanıt liste içermiyor, anahtarlar=%s", endpoint, list(sonuc.keys())
        )
        return []

    def gelen_faturalar(self, baslangic: date, bitis: date) -> list:
        """
        Gelen e-faturaları çeker (GelenFaturalarV2).
        Döner: [{"fat_Guid":..., "fat_evrak_seri":..., "fat_evrak_sira":...,
                  "fat_tarih":..., "fat_cari_kod":..., "fat_cari_unvan":...,
                  "fat_kdv_haric":..., "fat_kdv":..., "fat_toplam":...}, ...]
        """
        # CalismaYili evrak tarihinin yılına göre dinamik seçilir
        yil = str(baslangic.year)
        sonuc = self._post(
            "GelenFaturalarV2",
            {
                "IlkTarih": baslangic.strftime("%Y-%m-%d"),
                "SonTarih": bitis.strftime("%Y-%m-%d"),
            },
            calisma_yili=yil,
        )
        return self._extract_list_response(
            sonuc,
            "GelenFaturalarV2",
            tercih_anahtarlar=(
                "Faturalar",
                "faturalar",
                "Data",
                "data",
                "Result",
                "result",
                "Items",
                "items",
                "Liste",
                "liste",
                "Rows",
                "rows",
            ),
        )

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

        sonuc = self._post(
            "CariListesiV2",
            {
                "FieldName": "cari_kod, cari_unvan1, cari_unvan2, cari_vkn_vd, cari_baglanti_tipi",
                "WhereStr": where,
                "Sort": "cari_unvan1",
                "Size": "1000",
                "Index": 0,
            },
        )
        return self._extract_list_response(
            sonuc,
            "CariListesiV2",
            tercih_anahtarlar=(
                "Cariler",
                "cariler",
                "Data",
                "data",
                "Result",
                "result",
                "Items",
                "items",
            ),
        )

    def sql_oku(self, sorgu: str) -> list:
        """
        Mikro veritabanında serbest SQL sorgusu çalıştırır (SqlVeriOkuV2).
        Döner: [{"kolon1": deger, "kolon2": deger, ...}, ...]

        Yanıt yapısı: {"result": [{"StatusCode": 200, "Data": [{"SQLResult1": [...]}]}]}
        """
        sonuc = self._post("SqlVeriOkuV2", {"SQLSorgu": sorgu})
        try:
            result = sonuc.get("result", []) if isinstance(sonuc, dict) else []
            if result and isinstance(result, list):
                kayit = result[0]
                if kayit.get("IsError") or (kayit.get("StatusCode", 200) not in (200, 0)):
                    logger.warning(
                        "sql_oku hatası [%s]: %s",
                        kayit.get("StatusCode"),
                        kayit.get("ErrorMessage"),
                    )
                    return []
                data = kayit.get("Data") or []
                if data and isinstance(data, list):
                    sql_result = data[0].get("SQLResult1") or []
                    return sql_result if isinstance(sql_result, list) else []
        except Exception as e:
            logger.error("sql_oku parse hatası: %s", e)
        return []

    def stok_kartlari(self, arama: str = "") -> list:
        """
        Mikro stok kartı listesini çeker (StokListesiV2).
        Döner: [{"sto_kod":..., "sto_isim":..., "sto_birim1_ad":...}, ...]
        """
        sonuc = self._post(
            "StokListesiV2",
            {
                "StokKod": arama,
                "TarihTipi": 2,
                "IlkTarih": "2020-01-01",
                "SonTarih": date.today().strftime("%Y-%m-%d"),
                "Sort": "sto_kod",
                "Size": "1000",
                "Index": 0,
            },
        )
        return self._extract_list_response(
            sonuc,
            "StokListesiV2",
            tercih_anahtarlar=(
                "Stoklar",
                "stoklar",
                "Data",
                "data",
                "Result",
                "result",
                "Items",
                "items",
            ),
        )
