from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# Sürüm numarası (VERSION dosyasından okunur)
_version_file = BASE_DIR / "VERSION"
APP_VERSION = _version_file.read_text(encoding="utf-8").strip() if _version_file.exists() else "?"

SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-muhasebe-buro-local-secret-key-degistirin",
)

DEBUG = config("DEBUG", default=True, cast=bool)

# Güvensiz varsayılan anahtar üretimde kullanılmasın (fail-fast).
if not DEBUG and SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError(
        "SECRET_KEY güvensiz varsayılan değer taşıyor. "
        ".env dosyasına güçlü bir SECRET_KEY tanımlayın. "
        "Üretmek için: python -c \"from django.core.management.utils import "
        "get_random_secret_key; print(get_random_secret_key())\""
    )

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "widget_tweaks",
    # Proje uygulamaları
    "cari",
    "banka",
    "sozlesme",
    "tahsilat",
    "fatura",
    "ceksenet",
    "gider",
    "stok",
    "kasa",
    "rapor",
    "dashboard",
    "takvim",
    "kullanici",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    # Login zorunlu — AuthenticationMiddleware'den SONRA gelmeli
    "muhasebe_buro.middleware.LoginZorunluMiddleware",
    # Rol bazlı yetki kontrolü
    "muhasebe_buro.permissions.YetkiMiddleware",
    # Aktivite kaydı (POST istekleri)
    "muhasebe_buro.permissions.AktiviteMiddleware",
]

ROOT_URLCONF = "muhasebe_buro.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "muhasebe_buro.context_processors.uygulama_bilgileri",
            ],
        },
    },
]

WSGI_APPLICATION = "muhasebe_buro.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Dosya yükleme limiti: 20 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

# ── Kimlik Doğrulama ────────────────────────────────────────────────────────
LOGIN_URL = "/hesap/giris/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/hesap/giris/"

# ── E-posta (varsayılan: konsol; üretim için SMTP ayarlayın) ─────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = "Muhasebe Bürosu <noreply@localhost>"
# Hatırlatma e-postasının gönderileceği alıcılar (virgillü liste: "a@b.com,c@d.com")
HATIRLATMA_ALICI = config("HATIRLATMA_ALICI", default="", cast=Csv())

# ── Firma Bilgileri (E-Fatura XML için) ──────────────────────────────────────
FIRMA_ADI = config("FIRMA_ADI", default="Firma Adı")
FIRMA_VKN = config("FIRMA_VKN", default="0000000000")
FIRMA_VERGI_DAIRESI = config("FIRMA_VERGI_DAIRESI", default="")
FIRMA_ADRES = config("FIRMA_ADRES", default="")

# ── Sürüm Kontrolü (GitHub Releases) ──────────────────────────────────
# True (varsayılan): açılışta GitHub'dan yeni sürüm kontrolü yap (24 saat cache)
# False: kapat (internet bağlantısı yoksa veya kurumsal ortamlarda)
SURUM_KONTROL = config("SURUM_KONTROL", default=True, cast=bool)

# ── Mikro Sync API Token ─────────────────────────────────────────────────────
# mikro_sync projesindeki FirmaAyar.mb_api_token ile eşleşmeli
_MIKRO_TOKEN_PLACEHOLDER = "mikro-sync-token-degistir-uretimde"
MIKRO_SYNC_API_TOKEN = config("MIKRO_SYNC_API_TOKEN", default=_MIKRO_TOKEN_PLACEHOLDER)
if not DEBUG and MIKRO_SYNC_API_TOKEN == _MIKRO_TOKEN_PLACEHOLDER:
    raise RuntimeError(
        "MIKRO_SYNC_API_TOKEN güvensiz varsayılan değer taşıyor. "
        ".env dosyasına gerçek bir token tanımlayın."
    )

# ── Üretim Güvenlik Ayarları ─────────────────────────────────────────────────
# DEBUG=False ortamında otomatik aktif olur.
# HTTPS kullanmıyorsanız (yalnızca yerel LAN) SECURE_SSL_REDIRECT=False bırakın.
if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HTTPS doğrulandıktan sonra 31536000 (1 yıl) olarak ayarlayın
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# ── Loglama ─────────────────────────────────────────────────────────────────
_LOG_DIR = BASE_DIR / "logs"
_LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "konsol": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "dosya_hata": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(_LOG_DIR / "hata.log"),
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "verbose",
            "level": "ERROR",
        },
        "dosya_tum": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(_LOG_DIR / "uygulama.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 3,
            "encoding": "utf-8",
            "formatter": "verbose",
            "level": "INFO",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["konsol", "dosya_hata", "dosya_tum"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["konsol", "dosya_hata"],
            "level": "WARNING",
            "propagate": False,
        },
        # Uygulama logları için: logging.getLogger('muhasebe')
        "muhasebe": {
            "handlers": ["konsol", "dosya_hata", "dosya_tum"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Geliştirici araçları — yalnızca DEBUG modda aktif
# ---------------------------------------------------------------------------
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]
