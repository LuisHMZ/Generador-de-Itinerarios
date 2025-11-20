# config/settings.py
import os
from dotenv import load_dotenv
import sys

from pathlib import Path

# Carga las variables del archivo .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

# Aplicaciones propias y de terceros
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aplicaciones personalizadas
    'apps.users.apps.UsersConfig',
    'apps.itineraries.apps.ItinerariesConfig',
    'apps.messaging.apps.MessagingConfig',
    'apps.posts.apps.PostsConfig',
    'apps.reports.apps.ReportsConfig',
    'apps.alertas.apps.AlertasConfig', # agregado por luis
    
    # Librerías de terceros
    # Allauth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Proveedores de Allauth
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    
    # Librería de storage
    'storages',
    
    # Django Rest Framework
    'rest_framework',
    
    'friendship', # agregado por luis
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware de allauth
    'allauth.account.middleware.AccountMiddleware',

    'apps.users.middleware.ActiveUserMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'





# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de Django Allauth

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1 # Necesario para django-allauth

# Configuración opcional de Allauth
# Descomentar en caso de usarse
#ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
#LOGIN_REDIRECT_URL = '/'

#ACCOUNT_SIGNUP_FIELDS = ("username", "email*")

ACCOUNT_SIGNUP_FORM_CLASS = 'apps.users.forms.SimpleSignupForm'  # Formulario de registro personalizado

# Comentamos estas líneas porque dejaremos que allauth use su
# redirección por defecto (que es /home/)
# ACCOUNT_LOGIN_REDIRECT_URL = '/feed/'
# LOGIN_REDIRECT_URL = '/feed/'