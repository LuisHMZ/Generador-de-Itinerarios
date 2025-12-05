from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.itineraries.models import Category
import datetime

# --- Modelos de la App `users` ---

class Profile(models.Model):
    # La conexión uno-a-uno con el modelo User de Django.
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    birth_date = models.DateField(null=True, blank=True)
    last_seen = models.DateTimeField(default=timezone.now)
    # last_login ya existe en el modelo User de Django, no es necesario aquí.
    bio = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    last_password_update = models.DateTimeField(default=timezone.now)

    # Preferencias del usuario (ejemplo: categorías favoritas).
    preferred_categories = models.ManyToManyField(
        Category,
        blank=True, # Permite que un usuario no tenga preferencias
        related_name="user_profiles" # Nombre para acceder desde Category si es necesario
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'
    def esta_en_linea(self):
        # Consideramos "en línea" si se vio en los últimos 5 minutos
        now = timezone.now()
        return self.last_seen >= now - datetime.timedelta(minutes=5)

class UserConnection(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        ACCEPTED = 'accepted', 'Aceptada'
        REJECTED = 'rejected', 'Rechazada'
        BLOCKED = 'blocked', 'Bloqueado'

    from_user = models.ForeignKey(User, related_name='sent_connections', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_connections', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Asegura que no se pueda enviar más de una solicitud a la misma persona
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f'{self.from_user} -> {self.to_user}: {self.status}'

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField() # El script no tenía este campo pero es fundamental
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'Notificación para {self.user.username}'

class PasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=255) # Guarda el hash de la contraseña antigua
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Historial de contraseña para {self.user.username} del {self.created_at}'

# NOTA: El modelo SocialAccount será manejado por la librería django-allauth,
# por lo que no necesitas definirlo manualmente.

class LoginLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Exitoso'),
        ('failed', 'Fallido'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    username_attempt = models.CharField(max_length=150, blank=True) # Por si el usuario no existe (login fallido)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True) # Navegador/SO
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username_attempt} - {self.status} - {self.timestamp}"