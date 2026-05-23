"""
GitHub Releases API üzerinden otomatik sürüm kontrolü.
Sonuç 24 saat cache'lenir — her istekte API çağrısı yapılmaz.
"""
import json
import logging
import urllib.request

from django.core.cache import cache

logger = logging.getLogger("muhasebe")

CACHE_KEY = "github_surum_kontrol"
CACHE_SURE = 60 * 60 * 24  # 24 saat


def _surum_karsilastir(mevcut: str, yeni: str) -> bool:
    """Semantic versioning: yeni > mevcut ise True döner."""
    try:
        m = tuple(int(x) for x in mevcut.lstrip("v").split("."))
        y = tuple(int(x) for x in yeni.lstrip("v").split("."))
        return y > m
    except Exception:
        return False


def github_surum_kontrol(mevcut_versiyon: str) -> dict:
    """
    GitHub Releases API'dan son sürümü kontrol et.
    Returns: {"yeni_var": bool, "surum": str|None, "url": str|None}
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    try:
        url = "https://api.github.com/repos/acetin75/muhasebe-buro-crm/releases/latest"
        req = urllib.request.Request(
            url, headers={"User-Agent": "MuhasebeBuro/1.0 VersionCheck"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
        son_surum = data.get("tag_name", "").lstrip("v")
        github_url = data.get("html_url", "https://github.com/acetin75/muhasebe-buro-crm/releases")
        yeni_var = bool(son_surum) and _surum_karsilastir(mevcut_versiyon, son_surum)
        sonuc = {"yeni_var": yeni_var, "surum": son_surum, "url": github_url}
        logger.debug("Sürüm kontrolü: mevcut=%s, GitHub=%s, yeni_var=%s", mevcut_versiyon, son_surum, yeni_var)
    except Exception as e:
        logger.debug("GitHub sürüm kontrolü başarısız: %s", e)
        sonuc = {"yeni_var": False, "surum": None, "url": None}

    cache.set(CACHE_KEY, sonuc, CACHE_SURE)
    return sonuc
