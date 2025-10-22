from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Vista para la página de inicio
def home_view(request):
    """
    Renderiza la página de inicio.
    """
    # No se necesita lógica especial, solo mostrar el HTML.
    # El objeto 'request.user' está disponible automáticamente en la plantilla.
    return render(request, 'itineraries/provisional_home.html')