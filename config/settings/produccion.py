# config/settings/production.py

from .base import * # Importa toda la configuración base

# --- Configuración de Producción ---
DEBUG = False

ALLOWED_HOSTS = ['mextur-dominio.com'] # El dominio de despliegue

# --- Base de Datos de Supabase (leyendo desde el .env) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

# --- Configuración de Archivos Multimedia (Media) con Supabase Storage ---
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# --- Configuración de S3 (para django-storages) ---
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
AWS_S3_FILE_OVERWRITE = False  # No sobrescribir archivos con el mismo nombre
AWS_DEFAULT_ACL = 'public-read'  # Hace que los archivos sean públicos por defecto
AWS_S3_REGION_NAME = 'us-east-1' # Supabase usa una región por defecto
AWS_S3_SIGNATURE_VERSION = 's3v4'

# --- Configuración de MEDIA_URL ---
MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/object/public/{AWS_STORAGE_BUCKET_NAME}/'