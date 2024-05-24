"""
Django settings for ictsun project.

Generated by 'django-admin startproject' using Django 3.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialise environment variables
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


#Application definition

INSTALLED_APPS = [
    'debug_toolbar',
    'django_extensions',
    'drf_spectacular',
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
    'django.contrib.sitemaps',
    'django.contrib.sites',
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

ROOT_URLCONF = 'ictsun.urls'

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
                'main.contexts.project_verbose',
            ],
        },
    },
]

WSGI_APPLICATION = 'ictsun.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DBNAME'),
        'USER': env('POSTGRES_USERNAME'),
        'PASSWORD': env('POSTGRES_USERPASS'),
        'HOST': env('POSTGRES_MY_HOST'),
        'PORT': '5432',
    },
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
        'customed_files.rest_framework.classes.authentication.SessionAuthenticationCustom',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'  # 'rest_framework.schemas.coreapi.AutoSchema'
    }

#'DEFAULT_SCHEMA_CLASS ': 'rest_framework.schemas.openapi.AutoSchema'
#rest_framework.authentication.SessionAuthentication

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}


TIME_ZONE = 'Iran'       #for enabling this, you should disable USE_TZ

USE_I18N = True

USE_L10N = True

USE_TZ = False


LANGUAGE_CODE = 'fa'
gettext = lambda s: s
LANGUAGES = (
    ('fa', gettext('Farsi')),
    ('en', gettext('English')),
)                                             # main/management/createstates use 'fa' as default. it is important put default language in first (use in methods.conf_questwidget_class).

PHONENUMBER_DEFAULT_REGION = 'IR'
PHONENUMBER_DB_FORMAT = 'NATIONAL'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
# STATIC_ROOT = BASE_DIR / "static"      # for run command "python manage.py collectstatic" required

SPECTACULAR_SETTINGS = {
    'TITLE': 'My Project API',
    'DESCRIPTION': 'My project description',
    'VERSION': '0.9',
    'SERVE_INCLUDE_SCHEMA': False,
}

LOCALE_PATHS = (BASE_DIR / 'locale', )

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

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

#CSRF_TRUSTED_ORIGINS = ['http://192.168.114.100:3000', 'http://192.168.114.152:8000']

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

#DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880            # 5 mg size for uploading posts like product.detailed_description = HTMLField(..)     (default is 2.5) so we can write more posts with more images and ...

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# specify one of 'sites' to use. with django.contrib.sites we can create several 'sites' in admin panel like:
# '127.0.0.1:8000' and 'ictsun.ir', this uses in Site.objects.get_current(), in request.build_absolute_uri,
# and reverse()
SITE_ID = 1

# custom added vars (vars that aren't used by eny application or library and is only for personal usage)
CART_SESSION_ID = 'cart'
IMAGES_PATH_TYPE = 'jalali'  # 'jalali' or 'gregorian',  in gregorian images saves like: products_images/2023/06/03
POST_STEP = 6       # 6 means you will see 6 post in every PostList page, used in PostList view and main/sitemap.py
PRODUCT_STEP = 12
DEFAULT_SCHEME = 'http'   # uses in sitmape.py because we dont have access to request and request.scheme
SECRET_HS = 'mysecret'    # used in HS256 in users send sms
MONGO_PRODUCT_COL = 'product'  # used to create/get mongo collection, so change it only in first. for post static 'post'
