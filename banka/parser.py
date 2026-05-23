"""
Banka ekstresi parser — Excel (.xlsx/.xls) ve PDF dosyalarından
işlem satırlarını otomatik okur.

Kullanım:
    from banka.parser import parse_ekstre
    rows = parse_ekstre(dosya_yolu, uzanti)
    # rows: [{"tarih": date, "aciklama": str, "tutar": Decimal, "tip": "giris"|"cikis"}, ...]
"""

import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime, date

logger = logging.getLogger(__name__)


def _temizle_tutar(deger) -> Decimal | None:
    """'1.234,56' veya '1234.56' gibi tutarı Decimal'e çevirir."""
    if deger is None:
        return None
    metin = str(deger).strip().replace(" ", "").replace("\xa0", "")
    # Türkçe format: 1.234,56
    if "," in metin and "." in metin:
        metin = metin.replace(".", "").replace(",", ".")
    elif "," in metin:
        metin = metin.replace(",", ".")
    metin = metin.replace("−", "-").replace("–", "-")
    try:
        return Decimal(metin)
    except InvalidOperation:
        return None


def _temizle_tarih(deger) -> date | None:
    if isinstance(deger, (date, datetime)):
        return deger.date() if isinstance(deger, datetime) else deger
    if deger is None:
        return None
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(deger).strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_excel(dosya_yolu: str) -> list[dict]:
    """Excel dosyasını parse eder.
    
    Desteklenen sütun isimleri (büyük/küçük harf duyarsız):
    - Tarih: tarih, date, işlem tarihi, valör
    - Açıklama: açıklama, aciklama, description, işlem açıklaması
    - Borç/giriş: borç, borc, alacak (pozitif = giriş)
    - Tutar: tutar, amount, tutar (TL)
    """
    try:
        import openpyxl
    except ImportError:
        logger.error("openpyxl kurulu değil. 'pip install openpyxl' çalıştırın.")
        return []

    try:
        wb = openpyxl.load_workbook(dosya_yolu, data_only=True)
        ws = wb.active
    except Exception as exc:
        logger.error("Excel açılamadı: %s", exc)
        return []

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # Başlık satırını bul (ilk dolu satır)
    baslik_satiri = None
    baslik_idx = 0
    for i, row in enumerate(rows):
        if any(cell is not None for cell in row):
            baslik_satiri = [str(c).lower().strip() if c is not None else "" for c in row]
            baslik_idx = i
            break

    if baslik_satiri is None:
        return []

    def kolon_bul(*isimler):
        for isim in isimler:
            for j, baslik in enumerate(baslik_satiri):
                if isim in baslik:
                    return j
        return None

    tarih_kol = kolon_bul("tarih", "date", "valör", "valor")
    aciklama_kol = kolon_bul("açıklama", "aciklama", "description", "işlem")
    tutar_kol = kolon_bul("tutar", "amount")
    borc_kol = kolon_bul("borç", "borc", "çıkış", "cikis")
    alacak_kol = kolon_bul("alacak", "giriş", "giris")

    sonuclar = []
    for row in rows[baslik_idx + 1:]:
        if not any(cell is not None for cell in row):
            continue

        tarih = _temizle_tarih(row[tarih_kol]) if tarih_kol is not None else None
        aciklama = str(row[aciklama_kol]).strip() if aciklama_kol is not None and row[aciklama_kol] else ""

        tutar = None
        tip = "giris"

        if tutar_kol is not None and row[tutar_kol] is not None:
            tutar = _temizle_tutar(row[tutar_kol])
            if tutar is not None:
                tip = "cikis" if tutar < 0 else "giris"
                tutar = abs(tutar)
        elif alacak_kol is not None and row[alacak_kol] is not None:
            tutar = _temizle_tutar(row[alacak_kol])
            tip = "giris"
        elif borc_kol is not None and row[borc_kol] is not None:
            tutar = _temizle_tutar(row[borc_kol])
            tip = "cikis"

        if tarih and tutar and tutar > 0:
            sonuclar.append({
                "tarih": tarih,
                "aciklama": aciklama or "(Açıklama yok)",
                "tutar": tutar,
                "tip": tip,
            })

    logger.info("Excel parse: %d satır bulundu.", len(sonuclar))
    return sonuclar


def parse_pdf(dosya_yolu: str) -> list[dict]:
    """PDF ekstreyi pdfplumber ile parse eder."""
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber kurulu değil. 'pip install pdfplumber' çalıştırın.")
        return []

    sonuclar = []
    try:
        with pdfplumber.open(dosya_yolu) as pdf:
            for sayfa in pdf.pages:
                tablolar = sayfa.extract_tables()
                for tablo in tablolar:
                    if not tablo:
                        continue
                    for satir in tablo[1:]:  # Başlığı atla
                        if not satir or not any(satir):
                            continue
                        # Basit sezgisel: tarih, açıklama, tutar kolonları
                        tarih = _temizle_tarih(satir[0]) if satir[0] else None
                        aciklama = str(satir[1]).strip() if len(satir) > 1 and satir[1] else ""
                        tutar_str = satir[-1] if satir[-1] else None
                        tutar = _temizle_tutar(tutar_str)

                        if tarih and tutar and tutar != 0:
                            tip = "cikis" if tutar < 0 else "giris"
                            sonuclar.append({
                                "tarih": tarih,
                                "aciklama": aciklama or "(Açıklama yok)",
                                "tutar": abs(tutar),
                                "tip": tip,
                            })
    except Exception as exc:
        logger.error("PDF parse hatası: %s", exc)

    logger.info("PDF parse: %d satır bulundu.", len(sonuclar))
    return sonuclar


def parse_ekstre(dosya_yolu: str, uzanti: str) -> list[dict]:
    """Uzantıya göre doğru parser'ı çağırır."""
    uzanti = uzanti.lower().lstrip(".")
    if uzanti in ("xlsx", "xls"):
        return parse_excel(dosya_yolu)
    elif uzanti == "pdf":
        return parse_pdf(dosya_yolu)
    else:
        logger.warning("Desteklenmeyen dosya uzantısı: %s", uzanti)
        return []
