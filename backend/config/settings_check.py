"""
Test settings for SONAR-X.
Uses SQLite so tests run without a PostgreSQL server.
All other settings inherit from the main settings.
"""
from config.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_sonarx.sqlite3',
    }
}

# Allow Django test client host
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '*']

# Faster password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable real media storage in tests
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
