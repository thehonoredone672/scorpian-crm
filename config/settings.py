"""
Django settings for Scorpion Academy ERP & CRM project.
Engineered for strict NoSQL (MongoDB Atlas) integration.
Optimized for zero-downtime deployment on Render.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Establish Absolute Paths & Load Environment Configurations
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 2. Cryptographic & Operational Security Variables
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("CRITICAL: SECRET_KEY is missing from environment variables!")

# Explicit string-to-boolean translation preventing logical fallbacks
DEBUG = os.getenv("DEBUG", "False").strip().lower() in ["true", "1", "yes"]

# Dynamic Host Resolution Matrix mapping
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "localhost:5500"]

# Automatically ingest your specific Render Web Service URL if available
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    ALLOWED_HOSTS.append(".render.com")

if DEBUG and not RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append("*")

# 3. Component Architecture Layer (Application Registrations)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'accounts',
    'branches',
    'sports',
    'students',
    'finance',
    'leads',  # Ensure leads module app structure is registered explicitly
]

# 4. Request-Response Pipeline Processing Rules (Middleware)
# WhiteNoise handles streaming production static files without needing Nginx/Apache config
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <--- Insert right under security middleware
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
        'DIRS': [],
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

# 5. Database Decoupling Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy',
    }
}

# 6. Password Storage Fallback Rules
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 7. Localization, Regionalization & Time Management
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'  # Synced for Indian Standard Time
USE_I18N = True
USE_TZ = True

# 8. Production Assets Allocation Control
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Turn on compressed caching for static elements to boost load times
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 9. Framework-Wide REST Integration Behavior Engine Rules
# Location: config/settings.py

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.MongoJWTAuthentication', # Your custom engine
    ],
    
    # ADD THIS EXPLICIT ROW TO PREVENT FALLBACK BLOCKS:
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny', # Let views handle internal role access logic
    ],
    
    'UNAUTHENTICATED_USER': None,
}

# 10. CORS Policy Mapping Setup
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ]