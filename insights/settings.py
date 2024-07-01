"""
Django settings for insights project.

Generated by 'django-admin startproject' using Django 5.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

import environ
import sentry_sdk
from django.utils.log import DEFAULT_LOGGING
from sentry_sdk.integrations.django import DjangoIntegration

environ.Env.read_env(env_file=(environ.Path(__file__) - 2)(".env"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

AUTH_USER_MODEL = "users.User"

ADMIN_ENABLED = env.bool("ADMIN_ENABLED", default=True)

INSIGHTS_DOMAIN = env.str("INSIGHTS_DOMAIN")

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps
    "insights.event_driven",
    "insights.shared",
    "insights.dashboards",
    "insights.projects",
    "insights.sources",
    "insights.users",
    "insights.widgets",
    # 3rd party apps
    "django_filters",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
]

if ADMIN_ENABLED is True:
    INSTALLED_APPS.append("django.contrib.admin")

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

ROOT_URLCONF = "insights.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "insights.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": env.db(var="DEFAULT_DATABASE", default="sqlite:///insights_db.sqlite3"),
    "chats": env.db(var="CHATS_PG_DATABASE", default="sqlite:///chats_db.sqlite3"),
    "flows": env.str(var="FLOWS_PG_DATABASE", default="sqlite:///flows_db.sqlite3"),
}
FLOWS_ES_DATABASE = env.str(var="FLOWS_ES_DATABASE", default="https://localhost:9000")


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

DEFAULT_LANGUAGE = "en-us"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination." + "LimitOffsetPagination",
    "PAGE_SIZE": env.int("REST_PAGINATION_SIZE", default=20),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Insights Engine",
    "DESCRIPTION": "Insights REST API",
    "VERSION": "0.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # OTHER SETTINGS
}

# Logging

LOGGING = DEFAULT_LOGGING
LOGGING["formatters"]["verbose"] = {
    "format": "%(levelname)s  %(asctime)s  %(module)s "
    "%(process)d  %(thread)d  %(message)s"
}
LOGGING["handlers"]["console"] = {
    "level": "DEBUG",
    "class": "logging.StreamHandler",
    "formatter": "verbose",
}

# mozilla-django-oidc

OIDC_ENABLED = env.bool("OIDC_ENABLED", default=False)
if OIDC_ENABLED:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"].append(
        "mozilla_django_oidc.contrib.drf.OIDCAuthentication"
    )
    INSTALLED_APPS = (*INSTALLED_APPS, "mozilla_django_oidc")
    LOGGING["loggers"]["mozilla_django_oidc"] = {
        "level": "DEBUG",
        "handlers": ["console"],
        "propagate": False,
    }
    LOGGING["loggers"]["weni_django_oidc"] = {
        "level": "DEBUG",
        "handlers": ["console"],
        "propagate": False,
    }

    OIDC_RP_CLIENT_ID = env.str("OIDC_RP_CLIENT_ID")
    OIDC_RP_CLIENT_SECRET = env.str("OIDC_RP_CLIENT_SECRET")
    OIDC_OP_AUTHORIZATION_ENDPOINT = env.str("OIDC_OP_AUTHORIZATION_ENDPOINT")
    OIDC_OP_TOKEN_ENDPOINT = env.str("OIDC_OP_TOKEN_ENDPOINT")
    OIDC_OP_USER_ENDPOINT = env.str("OIDC_OP_USER_ENDPOINT")
    OIDC_OP_USERS_DATA_ENDPOINT = env.str("OIDC_OP_USERS_DATA_ENDPOINT")
    OIDC_OP_JWKS_ENDPOINT = env.str("OIDC_OP_JWKS_ENDPOINT")
    OIDC_RP_SIGN_ALGO = env.str("OIDC_RP_SIGN_ALGO", default="RS256")
    OIDC_DRF_AUTH_BACKEND = env.str(
        "OIDC_DRF_AUTH_BACKEND",
        default="insights.authentication.authentication.WeniOIDCAuthenticationBackend",
    )

    OIDC_RP_SCOPES = env.str("OIDC_RP_SCOPES", default="openid email")

    # TODO: Set admin permission to Chats client and remove the follow variables
    OIDC_ADMIN_CLIENT_ID = env.str("OIDC_ADMIN_CLIENT_ID")
    OIDC_ADMIN_CLIENT_SECRET = env.str("OIDC_ADMIN_CLIENT_SECRET")

OIDC_CACHE_TOKEN = env.bool(
    "OIDC_CACHE_TOKEN", default=False
)  # Enable/disable user token caching (default: False).
OIDC_CACHE_TTL = env.int(
    "OIDC_CACHE_TTL", default=600
)  # Time-to-live for cached user tokens (default: 600 seconds).

# CORS CONFIG
CORS_ORIGIN_ALLOW_ALL = True

# Sentry configuration

USE_SENTRY = env.bool("USE_SENTRY", default=False)

if USE_SENTRY:
    sentry_sdk.init(
        dsn=env.str("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        environment=env.str("ENVIRONMENT", default="develop"),
    )

USE_EDA = env.bool("USE_EDA", default=False)

if USE_EDA:
    EDA_CONNECTION_BACKEND = "insights.event_driven.backends.PyAMQPConnectionBackend"
    EDA_CONSUMERS_HANDLE = "insights.event_driven.handle.handle_consumers"

    EDA_BROKER_HOST = env("EDA_BROKER_HOST", default="localhost")
    EDA_VIRTUAL_HOST = env("EDA_VIRTUAL_HOST", default="/")
    EDA_BROKER_PORT = env.int("EDA_BROKER_PORT", default=5672)
    EDA_BROKER_USER = env("EDA_BROKER_USER", default="guest")
    EDA_BROKER_PASSWORD = env("EDA_BROKER_PASSWORD", default="guest")
    EDA_WAIT_TIME_RETRY = env.int("EDA_WAIT_TIME_RETRY", default=5)

    FLOWS_TICKETER_EXCHANGE = env("FLOWS_TICKETER_EXCHANGE", default="sectors.topic")
    FLOWS_QUEUE_EXCHANGE = env("FLOWS_QUEUE_EXCHANGE", default="queues.topic")

CHATS_URL = env("CHATS_URL")

PROJECT_ALLOW_LIST = env("PROJECT_ALLOW_LIST", default=[])
