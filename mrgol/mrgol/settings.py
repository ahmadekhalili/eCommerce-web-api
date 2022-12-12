"""
Django settings for mrgol project.

Generated by 'django-admin startproject' using Django 3.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-l(24ils3ph2mp0%cguxdq!i%8cfjfldw*1ugu+a@9wk^2x^-e'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


#Application definition

INSTALLED_APPS = [
    'debug_toolbar',
    'django_extensions',
    'main.apps.MainConfig',
    'users.apps.UsersConfig',
    'cart.apps.CartConfig',
    'orders.apps.OrdersConfig',
    'payment.apps.PaymentConfig',
    'phonenumber_field',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'ckeditor',
    'ckeditor_uploader',
    #'rest_framework.authtoken',
]


MIDDLEWARE = [
    'main.middleware.custom_debug.Custom_DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mrgol.urls'

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
                'main.mycontexts.project_verbose',
            ],
        },
    },
]

WSGI_APPLICATION = 'mrgol.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'akh_db',
        'USER': 'akh_db',                          
        'PASSWORD': '134313731374aA',
        'HOST': '172.17.0.3',
        'PORT': '5432',
    },
    'mongo': {
        'ENGINE': 'djongo',
        'NAME': 'shop',
        'CLIENT': {
            'host': '172.17.0.2',
            'port': 27017,
            'username': 'akh2',
            'password': '134313731374aA',
            'authSource': 'shop',
            'authMechanism': 'SCRAM-SHA-256'
        },
    }
}

DATABASE_ROUTERS = ['main.db_router.MongoRouter']

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'customed_files.rest_framework.rest_framework_customed_classes.custom_rest_authentication.CustomSessionAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema'
    }

#'DEFAULT_SCHEMA_CLASS ': 'rest_framework.schemas.openapi.AutoSchema'
#rest_framework.authentication.SessionAuthentication

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/




TIME_ZONE = 'Iran'       #for enabling this, you should disable USE_TZ

USE_I18N = True

USE_L10N = True

USE_TZ = False


LANGUAGE_CODE = 'fa'

PHONENUMBER_DEFAULT_REGION = 'IR'
PHONENUMBER_DB_FORMAT = 'NATIONAL'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

LOCALE_PATHS = (BASE_DIR / 'locale', )

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CKEDITOR_UPLOAD_PATH = "uploads/"
#CART_PRODUCTS_ID = 'cart_cookie'
#FAVORITE_PRODUCTS_ID = 'favorites_cookie'

AUTH_USER_MODEL = 'users.User'

CORS_ALLOW_ALL_ORIGINS = True
#CORS_ALLOWED_ORIGINS = ['http://192.168.114.102:3000', 'http://127.0.0.1:3000', 'http://localhost:3000']

CORS_ALLOW_HEADERS = []       # add custom headers here
#CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
#CORS_ALLOW_CREDENTIALS = True
#SESSION_COOKIE_SAMESITE = 'None'
#SESSION_COOKIE_SECURE = True

CART_SESSION_ID = 'cart'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

#DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880            # 5 mg size for uploading posts like product.detailed_description = HTMLField(..)     (defult is 2.5) so we can write more posts with more images and ...

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
