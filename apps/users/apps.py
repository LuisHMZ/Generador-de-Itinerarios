# apps/users/apps.py

from django.apps import AppConfig
# Solo necesitas importar post_save aquí
from django.db.models.signals import post_save

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users' # Asegúrate que coincida con tu ruta

    def ready(self):
        """
        Este método se llama cuando Django carga la aplicación.
        Conectamos las señales post_save para el perfil de usuario.
        """
        # --- Importaciones DENTRO de ready ---
        # Solo importamos lo necesario para las señales post_save
        try:
            from django.contrib.auth import get_user_model
            from .signals import create_user_profile, save_user_profile

            User = get_user_model() # Obtiene el modelo User activo

            # --- Conexiones existentes (se quedan igual) ---
            print("Conectando señales post_save para Profile...") # Mensaje actualizado
            post_save.connect(create_user_profile, sender=User, dispatch_uid="create_user_profile_unique_id")
            post_save.connect(save_user_profile, sender=User, dispatch_uid="save_user_profile_unique_id")
            print("Señales post_save de 'users' conectadas.") # Mensaje actualizado

        except ImportError:
            print("Advertencia: No se pudo importar User o signals.py en la app 'users' para conectar post_save.")
            pass # Ignora si algo falla al importar (ej. durante las primeras migraciones)

        # --- YA NO HAY CONEXIÓN PARA user_signed_up AQUÍ ---

