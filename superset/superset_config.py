"""
Apache Superset Configuration for Suphasan Data Warehouse
==========================================================
This file is mounted into the Superset container at /app/pythonpath/superset_config.py
"""

import os

# ---------------------------------------------------------------------------
# Core Settings
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'change-me-in-production')
APP_NAME = 'Suphasan Analytics'

# ---------------------------------------------------------------------------
# Database (PostgreSQL for metadata)
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://"
    f"{os.environ.get('DATABASE_USER', 'suphasan')}:"
    f"{os.environ.get('DATABASE_PASSWORD', 'suphasan2569')}@"
    f"{os.environ.get('DATABASE_HOST', 'postgres')}:"
    f"{os.environ.get('DATABASE_PORT', '5432')}/"
    f"{os.environ.get('DATABASE_DB', 'superset_meta')}"
)

# ---------------------------------------------------------------------------
# Redis Cache
# ---------------------------------------------------------------------------
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))

CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_DB': 2,
}

DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 600,
    'CACHE_KEY_PREFIX': 'superset_data_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_DB': 3,
}

# ---------------------------------------------------------------------------
# Feature Flags
# ---------------------------------------------------------------------------
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'DASHBOARD_NATIVE_FILTERS_SET': True,
    'ALERT_REPORTS': True,
    'EMBEDDED_SUPERSET': True,
}

# ---------------------------------------------------------------------------
# Security & CORS
# ---------------------------------------------------------------------------
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'origins': ['http://localhost', 'http://localhost:80', 'http://localhost:8088'],
}

WTF_CSRF_ENABLED = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# SQL Lab Settings
# ---------------------------------------------------------------------------
SQLLAB_TIMEOUT = 300
SUPERSET_WEBSERVER_TIMEOUT = 300

# ---------------------------------------------------------------------------
# Localization (Thai)
# ---------------------------------------------------------------------------
BABEL_DEFAULT_LOCALE = 'en'
LANGUAGES = {
    'en': {'flag': 'us', 'name': 'English'},
    'th': {'flag': 'th', 'name': 'Thai'},
}

