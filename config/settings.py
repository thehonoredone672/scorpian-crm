"""
Django settings for Scorpion Academy ERP & CRM project.
Engineered for strict NoSQL (MongoDB Atlas) integration.
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

# Host resolution matrix mapping
if DEBUG:
    ALLOWED_HOSTS = ["*", "127.0.0.1", "localhost"]
else:
    # Production route access restrictions will be handled during cloud stage
    ALLOWED_HOSTS = []

# 3. Component Architecture Layer (Application Registrations)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders', # <--- ADD THIS HERE
    'accounts',
    'branches',
    'sports',
    'students',
    'finance',
]

# 4. Request-Response Pipeline Processing Rules (Middleware)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # <--- ADD THIS AT THE VERY TOP
    'django.middleware.security.SecurityMiddleware',
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
# We explicitly route this to a dummy backend to prevent Django from looking for local SQL files.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy',
    }
}

# 6. Password Storage Fallback Rules
# Note: For our core app users, we use our custom bcrypt layout in accounts/utils.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 7. Localization, Regionalization & Time Management
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'  # Synced for Indian Standard Time
USE_I18N = True
USE_TZ = True

# 8. Assets & Media Allocation Control
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 9. Framework-Wide REST Integration Behavior Engine Rules
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.MongoJWTAuthentication', # Enforce our custom NoSQL token validation engine
    ],
    'UNAUTHENTICATED_USER': None,  # Decouples anonymous SQL User references entirely
}

# CORS CONFIGURATION (Development Mode)
CORS_ALLOW_ALL_ORIGINS = True # Allows our local HTML files to talk to the API