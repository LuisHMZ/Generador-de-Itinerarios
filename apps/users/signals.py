from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile # Importa Profile desde models.py AQUI

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Usamos get_or_create para más seguridad
    profile, created = Profile.objects.get_or_create(user=instance)
    if not created:
         # Solo intenta guardar si ya existía, evita doble guardado al crear
         profile.save()