from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Load environment variables


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'qreentry_project.urls'

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

# ✅ Supabase Database config
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {"NAME": 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {"NAME": 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {"NAME": 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS =  [
    BASE_DIR / "static",
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'


# Email configuration - read from .env
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "QREntry Support <noreply@qreentry.local>")
# Email configuration (reads from .env)
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

EMAIL_FAIL_SILENTLY = os.getenv("EMAIL_FAIL_SILENTLY", "False").lower() in (
    "1",
    "true",
    "yes",
)

# Read SMTP settings from environment; fallback to None/console defaults for dev
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
_EMAIL_PORT = os.getenv("EMAIL_PORT", "")
EMAIL_PORT = int(_EMAIL_PORT) if _EMAIL_PORT else None
EMAIL_USE_TLS = (
    os.getenv("EMAIL_USE_TLS", "").lower() in ("1", "true", "yes")
    if os.getenv("EMAIL_USE_TLS", "") != ""
    else False
)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "QREntry Support <noreply@qreentry.local>"
)

