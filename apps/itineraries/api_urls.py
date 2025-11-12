# apps/itineraries/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api as APIviews
from . import views

# Router para los endpoints REST
router = DefaultRouter()
router.register(r'itineraries', APIviews.ItineraryViewSet, basename='itinerary')
router.register(r'places', APIviews.TouristicPlaceViewSet, basename='touristicplace')
router.register(r'categories', APIviews.CategoryViewSet, basename='category')

urlpatterns = [
    # Endpoints API específicos
    path('places/search/', views.search_places_api_view, name='api-place-search'),
    path('places/nearby/', views.nearby_places_api_view, name='api-place-nearby'),
    path('itineraries/<int:itinerary_id>/stops/', views.itinerary_stops_api_view, name='itinerary_stops'),
    path('geocode/autocomplete/', views.geocode_autocomplete_api_view, name='geocode_autocomplete'),

    # Vista API para publicar un itinerario después de la previsualización
    path('itineraries/<int:itinerary_id>/publish/', views.publish_itinerary_api_view, name='publish_itinerary'),

    # Vista API para optimizar el orden de las paradas de un día usando el algoritmo del "Vecino más Cercano"
    path('itineraries/<int:itinerary_id>/stops/optimize/', views.optimize_stops_view, name='optimize_stops'),

    # Rutas registradas por el router (p.ej. api/itineraries/)
    path('', include(router.urls)),
]
