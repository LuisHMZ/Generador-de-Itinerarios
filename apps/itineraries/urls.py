# apps/users/urls.py

from django.urls import path
from . import views 

#Definimos el namespace para llamar a las rutas como "itinerarios:nombre_ruta"
#app name = 'itineraries'
app_name = 'itineraries'
urlpatterns = [
    path('itineraries/', views.my_itineraries_view, name='my_itineraries'),
    path('itineraries/create/', views.create_edit_itinerary_view, name='create_itinerary'),
    path('itineraries/delete/<int:itinerary_id>/', views.delete_itinerary_view, name='delete_itinerary'),
    path('itineraries/<int:itinerary_id>/add-stops/', views.add_stops_view, name='add_stops'),
    path('itineraries/<int:itinerary_id>/preview/', views.itinerary_preview_view, name='preview_itinerary'),
    path('itineraries/<int:itinerary_id>/edit/', views.create_edit_itinerary_view, name='edit_itinerary'),
    path('itineraries/<int:itinerary_id>/view/', views.view_itinerary_view, name='view_itinerary'),

    path('rate/<int:itinerary_id>/', views.rate_itinerary, name='rate_itinerary'),
    path('', views.home_view, name='home'),

    # --- NUEVAS RUTAS PARA ACCIONES SOCIALES ---
    path('like/<int:itinerary_id>/', views.toggle_itinerary_like, name='toggle_like'),
    path('save/<int:itinerary_id>/', views.toggle_itinerary_save, name='toggle_save'),
    # -------------------------------------------

    # --- RUTAS DE ADMINISTRACIÓN DE LUGARES ---
    path('panel/locaciones/', views.admin_places_list, name='admin_places_list'),
    path('panel/locaciones/crear/', views.admin_place_create, name='admin_place_create'),
    path('panel/locaciones/editar/<int:place_id>/', views.admin_place_edit, name='admin_place_edit'),
    path('panel/locaciones/eliminar/<int:place_id>/', views.admin_place_delete, name='admin_place_delete'),
    # -------------------------------------------
]