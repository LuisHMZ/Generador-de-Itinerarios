from django.urls import path
from . import views

# ESTO ES CLAVE: Define el "apellido" de las rutas
app_name = 'messaging'

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    
    # APIs
    path('api/list/', views.get_conversations, name='api_list'),
    path('api/messages/<int:conversation_id>/', views.get_messages, name='api_messages'),
    path('api/send/<int:conversation_id>/', views.send_message, name='api_send'),
]