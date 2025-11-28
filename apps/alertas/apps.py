# En: apps/alertas/apps.py
from django.apps import AppConfig

class AlertasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.alertas'
    # ¡La función ready() se ha ido!