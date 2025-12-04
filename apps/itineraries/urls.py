# apps/users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- RUTAS DE ADMINISTRACIÓN DE LUGARES ---
    path('panel/locaciones/', views.admin_places_list, name='admin_places_list'),
    path('panel/locaciones/crear/', views.admin_place_create, name='admin_place_create'),
    path('panel/locaciones/editar/<int:place_id>/', views.admin_place_edit, name='admin_place_edit'),
    path('panel/locaciones/eliminar/<int:place_id>/', views.admin_place_delete, name='admin_place_delete'),
]