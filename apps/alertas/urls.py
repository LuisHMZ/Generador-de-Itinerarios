from django.urls import path
from . import views

urlpatterns = [
    # 1. Tu ruta original para OBTENER la lista
    path('alertas/', views.api_alertas, name='api_alertas'),
    
    # 2. Tu ruta para MARCAR como leído
    path('alertas/mark-read/', views.mark_notifications_as_read, name='mark_notifications_as_read'),

    # --- ▼▼▼ AÑADE ESTA LÍNEA ▼▼▼ ---
    # 3. La nueva ruta solo para el CONTADOR
    path('alertas/unread-count/', views.get_unread_notification_count, name='get_unread_notification_count'),
    # --- ▲▲▲ FIN DEL CÓDIGO AÑADIDO ▲▲▲ ---
]