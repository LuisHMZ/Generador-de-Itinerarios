# config/settings/production.py

from .base import * # Importa toda la configuración base
import dj_database_url
import os

# --- Configuración de Producción ---
# 1. SEGURIDAD
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# 2. BASE DE DATOS (Supabase Postgres)
# Lee la variable DATABASE_URL que pondrás en Render
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Configuración de Archivos Multimedia (Media) con Supabase Storage ---
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# --- Configuración de S3 (para django-storages) ---
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
AWS_S3_FILE_OVERWRITE = False  # No sobrescribir archivos con el mismo nombre
# Configuraciones para que funcione bien
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_DEFAULT_ACL = 'public-read' # Para que las fotos sean visibles
AWS_QUERYSTRING_AUTH = False    # Para que las URLs sean limpias (sin firmas temporales)

# --- Configuración de MEDIA_URL ---
MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/object/public/{AWS_STORAGE_BUCKET_NAME}/'