# apps/itineraries/api.py
# ViewSets y vistas API para Itinerarios y Lugares Turísticos.

from rest_framework import viewsets, permissions
from .models import Itinerary, TouristicPlace, Category
from .serializers import ItinerarySerializer, TouristicPlaceSerializer, CategorySerializer


class ItineraryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, crear, ver, actualizar y borrar Itinerarios.
    """
    queryset = Itinerary.objects.all() # Define qué objetos maneja
    serializer_class = ItinerarySerializer # Le dice qué "traductor" usar
    
    # Define quién puede hacer qué (ajusta según tus necesidades)
    # IsAuthenticatedOrReadOnly: Cualquiera puede VER (GET), pero solo usuarios logueados pueden CREAR/EDITAR/BORRAR
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] 

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario autenticado como el creador del itinerario.
        """
        serializer.save(user=self.request.user)


# ViewSet para los lugares turísticos.
class TouristicPlaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para ver lugares turísticos.
    Permite listar (GET /api/places/) y ver detalles (GET /api/places/{id}/).
    """
    queryset = TouristicPlace.objects.all().prefetch_related('categories') # Optimiza la consulta de categorías
    serializer_class = TouristicPlaceSerializer
    # Cualquiera puede ver los lugares turísticos
    permission_classes = [permissions.AllowAny] 

# ViewSet para Categorías si quieres un endpoint para listarlas
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para listar categorías."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
