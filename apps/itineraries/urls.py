# apps/itineraries/urls.py

from django.urls import path
from . import views

# Definimos el namespace para llamar a las rutas como 'itineraries:nombre_ruta'
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
]