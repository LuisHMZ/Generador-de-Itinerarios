# En: apps/alertas/models.py
from django.db import models
from django.conf import settings

class Notification(models.Model):
    # El usuario que RECIBE la notificación
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    # El usuario que REALIZÓ la acción (opcional)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='+', 
        null=True, 
        blank=True
    )
    
    # El mensaje que se mostrará
    message = models.CharField(max_length=255)
    
    # El enlace al que debe dirigir al hacer clic
    link = models.URLField(max_length=200, blank=True)
    
    # Estado de la notificación
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',) # Las más nuevas primero

    def __str__(self):
        return f'Notificación para {self.recipient.username}'