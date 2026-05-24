"""Tüm form widget'larına Bootstrap 5 sınıfları ekleyen mixin."""


class BootstrapFormMixin:
    """Form __init__'inde bu mixin'i kullanarak widget'lara form-control ekler."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            existing = w.attrs.get("class", "")
            widget_class = type(w).__name__

            if widget_class in ("CheckboxInput",):
                w.attrs["class"] = f"{existing} form-check-input".strip()
            elif widget_class in ("Select", "SelectMultiple"):
                w.attrs["class"] = f"{existing} form-select form-select-sm".strip()
            elif widget_class in ("Textarea",):
                w.attrs["class"] = f"{existing} form-control form-control-sm".strip()
            elif widget_class in ("FileInput", "ClearableFileInput"):
                w.attrs["class"] = f"{existing} form-control form-control-sm".strip()
            else:
                w.attrs["class"] = f"{existing} form-control form-control-sm".strip()
