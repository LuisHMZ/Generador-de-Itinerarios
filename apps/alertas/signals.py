# En: apps/alertas/signals.py

from django.dispatch import receiver
from django.urls import reverse
from friendship.signals import friendship_request_created, friendship_request_accepted 
from .models import Notification

@receiver(friendship_request_created)
def create_notification_on_friend_request(sender, from_user, to_user, **kwargs):
    
    # --- ▼▼▼ AÑADE ESTA LÍNEA ▼▼▼ ---
    print("¡¡¡ SEÑAL DE SOLICITUD RECIBIDA !!!")
    # --- ▲▲▲ FIN DE LA LÍNEA ▲▲▲ ---

    try:
        link = reverse('nombre_de_tu_vista_de_solicitudes') 
    except Exception:
        link = '#' 

    Notification.objects.create(
        recipient=to_user,
        actor=from_user,
        message=f'{from_user.username} te ha enviado una solicitud de amistad.',
        link=link
    )

@receiver(friendship_request_accepted)
def create_notification_on_friend_accept(sender, from_user, to_user, **kwargs):
    
    # --- ▼▼▼ AÑADE ESTA LÍNEA ▼▼▼ ---
    print("¡¡¡ SEÑAL DE SOLICITUD ACEPTADA !!!")
    # --- ▲▲▲ FIN DE LA LÍNEA ▲▲▲ ---
    
    try:
        link = reverse('profile', args=[from_user.username])
    except Exception:
        link = '#' 

    Notification.objects.create(
        recipient=to_user,
        actor=from_user,
        message=f'{from_user.username} aceptó tu solicitud de amistad.',
        link=link
    )