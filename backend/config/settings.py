"""Django settings for the HireGraph AI local development foundation."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]  # .../backend
ROOT_DIR = BASE_DIR.parent                   # repository root
load_dotenv(ROOT_DIR / ".env")

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-local-only-change-before-deployment",
)
DEBUG = os.getenv("DJANGO_DEBUG", "True").strip().lower() in {"1", "true", "yes", "on"}

if not DEBUG and SECRET_KEY == "django-insecure-local-only-change-before-deployment":
    raise RuntimeError("Set a secure DJANGO_SECRET_KEY when DJANGO_DEBUG is False.")


def csv_setting(name: str, default: str = "") -> list[str]:
    """Read a comma-separated environment setting into a clean list."""
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


ALLOWED_HOSTS = csv_setting("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CORS_ALLOWED_ORIGINS = csv_setting(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
)
CSRF_TRUSTED_ORIGINS = csv_setting(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
)
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    # Project apps — accounts must precede organizations (FK dependency).
    "accounts",
    "organizations",
    "core",
    # Third-party DRF ecosystem.
    "django_filters",
    # Feature apps.
    "jobs",
    "approvals",
    "workflows",
    "candidates",
    "applications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Custom user model — must be set before the first migration.
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Database — PostgreSQL via psycopg3
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "hireflow"),
        "USER": os.getenv("POSTGRES_USER", "hireflow"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "local-db-password-change-me"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 5,
        },
    }
}

# ---------------------------------------------------------------------------
# Cache — Redis (provisioned in docker-compose.yml)
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": (
            f"redis://:{os.getenv('REDIS_PASSWORD', 'local-redis-password-change-me')}"
            f"@{os.getenv('REDIS_HOST', '127.0.0.1')}"
            f":{os.getenv('REDIS_PORT', '6379')}/1"
        ),
    }
}

# ---------------------------------------------------------------------------
# Session — stored in DB, delivered via HttpOnly cookie
# ---------------------------------------------------------------------------

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG  # True in production (HTTPS), False locally

# ---------------------------------------------------------------------------
# CSRF — cookie readable by JS (non-HttpOnly) so the frontend can set the header
# ---------------------------------------------------------------------------

CSRF_COOKIE_HTTPONLY = False   # Must be False so JS can read csrftoken cookie
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Return 403 (not 401) for unauthenticated requests because we use session auth.
    "UNAUTHENTICATED_USER": None,
    # Global filter backends (can be overridden per-view).
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Localisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Media and Private File Storage
# ---------------------------------------------------------------------------

PRIVATE_MEDIA_ROOT = Path(os.getenv("PRIVATE_MEDIA_ROOT", BASE_DIR / "media_private"))
MAX_RESUME_SIZE_BYTES = int(os.getenv("MAX_RESUME_SIZE_MB", "10")) * 1024 * 1024  # 10 MB default

# ---------------------------------------------------------------------------
# Celery Configuration
# ---------------------------------------------------------------------------

CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    f"redis://:{os.getenv('REDIS_PASSWORD', 'local-redis-password-change-me')}"
    f"@{os.getenv('REDIS_HOST', '127.0.0.1')}"
    f":{os.getenv('REDIS_PORT', '6379')}/2",
)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    f"redis://:{os.getenv('REDIS_PASSWORD', 'local-redis-password-change-me')}"
    f"@{os.getenv('REDIS_HOST', '127.0.0.1')}"
    f":{os.getenv('REDIS_PORT', '6379')}/3",
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").strip().lower() in {"1", "true", "yes", "on"}

# ---------------------------------------------------------------------------
# LLM & AI Orchestration Settings
# ---------------------------------------------------------------------------

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "fake")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

