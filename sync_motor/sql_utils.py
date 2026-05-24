"""SQL literal escape ve whitelist yardımcıları.

Mikro `SqlVeriOkuV2` parametrik sorgu desteklemediğinden tüm değerler SQL
metni içine güvenli biçimde gömülmelidir. Bu modüldeki yardımcılar dışında
ham f-string ile değer eklemekten kaçının.
"""
from __future__ import annotations

from datetime import date, datetime


def sql_str(deger: str | None, maks_uzunluk: int = 500) -> str:
    """String değerini SQL literali olarak güvenli biçimde tırnak içine alır.

    - Tek tırnaklar çiftlenir (T-SQL standardı).
    - NUL bytları kaldırılır.
    - ``maks_uzunluk`` üzeri girdiler kırpılır (DoS koruması).
    - ``None`` → ``"NULL"``.
    """
    if deger is None:
        return "NULL"
    s = str(deger).replace("\x00", "")
    if len(s) > maks_uzunluk:
        s = s[:maks_uzunluk]
    return "'" + s.replace("'", "''") + "'"


def sql_like(deger: str | None, maks_uzunluk: int = 200) -> str:
    """LIKE deseni için %_[] meta karakterlerini de kaçışlar.

    Sonuç: ``'%aranan%'`` formatında, ESCAPE '\\' ile birlikte kullanılmalıdır.
    """
    if deger is None:
        return "''"
    s = str(deger).replace("\x00", "")
    if len(s) > maks_uzunluk:
        s = s[:maks_uzunluk]
    s = (
        s.replace("\\", "\\\\")
         .replace("%", "\\%")
         .replace("_", "\\_")
         .replace("[", "\\[")
    )
    return "'%" + s.replace("'", "''") + "%'"


def sql_int(deger, varsayilan: int = 0) -> int:
    """Değeri int'e çevirir; başarısız olursa varsayılanı döner."""
    try:
        return int(deger)
    except (TypeError, ValueError):
        return varsayilan


def sql_date(deger) -> str:
    """``date``/``datetime``/``"YYYY-MM-DD"`` → ``'YYYY-MM-DD'`` literali.

    Geçersiz girdi ``ValueError`` fırlatır — view tarafında yakalanmalıdır.
    """
    if isinstance(deger, datetime):
        deger = deger.date()
    if isinstance(deger, date):
        return "'" + deger.strftime("%Y-%m-%d") + "'"
    s = str(deger).strip()[:10]
    # YYYY-MM-DD formatını doğrula
    datetime.strptime(s, "%Y-%m-%d")
    return "'" + s + "'"


def whitelist(deger: str | None, izinli: dict[str, str], varsayilan_anahtar: str) -> str:
    """`deger` izinli sözlükte ise karşılığını, değilse varsayılanı döner.

    ORDER BY / sütun adı gibi SQL'e doğrudan gömülen değerler için kullanın.
    """
    if deger in izinli:
        return izinli[deger]
    return izinli[varsayilan_anahtar]
