#apps/alertas/urls.py
from django.urls import path
from . import views

urlpatterns = [

    
    # 1. Tu ruta original para OBTENER la lista
    path('alertas/', views.api_alertas, name='api_alertas'),

    
    # 2. Tu ruta para MARCAR como leído
    path('alertas/mark-read/', views.mark_notifications_as_read, name='mark_notifications_as_read'),

    # 3. La ruta solo para el CONTADOR
    #CODIOG ANTERIOR: path('alertas/unread-count/', views.get_unread_notification_count, name='get_unread_notification_count'),
    # 3. La ruta para el CONTADOR JSON (opcional si solo usas HTMX, pero déjala por si acaso)
    #-- Nueva implementacion para A
    path('alertas/unread-count/', views.get_unread_notification_count, name='get_unread_notification_count'),
    
    #-----------------------Nuevo------------------------
    # 4. La ruta para el BADGE HTML (Esta es la que usará HTMX)
    path('alertas/badge/', views.badge_notification_html, name='badge_notification_html'),

]