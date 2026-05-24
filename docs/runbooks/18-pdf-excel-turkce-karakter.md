# Runbook 18 — PDF ve Excel Türkçe Karakter Desteği

**Faz:** P1  
**Durum:** ✅ Aktif (2026-05-23)

> Bu runbook bir kez yazıldı — Türkçe karakter sorununda buraya bak.  
> Copilot'a her seferinde hatırlatma gerekmez.

---

## Kural Özeti (TL;DR)

| Platform | Zorunlu | Notlar |
|---|---|---|
| PDF (xhtml2pdf) | `encoding="utf-8"` + DejaVu font | Aksi halde ş,ğ,ü,ö,ç,ı bozulur |
| Excel (openpyxl) | Varsayılan UTF-8, font adı Calibri | Genellikle sorun çıkmaz |
| CSV export | `encoding="utf-8-sig"` | `utf-8-sig` = Excel'de BOM ile doğru açılır |
| HTTP Response (PDF) | `content_type="application/pdf"` | charset ekleme — PDF kendi encoding'ini taşır |

---

## PDF — xhtml2pdf

### Çalışan şablon deseni

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    @font-face {
      font-family: DejaVu;
      src: url("{{ STATIC_ROOT }}/fonts/DejaVuSans.ttf");
    }
    body {
      font-family: DejaVu, sans-serif;
      font-size: 10pt;
    }
  </style>
</head>
<body>
  <!-- içerik -->
</body>
</html>
```

### Çalışan view deseni

```python
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

def pdf_indir(request, pk):
    html = render_to_string("fatura/fatura_pdf.html", {"fatura": fatura})
    buffer = BytesIO()
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("utf-8")),   # ← encode("utf-8") zorunlu
        buffer,
        encoding="utf-8",               # ← encoding parametresi zorunlu
    )
    if pdf.err:
        return HttpResponse("PDF oluşturma hatası", status=500)
    return HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="fatura_{pk}.pdf"'},
    )
```

### Font dosyası kurulumu

```bat
REM DejaVu fontunu static/fonts/ klasörüne koy
mkdir static\fonts
REM DejaVuSans.ttf → https://dejavu-fonts.github.io/ (ücretsiz, açık kaynak)
REM DejaVuSans-Bold.ttf de gerekiyorsa ekle
```

`settings.py` → `STATICFILES_DIRS` veya `STATIC_ROOT`'ta erişilebilir olmalı.

### Sık Hata: `UnicodeEncodeError: 'latin-1' codec`

**Neden:** `pisa.pisaDocument` varsayılan olarak latin-1 dener.  
**Çözüm:** `BytesIO(html.encode("utf-8"))` + `encoding="utf-8"` — her ikisi de zorunlu.

---

## Excel — openpyxl

### Çalışan export deseni

```python
from io import BytesIO
from django.http import HttpResponse
import openpyxl
from openpyxl.styles import Font, Alignment

def excel_indir(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rapor"

    # Başlık satırı
    basliklar = ["Tarih", "Açıklama", "Tutar (₺)", "Döviz"]
    for col, baslik in enumerate(basliklar, 1):
        hucre = ws.cell(row=1, column=col, value=baslik)
        hucre.font = Font(bold=True)
        hucre.alignment = Alignment(horizontal="center")

    # Veri satırları — Türkçe karakterler sorunsuz
    for row_idx, veri in enumerate(veriler, 2):
        ws.cell(row=row_idx, column=1, value=veri["tarih"])
        ws.cell(row=row_idx, column=2, value=veri["aciklama"])  # ş,ğ,ü OK
        ws.cell(row=row_idx, column=3, value=float(veri["tutar"]))
        ws.cell(row=row_idx, column=4, value=veri["doviz"])

    # Sütun genişliği otomatik
    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="rapor.xlsx"'},
    )
```

**Not:** openpyxl varsayılan olarak UTF-8 kullanır. Font adı `Calibri` çalışır.  
Türkçe için ekstra ayar gerekmez.

---

## CSV — Excel'de Doğru Açılmak İçin

```python
import csv
from django.http import HttpResponse

def csv_indir(request):
    response = HttpResponse(
        content_type="text/csv; charset=utf-8-sig",  # ← utf-8-sig = BOM ekler
    )
    response["Content-Disposition"] = 'attachment; filename="liste.csv"'

    writer = csv.writer(response, delimiter=";")  # Türkiye'de ; ayraç standart
    writer.writerow(["Kod", "Ünvan", "Tutar"])
    for row in veriler:
        writer.writerow([row["kod"], row["unvan"], row["tutar"]])
    return response
```

**Neden `utf-8-sig`?** Excel, BOM (Byte Order Mark) olmadan UTF-8 CSV'yi ANSI olarak  
açar → Türkçe karakterler bozulur. `utf-8-sig` BOM ekler, Excel doğru okur.

---

## Kontrol Listesi — PDF/Excel Üretiminde

- [ ] PDF: HTML şablonunda `<meta charset="UTF-8">` var mı?
- [ ] PDF: `pisa.pisaDocument(..., encoding="utf-8")` var mı?
- [ ] PDF: `BytesIO(html.encode("utf-8"))` kullanıldı mı?
- [ ] PDF: DejaVu fontu `static/fonts/` altında mı?
- [ ] Excel: `HttpResponse` `content_type` doğru mu?
- [ ] CSV: `utf-8-sig` encoding kullanıldı mı?
- [ ] CSV: Ayraç `;` mi (Türkiye standardı)?
