# apps/itineraries/urls.py

from django.urls import path
from . import views

# Rutas web (HTML) — se incluyen en el proyecto en la raíz para que
# /itineraries/create/ muestre la página HTML.
urlpatterns = [
    path('itineraries/create/', views.create_itinerary_view, name='create_itinerary'),
    path('itineraries/<int:itinerary_id>/add-stops/', views.add_stops_view, name='add_stops'),
    path('itineraries/<int:itinerary_id>/edit/', views.edit_itinerary_view, name='edit_itinerary'),
]