# config/settings/local.py
""" En este archivo se define la configuración específica para el entorno de desarrollo local. """

from .base import * # Importa toda la configuración base

# --- Configuración de Desarrollo ---
DEBUG = True

ALLOWED_HOSTS = []

# --- Base de Datos Local ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),   # El nombre que le diste en pgAdmin
        'USER': os.getenv('DB_USER'),             # El usuario por defecto de PostgreSQL
        'PASSWORD': os.getenv('DB_PASSWORD'), # La que pusiste al instalar PostgreSQL
        'HOST': os.getenv('DB_HOST'),              # O '127.0.0.1'
        'PORT': os.getenv('DB_PORT'),
    }
}

# --- Configuración de Archivos Multimedia (Media) ---
# Dónde se guardarán los archivos subidos por usuarios (fotos de perfil, etc.)
# Solo en desarrollo local
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')