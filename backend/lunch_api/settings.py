import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

LOCAL_SECRET_KEY = "django-insecure-local-development-only"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", LOCAL_SECRET_KEY)
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
if not DEBUG and SECRET_KEY == LOCAL_SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")
    if host.strip()
]
for vercel_host_variable in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    raw_host = os.getenv(vercel_host_variable, "").strip()
    if raw_host:
        parsed_host = urlparse(raw_host if "://" in raw_host else f"https://{raw_host}").hostname
        if parsed_host and parsed_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(parsed_host)

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "accounts",
    "recommendations",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "lunch_api.urls"
TEMPLATES: list[dict[str, object]] = []
WSGI_APPLICATION = "lunch_api.wsgi.application"
ASGI_APPLICATION = "lunch_api.asgi.application"

if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ["DATABASE_URL"],
            conn_max_age=0,
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
elif os.getenv("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.getenv("POSTGRES_USER", "lunch"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    if os.getenv("VERCEL") == "1":
        raise RuntimeError("DATABASE_URL must be set on Vercel; SQLite is not persistent there.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000",
    ).split(",")
    if origin.strip()
]
PROJECT_VERCEL_CORS_ORIGIN = (
    r"^https://(?:lunch-web(?:-[a-z0-9]+)?|"
    r"lunch-[a-z0-9]+-heedo-kim0624s-projects)\.vercel\.app$"
)
CORS_ALLOWED_ORIGIN_REGEXES = [
    PROJECT_VERCEL_CORS_ORIGIN,
    *[
        regex.strip()
        for regex in os.getenv("CORS_ALLOWED_ORIGIN_REGEXES", "").split(",")
        if regex.strip()
    ],
]
CORS_ALLOW_HEADERS = (*default_headers, "x-multi-token")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_THROTTLE_RATES": {
        "food_search": "240/min",
        "multi_room_create": "20/hour",
        "multi_room_join": "120/hour",
        "multi_room_read": "600/min",
        "multi_room_write": "120/min",
        "multi_room_draw": "60/min",
    },
}

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
