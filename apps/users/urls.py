# apps/users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.simple_register_view, name='simple_register'),
    path('login/', views.simple_login_view, name='simple_login'),
    path('logout/', views.simple_logout_view, name='simple_logout'),
    
    # --- RUTA PARA ENVIAR SOLICITUD ---
    path('request/send/<int:to_user_id>/', views.send_friend_request, name='send_friend_request'),
    
    # --- RUTA PARA LISTAR SOLICITUDES RECIBIDAS ---
    path('solicitudes/', views.friend_requests_view, name='friend_requests'),

    # --- RUTAS PARA ACEPTAR/RECHAZAR ---
    path('request/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('request/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    
    # --- RUTA PARA ELIMINAR AMIGO ---
    path('remove/friend/<int:user_id>/', views.remove_friend, name='remove_friend'),
    
    # --- RUTA PARA CANCELAR SOLICITUD ENVIADA (NUEVA) ---
    path('request/cancel/<int:request_id>/', views.cancel_friend_request, name='cancel_friend_request'),

    # Esta es la URL de tu página de solicitudes
    path('solicitudes/', views.friend_requests_view, name='friend_requests_view'),

    path('perfil/<str:username>/', views.profile_view, name='profile_view'),

    # --- RUTA PARA CREAR PUBLICACIÓN ---
    path('crear/post/', views.create_post_page_view, name='create_post_page'),

    # --- RUTA PARA EL PANEL DEL ADMIN ---
    path('panel/comunicaciones/', views.admin_communications_panel, name='admin_communications'),

    # --- RUTA PARA LA BÚSQUEDA (API) ---
    path('api/search-users/', views.api_search_users, name='api_search_users'),

]