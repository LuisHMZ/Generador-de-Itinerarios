from django.shortcuts import render

from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from .forms import TouristicPlaceForm
from .models import TouristicPlace
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


# Vista para la página de inicio
def home_view(request):
    """
    Renderiza la página de inicio.
    """
    # No se necesita lógica especial, solo mostrar el HTML.
    # El objeto 'request.user' está disponible automáticamente en la plantilla.
    return render(request, 'itineraries/provisional_home.html')


# --- GESTIÓN DE LUGARES (ADMIN) ---

def es_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(es_admin)
def admin_places_list(request):
    # Obtenemos todos los lugares ordenados por nombre
    places_list = TouristicPlace.objects.all().order_by('name')

    # Filtro de búsqueda (Nombre o Dirección)
    query = request.GET.get('q')
    if query:
        places_list = places_list.filter(
            Q(name__icontains=query) | 
            Q(address__icontains=query)
        )

    # Paginación (10 lugares por página)
    paginator = Paginator(places_list, 10)
    page_number = request.GET.get('page')
    places = paginator.get_page(page_number)

    return render(request, 'itineraries/admin-locaciones.html', {
        'places': places,
        'search_query': query
    })

@login_required
@user_passes_test(es_admin)
def admin_place_create(request):
    if request.method == 'POST':
        form = TouristicPlaceForm(request.POST)
        if form.is_valid():
            lugar = form.save()
            messages.success(request, f'Lugar "{lugar.name}" creado exitosamente.')
            return redirect('admin_places_list')
    else:
        form = TouristicPlaceForm()
    
    return render(request, 'itineraries/admin-locaciones-form.html', {
        'form': form, 
        'titulo': 'Nuevo Lugar Turístico'
    })

@login_required
@user_passes_test(es_admin)
def admin_place_edit(request, place_id):
    place = get_object_or_404(TouristicPlace, id=place_id)
    
    if request.method == 'POST':
        form = TouristicPlaceForm(request.POST, instance=place)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lugar "{place.name}" actualizado correctamente.')
            return redirect('admin_places_list')
    else:
        form = TouristicPlaceForm(instance=place)
    
    return render(request, 'itineraries/admin-locaciones-form.html', {
        'form': form, 
        'titulo': f'Editar {place.name}'
    })

@login_required
@user_passes_test(es_admin)
@require_POST
def admin_place_delete(request, place_id):
    place = get_object_or_404(TouristicPlace, id=place_id)
    nombre = place.name
    place.delete()
    messages.success(request, f'El lugar "{nombre}" ha sido eliminado.')
    return redirect('admin_places_list')