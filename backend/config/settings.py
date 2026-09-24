"""
SONAR-X Django Settings
Physics-Aware Explainable Marine Debris Intelligence System
"""

import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR.parent / '.env')
except ImportError:
    pass

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'sonarx-dev-secret-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    # SONAR-X apps
    'accounts',
    'surveys',
    'sonar',
    'detections',
    'fingerprint',
    'fusion',
    'hazard',
    'temporal',
    'exports',
    'evaluation',
    'reports',
    'common',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database — designed for PostGIS upgrade path
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sonarx_db'),
        'USER': os.environ.get('DB_USER', 'sonarx'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'sonarx_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', str(BASE_DIR / 'media')))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('JWT_SECRET', SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://localhost:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# SONAR-X specific settings
SONARX_VERSION = os.environ.get('SONARX_VERSION', '0.1.0-prototype')
AI_MODEL_PATH = os.environ.get('AI_MODEL_PATH', str(BASE_DIR.parent / 'ai' / 'models' / 'sonarx_yolo.pt'))
DEMO_MODE = os.environ.get('DEMO_MODE', 'true').lower() == 'true'
YOLO_CONFIDENCE_THRESHOLD = float(os.environ.get('YOLO_CONFIDENCE_THRESHOLD', '0.35'))
TEMPORAL_SEARCH_RADIUS = float(os.environ.get('TEMPORAL_SEARCH_RADIUS', '500'))
FINGERPRINT_SIMILARITY_THRESHOLD = float(os.environ.get('FINGERPRINT_SIMILARITY_THRESHOLD', '0.65'))
MAX_UPLOAD_SIZE_MB = int(os.environ.get('MAX_UPLOAD_SIZE_MB', '100'))

DEMO_DATA_DIR = BASE_DIR.parent / 'demo_data'
AI_DIR = BASE_DIR.parent / 'ai'
