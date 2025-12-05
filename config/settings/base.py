# git
# config/settings.py
import os
from dotenv import load_dotenv
import sys
from django.contrib.messages import constants as messages
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
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

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
    'django_recaptcha',
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
    'apps.users.middleware.ActiveUserUpdateMiddleware',
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

# Configuración del Backend de Email (para desarrollo)
# Mostrará los emails en la consola en lugar de enviarlos realmente.
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Le dice a Django que use el servidor SMTP (Servidor de Correo Real)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Configuración del servidor de Gmail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True # Usa Seguridad de Capa de Transporte (TLS)  """

# Credenciales (leídas de forma segura desde tu archivo .env)
# (Asegúrate de tener 'import os' al inicio de tu settings.py)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Dirección "De:" por defecto para los correos enviados por tu app
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
        


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
ACCOUNT_EMAIL_CONFIRMATION_HMAC = False
SITE_ID = 1 # Necesario para django-allauth
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_ADAPTER = 'apps.users.adapters.CustomAccountAdapter'
# Configuración opcional de Allauth
# Descomentar en caso de usarse
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*', 'first_name', 'last_name', 'birth_date']
ACCOUNT_LOGIN_METHODS = {'username', 'email'} # Permite iniciar sesión con username O email
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
#Opción 1. Mandar a nuestro login
#ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/login/'
#LOGIN_URL = 'simple_login'
#LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'account_login'
# ---------------------------------

# URL a la que ir después de un login exitoso
LOGIN_REDIRECT_URL = '/' # A la home

# URL a la que ir después de un logout exitoso
# (Lo apuntamos a nuestra vista 'simple_login' personalizada)
ACCOUNT_LOGOUT_REDIRECT_URL = 'simple_login' 

# URL a la que ir después de confirmar el email
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = 'simple_login'
#ACCOUNT_SIGNUP_FIELDS = ("username", "email*")

ACCOUNT_SIGNUP_FORM_CLASS = 'apps.users.forms.SimpleSignupForm'  # Formulario de registro personalizado

# Configuración de Proveedores de Allauth (SOCIALACCOUNT)
# Esto le dice a allauth qué datos pedir a Google/Facebook

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # Para obtener datos como 'first_name', 'last_name'
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'facebook': {
        # Pedimos el email, perfil público y nombre
        'SCOPE': ['email', 'public_profile'],
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'verified',
        ],
        'METHOD': 'oauth2', # Usar OAuth2
        'VERIFIED_EMAIL': False, # Facebook no siempre garantiza email verificado
    }
}

# (Opcional, pero recomendado)
# Registrar automáticamente al usuario después de un login social exitoso
SOCIALACCOUNT_AUTO_SIGNUP = True
# Si el proveedor (ej. Google) ya verificó el email, confiamos en él
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'

# --- Configuración de reCAPTCHA ---
# (Asegúrate de que 'import os' esté al inicio de tu settings.py)

# Lee la Clave de Sitio (pública) desde el .env
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_SITE_KEY')

# Lee la Clave Secreta (privada) desde el .env
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_SECRET_KEY')

# Opcional: Cambia el tema a oscuro si prefieres
# RECAPTCHA_DEFAULT_THEME = 'dark'


# Comentamos estas líneas porque dejaremos que allauth use su
# redirección por defecto (que es /home/)
# ACCOUNT_LOGIN_REDIRECT_URL = '/feed/'
# LOGIN_REDIRECT_URL = '/feed/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
