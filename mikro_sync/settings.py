"""
Mikro Sync — Django Ayarları
Mikro ERP <-> Muhasebe Bürosu iki yönlü senkronizasyon servisi
Port: 8001
"""

from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = config("DEBUG", default=True, cast=bool)

SECRET_KEY = config("SECRET_KEY", default="django-insecure-mikrosync-degistir-uretimde!!")

if not DEBUG and SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError(
        "Üretim ortamında SECRET_KEY değiştirilmeli! "
        ".env dosyasına güçlü bir SECRET_KEY ekleyin."
    )

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")

# ---------------------------------------------------------------------------
# UYGULAMALAR
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Proje uygulamaları
    "widget_tweaks",
    "sync_motor",
    "hesap_yonetimi",
    "lisans",
    "posta",
    "kullanici",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "mikro_sync.middleware.LoginZorunluMiddleware",
    "lisans.middleware.LisansKontrolMiddleware",
    "mikro_sync.middleware.FirmaSecimZorunluMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mikro_sync.urls"

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
                "mikro_sync.context_processors.hy_aktif_firma",
                "mikro_sync.context_processors.lisans_bilgi",
            ],
        },
    },
]

WSGI_APPLICATION = "mikro_sync.wsgi.application"

# ---------------------------------------------------------------------------
# VERİTABANI
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# ŞIFRE DOĞRULAMA
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# ULUSLARARASILAŞTIRMA
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATİK DOSYALAR
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# GİRİŞ
# ---------------------------------------------------------------------------
LOGIN_URL = "/giris/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/giris/"

# ---------------------------------------------------------------------------
# LOGLAMA
# ---------------------------------------------------------------------------
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} [{name}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "dosya": {
            # Günlük rotasyon — 30 gün sakla, sadece INFO+ yazar (DEBUG dosyaya gitmez)
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOGS_DIR / "mikro_sync.log",
            "when": "midnight",
            "backupCount": 30,
            "formatter": "verbose",
            "encoding": "utf-8",
            "level": "INFO",
        },
    },
    "loggers": {
        "mikro_sync": {"handlers": ["console", "dosya"], "level": "DEBUG", "propagate": False},
    },
}

# ---------------------------------------------------------------------------
# ÜRETİM GÜVENLİK AYARLARI (DEBUG=False olduğunda devreye girer)
# ---------------------------------------------------------------------------
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_TRUSTED_ORIGINS = [
        x for x in config("CSRF_TRUSTED_ORIGINS", default="http://127.0.0.1:8001,http://localhost:8001").split(",") if x
    ]
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
