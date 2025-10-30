from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# -------------------------
# Core settings
# -------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

# -------------------------
# Installed apps & middleware
# -------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'qreentry_project.urls'

# -------------------------
# Templates
# -------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'qreentry_project.wsgi.application'

# -------------------------
# Database (Supabase PostgreSQL)
# -------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# -------------------------
# Authentication
# -------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {"NAME": 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {"NAME": 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {"NAME": 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------
# Localization
# -------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -------------------------
# Static files
# -------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



# -------------------------
# Auth redirects
# -------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -------------------------
# Gmail Email Configuration
# -------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_FAIL_SILENTLY = os.getenv("EMAIL_FAIL_SILENTLY", "False").lower() in ("1", "true", "yes")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "0")) or 587
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("1", "true", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "QREntry Support <noreply@qreentry.local>")
