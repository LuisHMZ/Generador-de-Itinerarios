from django.contrib.auth.models import User
from django.db.models.signals import post_save
from .models import Profile # Importa Profile desde models.py AQUI

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def save_user_profile(sender, instance, **kwargs):
    # Usamos get_or_create para más seguridad
    profile, created = Profile.objects.get_or_create(user=instance)
    if not created:
         # Solo intenta guardar si ya existía, evita doble guardado al crear
         profile.save()