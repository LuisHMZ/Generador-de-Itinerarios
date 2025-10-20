# apps/users/apps.py

from django.apps import AppConfig
# 1. Importa post_save aquí
from django.db.models.signals import post_save

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        # 2. Importa el modelo User y tus funciones de signals DENTRO de ready
        from django.contrib.auth.models import User
        from .signals import create_user_profile, save_user_profile

        # 3. Conecta las señales explícitamente
        post_save.connect(create_user_profile, sender=User, dispatch_uid="create_user_profile_unique_id")
        post_save.connect(save_user_profile, sender=User, dispatch_uid="save_user_profile_unique_id")