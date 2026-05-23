"""
GİB UBL-TR 2.1 formatında e-fatura XML üreticisi.

Kullanım:
    from fatura.efatura import ubl_xml_uret
    xml_bytes = ubl_xml_uret(fatura)

Üretilen XML GİB e-Fatura portalına (efatura.gib.gov.tr) manuel olarak yüklenebilir.
"""
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


# GİB UBL-TR namespace tanımları
NS = {
    "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "xmlns:ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"

def _cbc(tag):
    return f"{{{CBC}}}{tag}"

def _cac(tag):
    return f"{{{CAC}}}{tag}"


def ubl_xml_uret(fatura) -> bytes:
    """
    Fatura nesnesinden GİB UBL-TR 2.1 uyumlu XML üretir.
    Döndürür: utf-8 encoded bytes
    """
    # Kök eleman
    root = Element("Invoice")
    for attr, val in NS.items():
        root.set(attr, val)

    # ── Başlık ────────────────────────────────────────────────────────────
    _sub(root, _cbc("UBLVersionID"), "2.1")
    _sub(root, _cbc("CustomizationID"), "TR1.2")
    _sub(root, _cbc("ProfileID"), "TICARIFATURA")
    _sub(root, _cbc("ID"), str(fatura.fatura_no))
    _sub(root, _cbc("CopyIndicator"), "false")
    _sub(root, _cbc("UUID"), str(fatura.e_fatura_uuid).upper())
    _sub(root, _cbc("IssueDate"), fatura.tarih.strftime("%Y-%m-%d"))
    _sub(root, _cbc("IssueTime"), "00:00:00")
    _sub(root, _cbc("InvoiceTypeCode"), "SATIS")
    _sub(root, _cbc("DocumentCurrencyCode"), fatura.para_birimi or "TRY")
    _sub(root, _cbc("LineCountNumeric"), str(fatura.kalemler.count()))

    # Açıklama (isteğe bağlı)
    if fatura.aciklama:
        _sub(root, _cbc("Note"), fatura.aciklama)

    # Vade tarihi
    if fatura.vade_tarihi:
        pb = SubElement(root, _cac("PaymentTerms"))
        _sub(pb, _cbc("Note"), "Vadeli")
        _sub(pb, _cbc("PaymentDueDate"), fatura.vade_tarihi.strftime("%Y-%m-%d"))

    # ── Satıcı (AccountingSupplierParty) ─────────────────────────────────
    # Ayarlardan firma bilgisi çekilir (yoksa placeholder)
    try:
        from django.conf import settings as djsettings
        firma_adi = getattr(djsettings, "FIRMA_ADI", "Firma Adı")
        firma_vkn = getattr(djsettings, "FIRMA_VKN", "0000000000")
        firma_vd = getattr(djsettings, "FIRMA_VERGI_DAIRESI", "")
        firma_adres = getattr(djsettings, "FIRMA_ADRES", "")
    except Exception:
        firma_adi = "Firma Adı"
        firma_vkn = "0000000000"
        firma_vd = ""
        firma_adres = ""

    supplier = SubElement(root, _cac("AccountingSupplierParty"))
    sp = SubElement(supplier, _cac("Party"))
    _parti_vkn(sp, firma_vkn, firma_vd)
    pn = SubElement(sp, _cac("PartyName"))
    _sub(pn, _cbc("Name"), firma_adi)
    if firma_adres:
        pa = SubElement(sp, _cac("PostalAddress"))
        _sub(pa, _cbc("StreetName"), firma_adres)

    # ── Alıcı (AccountingCustomerParty) ──────────────────────────────────
    cari = fatura.cari
    customer = SubElement(root, _cac("AccountingCustomerParty"))
    cp = SubElement(customer, _cac("Party"))
    _parti_vkn(cp, cari.vergi_no or "0000000000", cari.vergi_dairesi or "")
    cn = SubElement(cp, _cac("PartyName"))
    _sub(cn, _cbc("Name"), cari.ad)
    if cari.adres:
        ca = SubElement(cp, _cac("PostalAddress"))
        _sub(ca, _cbc("StreetName"), cari.adres)
    if cari.email:
        cc = SubElement(cp, _cac("Contact"))
        _sub(cc, _cbc("ElectronicMail"), cari.email)

    # ── Vergi toplamları ──────────────────────────────────────────────────
    kdv_ozeti = fatura.kdv_ozeti
    for oran, degerler in kdv_ozeti.items():
        ts = SubElement(root, _cac("TaxTotal"))
        _sub(ts, _cbc("TaxAmount"), _para(degerler["kdv"]), currencyID=fatura.para_birimi)
        tsc = SubElement(ts, _cac("TaxSubtotal"))
        _sub(tsc, _cbc("TaxableAmount"), _para(degerler["matrah"]), currencyID=fatura.para_birimi)
        _sub(tsc, _cbc("TaxAmount"), _para(degerler["kdv"]), currencyID=fatura.para_birimi)
        tc = SubElement(tsc, _cac("TaxCategory"))
        _sub(tc, _cbc("Percent"), str(oran))
        ts2 = SubElement(tc, _cac("TaxScheme"))
        _sub(ts2, _cbc("Name"), "KDV")
        _sub(ts2, _cbc("TaxTypeCode"), "0015")

    # ── Genel toplamlar ───────────────────────────────────────────────────
    lm = SubElement(root, _cac("LegalMonetaryTotal"))
    _sub(lm, _cbc("LineExtensionAmount"), _para(fatura.kdv_haric_toplam), currencyID=fatura.para_birimi)
    _sub(lm, _cbc("TaxExclusiveAmount"), _para(fatura.kdv_haric_toplam), currencyID=fatura.para_birimi)
    _sub(lm, _cbc("TaxInclusiveAmount"), _para(fatura.genel_toplam), currencyID=fatura.para_birimi)
    _sub(lm, _cbc("PayableAmount"), _para(fatura.genel_toplam), currencyID=fatura.para_birimi)

    # ── Fatura kalemleri ──────────────────────────────────────────────────
    for i, kalem in enumerate(fatura.kalemler.all(), start=1):
        il = SubElement(root, _cac("InvoiceLine"))
        _sub(il, _cbc("ID"), str(i))
        _sub(il, _cbc("InvoicedQuantity"), _miktar(kalem.miktar), unitCode=kalem.birim or "C62")
        _sub(il, _cbc("LineExtensionAmount"), _para(kalem.kdv_haric_tutar), currencyID=fatura.para_birimi)

        # KDV
        it = SubElement(il, _cac("TaxTotal"))
        _sub(it, _cbc("TaxAmount"), _para(kalem.kdv_tutari), currencyID=fatura.para_birimi)
        its = SubElement(it, _cac("TaxSubtotal"))
        _sub(its, _cbc("TaxableAmount"), _para(kalem.kdv_haric_tutar), currencyID=fatura.para_birimi)
        _sub(its, _cbc("TaxAmount"), _para(kalem.kdv_tutari), currencyID=fatura.para_birimi)
        itc = SubElement(its, _cac("TaxCategory"))
        _sub(itc, _cbc("Percent"), str(kalem.kdv_orani))
        its2 = SubElement(itc, _cac("TaxScheme"))
        _sub(its2, _cbc("Name"), "KDV")
        _sub(its2, _cbc("TaxTypeCode"), "0015")

        # Kalem açıklaması
        item = SubElement(il, _cac("Item"))
        _sub(item, _cbc("Description"), kalem.aciklama)
        _sub(item, _cbc("Name"), kalem.aciklama[:50])

        # Fiyat
        price = SubElement(il, _cac("Price"))
        _sub(price, _cbc("PriceAmount"), _para(kalem.birim_fiyat), currencyID=fatura.para_birimi)

    # Güzel formatlanmış XML döndür
    xmlstr = tostring(root, encoding="unicode", xml_declaration=False)
    dom = parseString(f'<?xml version="1.0" encoding="UTF-8"?>\n{xmlstr}')
    return dom.toprettyxml(indent="  ", encoding="UTF-8")


# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────

def _sub(parent, tag, text="", **attrs):
    el = SubElement(parent, tag)
    if text:
        el.text = str(text)
    for k, v in attrs.items():
        el.set(k, str(v))
    return el


def _para(deger) -> str:
    return f"{Decimal(str(deger)):.2f}"


def _miktar(deger) -> str:
    return f"{Decimal(str(deger)):.3f}"


def _parti_vkn(parent, vkn: str, vd: str):
    pi = SubElement(parent, _cac("PartyIdentification"))
    vid = SubElement(pi, _cbc("ID"))
    vid.set("schemeID", "VKN" if len(vkn.strip()) == 10 else "TCKN")
    vid.text = vkn.strip()
    if vd:
        pi2 = SubElement(parent, _cac("PartyIdentification"))
        vid2 = SubElement(pi2, _cbc("ID"))
        vid2.set("schemeID", "VERGI_DAIRESI")
        vid2.text = vd.strip()
