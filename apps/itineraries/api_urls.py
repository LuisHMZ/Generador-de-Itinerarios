# apps/itineraries/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para los endpoints REST
router = DefaultRouter()
#router.register(r'itineraries', views.ItineraryViewSet, basename='itinerary')
#router.register(r'places', views.TouristicPlaceViewSet, basename='touristicplace')
#router.register(r'categories', views.CategoryViewSet, basename='category')

urlpatterns = [
    # Endpoints API específicos
    path('places/search/', views.search_places_api_view, name='api-place-search'),
    path('itineraries/<int:itinerary_id>/stops/', views.itinerary_stops_api_view, name='itinerary_stops'),
    path('geocode/autocomplete/', views.geocode_autocomplete_api_view, name='geocode_autocomplete'),

    # Rutas registradas por el router (p.ej. api/itineraries/)
    path('', include(router.urls)),
]