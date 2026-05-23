"""
Stok Değerleme Yöntemleri — VUK Madde 274
==========================================
Desteklenen yöntemler:
  • Ağırlıklı Ortalama Maliyet (WAC — Weighted Average Cost)
  • FIFO — İlk Giren İlk Çıkar (First In First Out)

Her fonksiyon şu dict'i döndürür:
  {
    "birim_maliyet":  Decimal,
    "toplam_deger":   Decimal,
    "mevcut_adet":    Decimal,
    "yontem_adi":     str,
    "fifo_katmanlar": list[dict]  # yalnızca FIFO
  }
"""

from collections import deque
from decimal import ROUND_HALF_UP, Decimal


def _d(val) -> Decimal:
    """Herhangi bir değeri Decimal'e güvenli çevirir."""
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val or 0))


# ─────────────────────────────────────────────────────────────────────────────
# Ağırlıklı Ortalama Maliyet
# ─────────────────────────────────────────────────────────────────────────────

def ortalama_maliyet(urun) -> dict:
    """
    Ağırlıklı Ortalama Maliyet yöntemi.

    Tüm giriş hareketlerinin fiyat-ağırlıklı ortalamasını alır.
    Ortalama = Σ(miktar × birim_fiyat) / Σ(miktar)
    ve bu ortalama mevcut stok adediyle çarpılır.
    """
    girisler = urun.hareketler.filter(
        tip__in=["giris", "sayim"]
    ).order_by("tarih", "olusturuldu")

    toplam_miktar = Decimal("0")
    toplam_deger  = Decimal("0")

    for h in girisler:
        fiyat = _d(h.birim_fiyat)
        if fiyat > 0:
            toplam_miktar += _d(h.miktar)
            toplam_deger  += _d(h.miktar) * fiyat

    mevcut = _d(urun.mevcut_stok)

    if toplam_miktar <= 0 or mevcut <= 0:
        return {
            "birim_maliyet":  Decimal("0"),
            "toplam_deger":   Decimal("0"),
            "mevcut_adet":    mevcut,
            "yontem_adi":     "Ağırlıklı Ortalama",
            "fifo_katmanlar": [],
        }

    birim = (toplam_deger / toplam_miktar).quantize(
        Decimal("0.0001"), ROUND_HALF_UP
    )
    return {
        "birim_maliyet":  birim,
        "toplam_deger":   (birim * mevcut).quantize(Decimal("0.01"), ROUND_HALF_UP),
        "mevcut_adet":    mevcut,
        "yontem_adi":     "Ağırlıklı Ortalama",
        "fifo_katmanlar": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# FIFO — İlk Giren İlk Çıkar
# ─────────────────────────────────────────────────────────────────────────────

def fifo_maliyet(urun) -> dict:
    """
    FIFO yöntemi.

    Hareketler kronolojik sırada işlenir:
      • giris / sayim  → kuyruğa eklenir (tarih, fiyat, miktar)
      • cikis          → kuyruğun başından tüketilir

    Geriye kalan kuyruk = stokta duran ürünlerin maliyet katmanları.
    """
    hareketler = list(urun.hareketler.order_by("tarih", "olusturuldu"))

    # FIFO kuyruğu: liste elemanı [kalan_miktar, birim_fiyat, tarih_str]
    fifo_queue: deque = deque()

    for h in hareketler:
        miktar = _d(h.miktar)
        fiyat  = _d(h.birim_fiyat)
        tarih  = str(h.tarih)

        if h.tip in ("giris", "sayim"):
            fifo_queue.append([miktar, fiyat, tarih])

        elif h.tip == "cikis":
            kalan = miktar
            while kalan > 0 and fifo_queue:
                batch_miktar, batch_fiyat, batch_tarih = fifo_queue[0]
                if batch_miktar <= kalan:
                    kalan -= batch_miktar
                    fifo_queue.popleft()
                else:
                    fifo_queue[0][0] -= kalan
                    kalan = Decimal("0")

    mevcut_adet  = sum(_d(b[0]) for b in fifo_queue)
    toplam_deger = sum(_d(b[0]) * _d(b[1]) for b in fifo_queue)

    if mevcut_adet <= 0:
        return {
            "birim_maliyet":  Decimal("0"),
            "toplam_deger":   Decimal("0"),
            "mevcut_adet":    Decimal("0"),
            "yontem_adi":     "FIFO",
            "fifo_katmanlar": [],
        }

    birim = (toplam_deger / mevcut_adet).quantize(
        Decimal("0.0001"), ROUND_HALF_UP
    )

    katmanlar = [
        {
            "miktar":       b[0],
            "birim_fiyat":  b[1],
            "deger":        (_d(b[0]) * _d(b[1])).quantize(Decimal("0.01"), ROUND_HALF_UP),
            "tarih":        b[2],
        }
        for b in fifo_queue
        if _d(b[0]) > 0
    ]

    return {
        "birim_maliyet":  birim,
        "toplam_deger":   toplam_deger.quantize(Decimal("0.01"), ROUND_HALF_UP),
        "mevcut_adet":    mevcut_adet,
        "yontem_adi":     "FIFO",
        "fifo_katmanlar": katmanlar,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────────────────────────────────────

def urun_degerleme(urun) -> dict:
    """Ürünün seçili yöntemine göre değerleme bilgisini döndürür."""
    yontem = getattr(urun, "degerleme_yontemi", "ortalama")
    if yontem == "fifo":
        return fifo_maliyet(urun)
    return ortalama_maliyet(urun)
