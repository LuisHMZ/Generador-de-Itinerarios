# apps/itineraries/views.py

import requests    # Para llamar a la API de Google Places
import os          # Para leer variables de entorno
import json       # Para formatear debug con json.dumps

from django.conf import settings # Para acceder a la configuración del proyecto
from django.shortcuts import render, get_object_or_404, redirect     # Para renderizar plantillas HTML y obtener objetos o 404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test  # Para requerir login en vistas basadas en funciones
from django.core.exceptions import PermissionDenied # Importante para manejo de permisos

# --- NUEVAS IMPORTACIONES (NECESARIAS PARA QUE FUNCIONE) ---
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile # Para manejar archivos de imagen
# -----------------------------------------------------------

from rest_framework.response import Response     # Para devolver respuestas API
from rest_framework.decorators import api_view, permission_classes  # Para definir vistas API y permisos
from rest_framework import viewsets, permissions, status     # Para ViewSets y permisos

# Importamos los modelos locales
from .models import Itinerary, ItineraryStop, TouristicPlace, Category, ItineraryComment, ItineraryReview
from .serializers import ItinerarySerializer, TouristicPlaceSerializer, CategorySerializer, ItineraryStopDetailSerializer

from apps.alertas.models import Notification
from friendship.models import Friend, FriendshipRequest

# --- Importaciones de la Lógica Social ---
from django.contrib.auth import get_user_model
from apps.posts.models import Post 

#Importaciones de la logica para el email verification 
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import TouristicPlaceForm
from itertools import groupby
from operator import attrgetter

# --- Definimos el Modelo de User UNA SOLA VEZ ---
User = get_user_model()

from .utils import haversine  # Importa la función de utilidad para calcular distancias

# Create your views here.
from django.shortcuts import render

# Tipos de Google Places v1 que SÍ queremos guardar
# Basado en las llaves de MAPEO_CATEGORIAS de add_stops.js
ALLOWED_GOOGLE_TYPES = {
    'museum', 'art_gallery', 'tourist_attraction', 'point_of_interest',
    'church', 'hindu_temple', 'mosque', 'synagogue', 
    'place_of_worship', 'historical_place', 'cultural_landmark', 'historical_landmark',
    'amusement_park', 'aquarium', 'zoo', 'stadium', 'movie_theater', 'night_club', 'bar', 'casino', 
    'park', 'natural_feature', 'campground', 'restaurant', 'cafe', 
    'bakery', 'shopping_mall'
}

# Sistema de categorías principales
CATEGORIAS_PRINCIPALES = [
    'Museos', 'Galerías de Arte', 'Puntos de Interés', 'Atracciones Turísticas', 
    'Sitios Históricos', 'Iglesias y Templos', 'Teatros', 'Parques de Diversiones',
    'Zoológicos', 'Acuarios', 'Estadios', 'Cines', 'Vida Nocturna', 'Parques y Plazas',
    'Maravillas Naturales', 'Zonas de Acampar', 'Restaurantes', 'Cafeterías', 
    'Bares y Cantinas', 'Panaderías'
]

# Mapeo de tipos de Google Places a categorías en español
# Basado en categorias.csv y alineado con ALLOWED_GOOGLE_TYPES
GOOGLE_TYPE_TO_CATEGORY = {
    'museum': 'Museos',
    'art_gallery': 'Galerías de Arte',
    'landmark': 'Puntos de Interés',
    'point_of_interest': 'Puntos de Interés',
    'tourist_attraction': 'Atracciones Turísticas',
    'historical_place': 'Sitios Históricos',
    'historical_landmark': 'Sitios Históricos',
    'cultural_landmark': 'Sitios Históricos',
    'church': 'Iglesias y Templos',
    'hindu_temple': 'Iglesias y Templos',
    'mosque': 'Iglesias y Templos',
    'synagogue': 'Iglesias y Templos',
    'place_of_worship': 'Iglesias y Templos',
    'performing_arts_theater': 'Teatros',
    'amusement_park': 'Parques de Diversiones',
    'zoo': 'Zoológicos',
    'aquarium': 'Acuarios',
    'stadium': 'Estadios',
    'movie_theater': 'Cines',
    'night_club': 'Vida Nocturna',
    'bar': 'Vida Nocturna',
    'casino': 'Vida Nocturna',
    'park': 'Parques y Plazas',
    'natural_feature': 'Maravillas Naturales',
    'campground': 'Zonas de Acampar',
    'restaurant': 'Restaurantes',
    'cafe': 'Cafeterías',
    'bakery': 'Panaderías',
    'shopping_mall': 'Atracciones Turísticas',  # Centros comerciales como atracción
}

# # --- VISTA DEL FEED SOCIAL (home_view) ---
# @login_required
# # Vista para la página principal (condicional)
# def home_view(request):
#     """
#     Esta vista maneja la página principal ('/home/')
#     y ahora sirve el NUEVO diseño del feed (feed/feed.html)
#     con datos REALES de la base de datos (Posts y Amigos).
#     """
#     # No se necesita lógica especial, solo mostrar el HTML.
#     # El objeto 'request.user' está disponible automáticamente en la plantilla.
#     return render(request, 'itineraries/provisional_home.html')


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
            return redirect('itineraries:admin_places_list')
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
    
    # 1. CAPTURAR: Obtenemos la url 'next' si viene en la URL o en el POST
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = TouristicPlaceForm(request.POST, request.FILES, instance=place)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lugar "{place.name}" actualizado correctamente.')
            
            # 2. REDIRIGIR: Si existe next_url, vamos ahí. Si no, a la lista.
            if next_url:
                return redirect(next_url)
            return redirect('itineraries:admin_places_list') # Asegúrate del namespace correcto
    else:
        form = TouristicPlaceForm(instance=place)
    
    return render(request, 'itineraries/admin-locaciones-form.html', {
        'form': form, 
        'titulo': f'Editar {place.name}',
        'next_url': next_url # 3. PASAR A PLANTILLA: Vital para el botón cancelar
    })

@login_required
@user_passes_test(es_admin)
@require_POST
def admin_place_delete(request, place_id):
    place = get_object_or_404(TouristicPlace, id=place_id)
    nombre = place.name
    place.delete()
    messages.success(request, f'El lugar "{nombre}" ha sido eliminado.')
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('itineraries:admin_places_list')

@login_required
@user_passes_test(es_admin)
@require_POST
def admin_place_toggle_visibility(request, place_id):
    place = get_object_or_404(TouristicPlace, id=place_id)
    place.is_active = not place.is_active # Invierte el estado
    place.save()
    estado = "visible" if place.is_active else "oculto"
    messages.success(request, f'El lugar "{place.name}" ahora está {estado}.')
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('itineraries:admin_places_list')

""" @login_required
@user_passes_test(es_admin)
def admin_place_detail(request, place_id):
    place = get_object_or_404(TouristicPlace, id=place_id)
    return render(request, 'itineraries/admin-locaciones-detalle.html', {
        'place': place
    }) """

# Asegúrate de tener: import os
@login_required
@user_passes_test(es_admin)
def admin_place_detail(request, place_id):
    place = get_object_or_404(TouristicPlace, id=place_id)
    return render(request, 'itineraries/admin-locaciones-detalle.html', {
        'place': place,
        'google_api_key': os.environ.get('GOOGLE_API_KEY', '') # <--- ESTO ES NUEVO
    })

@login_required
@user_passes_test(es_admin)
def admin_itinerary_preview(request, itinerary_id):
    """
    Vista exclusiva para administradores. 
    Muestra el itinerario limpio, sin distracciones, para moderación.
    """
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    # Reutilizamos la lógica de paradas si es necesaria
    all_stops = itinerary.itinerarystop_set.select_related('touristic_place').order_by('day_number', 'placement')
    
    # Agrupamos por día para la plantilla
    # groupby requiere que la lista ya esté ordenada por la clave de agrupación
    stops_by_day = []
    for day, stops in groupby(all_stops, key=attrgetter('day_number')):
        stops_by_day.append((day, list(stops)))
    source_report_id = request.GET.get('report_id')
    return render(request, 'itineraries/admin-view-itinerary.html', {
        'itinerary': itinerary,
        'stops_by_day': stops_by_day, # <--- Variable nueva
        'is_admin_preview': True,
        'google_api_key': os.environ.get('GOOGLE_API_KEY', ''),
        'source_report_id': source_report_id
    })

@login_required
@user_passes_test(es_admin)
def admin_toggle_itinerary_visibility(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Invertir el estado
    itinerary.is_active = not itinerary.is_active
    itinerary.save()
    
    estado = "visible" if itinerary.is_active else "oculto"
    messages.success(request, f"El itinerario ahora está {estado}.")
    
    # Redirigir a la misma página de revisión
    return redirect('itineraries:admin_itinerary_preview', itinerary_id=itinerary.id)
###################################################################################
#     if request.user.is_authenticated:
        
#         user = request.user
        
#         # --- 1. LÓGICA DE POSTS ---
#         try:
#             friend_ids_list = [f.id for f in Friend.objects.friends(user)]
#             posts = Post.objects.filter(
#                 author_id__in=friend_ids_list + [user.id]
#             ).order_by('-created_at')
#         except Exception as e:
#             print(f"Error obteniendo posts: {e}")
#             posts = []

#         # --- 2. LÓGICA DE AMIGOS (Sugerencias y Estado) ---
#         try:
#             friends_ids = [f.id for f in Friend.objects.friends(user)]
#             sent_requests = FriendshipRequest.objects.filter(from_user=user, rejected__isnull=True)
#             sent_ids = sent_requests.values_list('to_user_id', flat=True)
#             received_requests = FriendshipRequest.objects.filter(to_user=user, rejected__isnull=True)
#             received_ids = received_requests.values_list('from_user_id', flat=True)

#             all_other_users = User.objects.exclude(id=user.id)
            
#             users_with_status = []
#             for other_user in all_other_users:
#                 status = 'NONE'
#                 request_id = None
                
#                 if other_user.id in friends_ids:
#                     status = 'FRIENDS'
#                 elif other_user.id in sent_ids:
#                     status = 'PENDING_SENT'
#                     req = sent_requests.filter(to_user=other_user).first()
#                     if req: request_id = req.id
#                 elif other_user.id in received_ids:
#                     status = 'PENDING_RECEIVED'
#                     req = received_requests.filter(from_user=other_user).first()
#                     if req: request_id = req.id

#                 users_with_status.append({
#                     'user': other_user,
#                     'status': status,
#                     'request_id': request_id, 
#                 })
#         except Exception as e:
#             print(f"Error obteniendo sugerencias de amigos: {e}")
#             users_with_status = []

#         # --- 3. LÓGICA DE NOTIFICACIONES ---
#         try:
#             # Buscamos las notificaciones NO LEÍDAS para este usuario
#             notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')
#         except Exception as e:
#             print(f"Error obteniendo notificaciones: {e}")
#             notifications = []

#         # 4. Enviar los datos a la NUEVA plantilla
#         context = {
#             'posts': posts, 
#             'users_with_status': users_with_status,
#             'notifications': notifications
#         }
        
#         return render(request, 'feed/home_feed.html', context)
    
#     else:
#         return redirect('account_login')


# --- OTRAS VISTAS (API, ITINERARIOS, ETC.) ---

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_places_api_view(request):
    """
    Endpoint de API para buscar lugares turísticos (v1)
    """
    query = request.query_params.get('query', None)
    if not query:
        return Response({"error": "Parámetro 'query' es requerido."}, status=status.HTTP_400_BAD_REQUEST)

    # Obtener ubicación del usuario (si está disponible)
    user_lat = request.query_params.get('lat')
    user_lng = request.query_params.get('lng')
    search_radius_km = 25  # Radio de búsqueda de 25km

    local_results = []
    place_ids_found_locally = set()

    # --- 1. Buscar en la Base de Datos Local ---
    try:
        local_places_query = TouristicPlace.objects.filter(name__icontains=query, is_active=True)
        
        # Si el usuario proporcionó ubicación, filtrar por distancia
        if user_lat and user_lng:
            try:
                user_lat_float = float(user_lat)
                user_lng_float = float(user_lng)
                
                # Filtrar lugares cercanos usando haversine
                nearby_local_places = []
                for place in local_places_query:
                    if place.lat and place.long:
                        try:
                            distance = haversine(user_lat_float, user_lng_float, float(place.lat), float(place.long))
                            if distance <= search_radius_km:
                                nearby_local_places.append(place)
                        except (TypeError, ValueError):
                            continue
                
                local_places = nearby_local_places[:10]
            except ValueError:
                # Si las coordenadas no son válidas, usar búsqueda sin filtro de distancia
                local_places = local_places_query[:10]
        else:
            local_places = local_places_query[:10]
        
        local_results = TouristicPlaceSerializer(local_places, many=True).data
        place_ids_found_locally = {place['id'] for place in local_results}
    except Exception as e:
        print(f"!!! [ERROR] Buscando en BD local: {e}")

    google_results_processed = []
    if len(local_results) < 5:
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            print("!!! [ERROR] GOOGLE_API_KEY no encontrada.")
        else:
            # --- 2. Llamar a Google Text Search (v1) ---
            search_url = "https://places.googleapis.com/v1/places:searchText"
            search_body = {
                'textQuery': query,
                'languageCode': 'es',
                'maxResultCount': 10
            }
            
            # Agregar restricción de ubicación si el usuario proporcionó coordenadas
            if user_lat and user_lng:
                try:
                    user_lat_float = float(user_lat)
                    user_lng_float = float(user_lng)
                    search_body['locationBias'] = {
                        'circle': {
                            'center': {
                                'latitude': user_lat_float,
                                'longitude': user_lng_float
                            },
                            'radius': search_radius_km * 1000  # Convertir km a metros
                        }
                    }
                except ValueError:
                    print("!!! [WARNING] Coordenadas de usuario no válidas, buscando sin restricción geográfica")
            
            # Pedimos el 'id' (v1) y 'displayName'
            search_headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': api_key,
                'X-Goog-FieldMask': 'places.name,places.displayName'
            }
            
            try:
                search_response = requests.post(search_url, json=search_body, headers=search_headers, timeout=10)
                search_response.raise_for_status()
                search_data = search_response.json()

                for place_data_basic in search_data.get('places', []):

                    # Obtenemos el ID v1 (ej. 'places/ChIJ...')
                    google_v1_id = place_data_basic.get('name') # 'name' contiene el ID v1
                    if not google_v1_id:
                        continue

                    existing_place = TouristicPlace.objects.filter(external_api_id=google_v1_id).first()
                    place_obj = None

                    if existing_place:
                        if not existing_place.is_active:
                            continue
                        if existing_place.id not in place_ids_found_locally:
                            place_obj = existing_place
                    else:
                        # --- 3. Llamar a Place Details (v1) ---
                        details_url = f"https://places.googleapis.com/v1/{google_v1_id}"
                        
                        fields_mask = (
                            'id,'
                            'displayName,'
                            'formattedAddress,'
                            'location,'
                            'websiteUri,'
                            'internationalPhoneNumber,'
                            'regularOpeningHours,'
                            'rating,'
                            'editorialSummary,'
                            'photos,'
                            'types'
                        )
                        
                        details_headers = {
                            'X-Goog-Api-Key': api_key,
                            'X-Goog-FieldMask': fields_mask
                        }

                        details_params = {'languageCode': 'es'}

                        try:
                            details_response = requests.get(
                                details_url, 
                                params=details_params,
                                headers=details_headers,
                                timeout=10
                            )
                            details_response.raise_for_status()
                            place_detail = details_response.json()

                            # --- ¡FILTRO DE TIPOS MOVIDO AQUÍ! ---
                            # (Asegúrate de tener ALLOWED_GOOGLE_TYPES definido arriba en tu archivo)
                            place_types = place_detail.get('types', [])
                            if not place_types or not ALLOWED_GOOGLE_TYPES.intersection(set(place_types)):
                                print(f"--- [DEBUG] Omitiendo '{place_detail.get('displayName', {}).get('text')}' (Tipo no deseado: {place_types})")
                                continue # Salta al siguiente lugar en el 'for' loop
                            # --- FIN DEL FILTRO ---
                            
                            print(f"--- [DEBUG] Respuesta de Place Details: OK")

                            # Mapea los campos v1 a los nombres de tu modelo
                            defaults = {
                                'name': place_detail.get('displayName', {}).get('text', ''),
                                'address': place_detail.get('formattedAddress', ''),
                                'description': place_detail.get('editorialSummary', {}).get('text', ''),
                                'lat': place_detail.get('location', {}).get('latitude'),
                                'long': place_detail.get('location', {}).get('longitude'),
                                'website': place_detail.get('websiteUri', ''),
                                'phone_number': place_detail.get('internationalPhoneNumber', ''),
                                'opening_hours': str(place_detail.get('regularOpeningHours', {}).get('weekdayDescriptions', '[]')),
                                'external_api_rating': place_detail.get('rating'),
                            }
                            
                            place_obj, created = TouristicPlace.objects.update_or_create(
                                external_api_id=google_v1_id,
                                defaults=defaults
                            )
                            if not place_obj.is_active:
                                continue  # Saltamos si está oculto en nuestra BD
                            # ---------------------------

                            # --- ASIGNAR CATEGORÍAS ---
                            if created or not place_obj.categories.exists():
                                # Mapear los tipos de Google a categorías del sistema
                                categories_to_add = set()
                                for google_type in place_types:
                                    if google_type in GOOGLE_TYPE_TO_CATEGORY:
                                        category_name = GOOGLE_TYPE_TO_CATEGORY[google_type]
                                        categories_to_add.add(category_name)
                                
                                # Crear o recuperar las categorías y asignarlas
                                for category_name in categories_to_add:
                                    category_obj, _ = Category.objects.get_or_create(
                                        name=category_name,
                                        defaults={'description': f'Categoría: {category_name}'}
                                    )
                                    place_obj.categories.add(category_obj)
                                
                                if categories_to_add:
                                    print(f"--- [DEBUG] Categorías asignadas a '{place_obj.name}': {categories_to_add}")
                            
                            # --- LÓGICA DE FOTOS ---
                            if not place_obj.photo and 'photos' in place_detail and len(place_detail['photos']) > 0:
                                photo_resource_name = place_detail['photos'][0].get('name')
                                
                                if photo_resource_name:
                                    photo_url = (
                                        f"https://places.googleapis.com/v1/{photo_resource_name}/media"
                                        f"?key={api_key}&maxWidthPx=800"
                                    )
                                    
                                    try:
                                        photo_response = requests.get(photo_url, timeout=10)
                                        photo_response.raise_for_status()
                                        image_content = photo_response.content
                                        file_name = f"{google_v1_id.split('/')[-1]}.jpg" 
                                        place_obj.photo.save(file_name, ContentFile(image_content), save=True)
                                        
                                    except requests.exceptions.RequestException as e_photo:
                                        print(f"!!! [ERROR] FOTO: {e_photo}")

                        except requests.exceptions.RequestException as e_details:
                            print(f"!!! [ERROR] Google Place Details: {e_details}")
                        except Exception as e_proc_details:
                            print(f"!!! [ERROR] procesando detalles v1: {e_proc_details.response.text if e_proc_details.response else e_proc_details}")

                    if place_obj and place_obj.id not in place_ids_found_locally:
                        serialized_place = TouristicPlaceSerializer(place_obj).data
                        google_results_processed.append(serialized_place)
                        place_ids_found_locally.add(place_obj.id)

            except requests.exceptions.RequestException as e_search:
                print(f"!!! [ERROR] Google Text Search: {e_search}")
            except Exception as e_proc_search:
                print(f"!!! [ERROR] procesando búsqueda: {e_proc_search}")

    combined_results = local_results + google_results_processed
    return Response(combined_results)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def nearby_places_api_view(request):
    """
    Endpoint para obtener lugares cercanos (server-side).
    PRIMERO busca en BD local, luego complementa con Google Places API si es necesario.
    Parámetros GET esperados: lat (required), lng (required), radius_km (opcional, default 15)
    """
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    try:
        radius_km = float(request.query_params.get('radius_km', ''))
    except Exception:
        # Valor por defecto: si existe en settings usa RECOMMENDATION_RADIUS_KM, sino 25.0 km
        radius_km = float(getattr(settings, 'RECOMMENDATION_RADIUS_KM', 25.0))

    if not lat or not lng:
        return Response({'error': "Parámetros 'lat' y 'lng' son requeridos."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        lat_float = float(lat)
        lng_float = float(lng)
    except ValueError:
        return Response({'error': "Parámetros 'lat' y 'lng' deben ser números válidos."}, status=status.HTTP_400_BAD_REQUEST)

    # --- 1. BUSCAR PRIMERO EN LA BASE DE DATOS LOCAL ---
    local_results = []
    place_ids_found = set()
    
    try:
        # Obtener todos los lugares turísticos de la BD que tengan coordenadas
        all_places = TouristicPlace.objects.filter(
            lat__isnull=False, 
            long__isnull=False,
            is_active=True
        ).select_related()
        
        # Filtrar por distancia usando la función haversine
        nearby_places = []
        for place in all_places:
            try:
                distance = haversine(lat_float, lng_float, float(place.lat), float(place.long))
                if distance <= radius_km:
                    nearby_places.append(place)
                    place_ids_found.add(place.id)
            except (TypeError, ValueError):
                continue
        
        # Serializar los resultados locales (hasta 18 para paginación)
        if nearby_places:
            local_results = TouristicPlaceSerializer(nearby_places[:18], many=True).data
            # Debug: verificar cuántos tienen foto
            places_with_photo = sum(1 for p in nearby_places[:18] if p.photo)
            print(f"--- [DEBUG-Nearby] Encontrados {len(local_results)} lugares en BD local dentro de {radius_km} km")
            print(f"--- [DEBUG-Nearby] {places_with_photo} lugares tienen foto asignada")
            # Debug: mostrar URLs de foto
            for place_data in local_results:
                if place_data.get('photo_url'):
                    print(f"--- [DEBUG-Nearby] {place_data['name']}: photo_url = {place_data['photo_url']}")
                else:
                    print(f"--- [DEBUG-Nearby] {place_data['name']}: SIN FOTO (photo_url es None)")
        else:
            print(f"--- [DEBUG-Nearby] No se encontraron lugares en BD local dentro de {radius_km} km")
            
    except Exception as e:
        print(f"!!! [ERROR] Buscando en BD local (nearby): {e}")

    # --- 2. SI HAY MENOS DE 5 RESULTADOS, COMPLEMENTAR CON GOOGLE API ---
    if len(local_results) < 5:
        print(f"--- [DEBUG-Nearby] Solo {len(local_results)} resultados locales. Buscando en Google API...")
        
        api_key = os.environ.get('GOOGLE_API_KEY') or getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            print("!!! [WARNING] Google API key no configurada. Retornando solo resultados locales.")
            return Response(local_results)

        # Lista de tipos para recomendaciones
        DEFAULT_NEARBY_TYPES = [
            'art_gallery',
            'museum',
            'park',
            'restaurant',
            'cafe',
            'shopping_mall',
            'historical_place',
            'plaza',
        ]

        try:
            tipos_a_incluir = DEFAULT_NEARBY_TYPES 
            place_type = request.query_params.get('type')
            if place_type:
                if place_type in ALLOWED_GOOGLE_TYPES:
                     tipos_a_incluir = [place_type]
                else:
                    return Response({'error': f"Tipo '{place_type}' no soportado."}, status=status.HTTP_400_BAD_REQUEST)

            # Definir el Field Mask (pedimos todo lo necesario para guardar)
            fields_mask = (
                "places.id,"
                "places.name,"
                "places.displayName,"
                "places.types,"
                "places.rating,"
                "places.formattedAddress,"
                "places.location,"
                "places.websiteUri,"
                "places.internationalPhoneNumber,"
                "places.editorialSummary,"
                "places.photos"
            )

            # Construir el Body para searchNearby
            search_body = {
                "languageCode": "es",
                "includedTypes": tipos_a_incluir,
                "maxResultCount": 20,  # Aumentado para paginación (3 páginas de 6) 
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": lat_float,
                            "longitude": lng_float
                        },
                        "radius": int(radius_km * 1000)
                    }
                }
            }
            
            # Headers
            search_headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': api_key,
                'X-Goog-FieldMask': fields_mask
            }

            # Llamar a searchNearby
            search_url = 'https://places.googleapis.com/v1/places:searchNearby'
            resp = requests.post(search_url, json=search_body, headers=search_headers, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            results = data.get('places', [])
            
            print(f"--- [DEBUG-Nearby] Google API devolvió {len(results)} lugares")

            # Procesar y guardar lugares de Google API
            google_results = []
            for place_data in results:
                google_v1_id = place_data.get('name')
                if not google_v1_id:
                    continue

                # Mapear datos
                defaults = {
                    'name': place_data.get('displayName', {}).get('text', ''),
                    'address': place_data.get('formattedAddress', ''),
                    'description': place_data.get('editorialSummary', {}).get('text', ''),
                    'lat': place_data.get('location', {}).get('latitude'),
                    'long': place_data.get('location', {}).get('longitude'),
                    'website': place_data.get('websiteUri', ''),
                    'phone_number': place_data.get('internationalPhoneNumber', ''),
                    'external_api_rating': place_data.get('rating'),
                }
                
                # Guardar o Actualizar en BD
                place_obj, created = TouristicPlace.objects.update_or_create(
                    external_api_id=google_v1_id,
                    defaults=defaults
                )
                
                # --- ASIGNAR CATEGORÍAS ---
                if created or not place_obj.categories.exists():
                    # Obtener los tipos del lugar
                    place_types = place_data.get('types', [])
                    # Mapear los tipos de Google a categorías del sistema
                    categories_to_add = set()
                    for google_type in place_types:
                        if google_type in GOOGLE_TYPE_TO_CATEGORY:
                            category_name = GOOGLE_TYPE_TO_CATEGORY[google_type]
                            categories_to_add.add(category_name)
                    
                    # Crear o recuperar las categorías y asignarlas
                    for category_name in categories_to_add:
                        category_obj, _ = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'Categoría: {category_name}'}
                        )
                        place_obj.categories.add(category_obj)
                    
                    if categories_to_add:
                        print(f"--- [DEBUG-Nearby] Categorías asignadas a '{place_obj.name}': {categories_to_add}")
                
                # Solo agregar si no estaba en los resultados locales
                if place_obj.id not in place_ids_found:
                    # Descargar foto si no tiene
                    if not place_obj.photo and 'photos' in place_data and len(place_data['photos']) > 0:
                        photo_resource_name = place_data['photos'][0].get('name')
                        if photo_resource_name:
                            photo_url = f"https://places.googleapis.com/v1/{photo_resource_name}/media?key={api_key}&maxWidthPx=800"
                            try:
                                photo_response = requests.get(photo_url, timeout=10)
                                photo_response.raise_for_status()
                                file_name = f"{google_v1_id.split('/')[-1]}.jpg" 
                                place_obj.photo.save(file_name, ContentFile(photo_response.content), save=True)
                                print(f"--- [DEBUG-Nearby] Foto guardada: {place_obj.photo.url}")
                            except requests.exceptions.RequestException as e_photo:
                                print(f"!!! [ERROR-Nearby] No se pudo descargar foto: {e_photo}")
                    
                    google_results.append(place_obj)
                    place_ids_found.add(place_obj.id)
            
            # Serializar resultados de Google
            if google_results:
                google_serialized = TouristicPlaceSerializer(google_results, many=True).data
                print(f"--- [DEBUG-Nearby] Agregados {len(google_serialized)} lugares nuevos de Google API")
                local_results.extend(google_serialized)

        except requests.exceptions.RequestException as e:
            print(f"!!! [ERROR] Llamando a Google Places Nearby API: {e}")
            # Continuar con solo los resultados locales
        except Exception as e:
            print(f"!!! [ERROR] Procesando resultados de Google API: {e}")
            # Continuar con solo los resultados locales

    # --- 3. RETORNAR RESULTADOS COMBINADOS (BD Local + Google API) ---
    print(f"--- [DEBUG-Nearby] Retornando {len(local_results)} lugares en total")
    return Response(local_results)


# Vistas para la creación de itinerarios (HTML)

from django.shortcuts import render, get_object_or_404, reverse
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from .models import Itinerary

@login_required
def create_edit_itinerary_view(request, itinerary_id=None):
    
    # 1. LOGICA COMÚN: Intentar obtener el itinerario si hay ID
    itinerary = None
    if itinerary_id:
        # Nota: Aquí NO filtramos por status='draft' porque el dueño 
        # debe poder abrir su itinerario 'published' para editarlo (y que pase a draft)
        itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)

    # ====================================================
    # CASO GET: Servir el HTML (Lo que ya hacías)
    # ====================================================
    if request.method == 'GET':
        context = {
            'itinerary': itinerary,
            'categorias': CATEGORIAS_PRINCIPALES,
            'mode': 'Editar' if itinerary else 'Crear'
        }
        return render(request, 'itineraries/create_edit_itinerary.html', context)

    # ====================================================
    # CASO POST: Procesar los datos (Reemplaza al ViewSet)
    # ====================================================
    if request.method == 'POST':
        # Validar que sea AJAX (opcional, pero buena práctica con tu JS actual)
        # En Django moderno a veces request.is_ajax() está depreciado, 
        # se puede checar el header 'X-Requested-With' si es necesario.
        
        try:
            # A. RECOGER DATOS DEL FORM
            title = request.POST.get('title')
            description = request.POST.get('description')
            start_date = request.POST.get('start_date') or None
            end_date = request.POST.get('end_date') or None
            category = request.POST.get('category')
            banner_pic = request.FILES.get('banner_pic') # ¡Fácil manejo de archivos!

            # B. GUARDAR (Crear o Actualizar)
            if itinerary:
                # --- MODO EDICIÓN ---
                itinerary.title = title
                itinerary.description = description
                itinerary.start_date = start_date
                itinerary.end_date = end_date
                itinerary.category = category
                
                if banner_pic:
                    itinerary.banner_pic = banner_pic
                
                # ¡Aquí aplicamos tu regla de negocio fácilmente!
                itinerary.status = 'draft' 
                
                itinerary.save()
                
                # Redirección al paso 2
                next_url = reverse('itineraries:add_stops', args=[itinerary.id])
                
            else:
                # --- MODO CREACIÓN ---
                itinerary = Itinerary.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    category=category,
                    banner_pic=banner_pic,
                    status='draft'
                )
                next_url = reverse('itineraries:add_stops', args=[itinerary.id])

            return JsonResponse({'success': True, 'redirect_url': next_url})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # Método no permitido
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def add_stops_view(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)

    # Si el itinerario está publicado o si no es del usuario, lanzamos un Permission Denied
    if (itinerary.user != request.user) or (itinerary.status == 'published'):
        raise PermissionDenied("No tienes permiso para modificar este itinerario.")

    # --- Cálculo del numero de días que el usuario ha planeado ---
    total_dias = 1 # Valor por defecto
    if itinerary.start_date and itinerary.end_date and itinerary.start_date <= itinerary.end_date:
        total_dias = (itinerary.end_date - itinerary.start_date).days + 1

    google_api_key = os.environ.get('GOOGLE_API_KEY') or ""

    # Obtener la categoría del itinerario para filtrar recomendaciones
    itinerary_category = itinerary.category if itinerary.category else ""

    context = {
        'itinerary': itinerary,
        'total_dias': total_dias,
        'google_api_key': google_api_key,
        'itinerary_category': itinerary_category,
    }

    return render(request, 'itineraries/add_stops.html', context)


# @login_required
# def edit_itinerary_view(request, itinerary_id):
#     itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)
#     context = {
#         'itinerary': itinerary, 
#         'categorias': CATEGORIAS_PRINCIPALES,
#         'mode': 'Editar',        
#     }
#     return render(request, 'itineraries/create_edit_itinerary.html', context)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def geocode_autocomplete_api_view(request):
    query = request.query_params.get('query', None)
    if not query or len(query) < 3:
        return Response({"error": "Query parameter 'query' is required (min 3 chars)."}, status=status.HTTP_400_BAD_REQUEST)

    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return Response({"error": "Server configuration error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    external_api_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        'input': query,
        'key': api_key,
        'language': 'es',
        'types': '(cities)',
        'components': 'country:mx',
    }

    try:
        response = requests.get(external_api_url, params=params, timeout=5)
        response.raise_for_status() 
        data = response.json()

        if data.get('status') != 'OK':
            return Response({"error": "Could not fetch suggestions."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        predictions = data.get('predictions', [])
        desired_states = [
            'estado de méxico', 'estado de mexico', 'méxico', 'mexico',
            'ciudad de méxico', 'cdmx',
            'morelos', 'hidalgo', 'tlaxcala', 'puebla'
        ]

        def is_allowed_state(address_components):
            if not address_components:
                return False
            for comp in address_components:
                if 'administrative_area_level_1' in comp.get('types', []):
                    long = comp.get('long_name', '').lower()
                    short = comp.get('short_name', '').lower()
                    for s in desired_states:
                        if s in long or s in short:
                            return True
            return False

        suggestions = []
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        MAX_DETAILS_CALLS = 6
        details_calls = 0
        
        for p in predictions:
            if details_calls >= MAX_DETAILS_CALLS:
                break
            place_id = p.get('place_id')
            if not place_id: continue

            details_params = {
                'place_id': place_id,
                'fields': 'address_component,formatted_address',
                'key': api_key,
                'language': 'es'
            }
            try:
                dresp = requests.get(details_url, params=details_params, timeout=5)
                dresp.raise_for_status()
                ddata = dresp.json()
                if ddata.get('status') == 'OK':
                    addr_comps = ddata.get('result', {}).get('address_components', [])
                    if is_allowed_state(addr_comps):
                        suggestions.append({"description": p.get('description')})
                details_calls += 1
            except requests.exceptions.RequestException:
                details_calls += 1
                continue

        if suggestions:
            return Response(suggestions)

        fallback = [{"description": p.get('description')} for p in predictions][:10]
        return Response(fallback)

    except Exception as e:
        print(f"Error in geocode autocomplete: {e}")
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# Vista para los sitios turisticos de un itinerario en específico 
# api/itineraries/<int:itinerary_id>/places/
@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def itinerary_stops_api_view(request, itinerary_id):
    """
    Endpoint de API para obtener (GET) o Actualizar (PATCH)
    las paradas de un itinerario específico.
    """

    try:
        itinerary = Itinerary.objects.get(id=itinerary_id, user=request.user)
    except Itinerary.DoesNotExist:
        return Response({"error": "Itinerario no encontrado o no te pertenece."}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Lógica del método GET: Obtener las paradas del itinerario
        try:
            stops = ItineraryStop.objects.filter(itinerary=itinerary).order_by('day_number','placement')
            serialized_stops = ItineraryStopDetailSerializer(stops, many=True)
            return Response(serialized_stops.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error al obtener paradas: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'PATCH':
        # Lógica del método PATCH: Actualizar las paradas del itinerario
        # Se encarga de borrar y re-crear las paradas según los datos recibidos
        try:
            stops_data_by_day = request.data.get('stops', [])
            if not stops_data_by_day:
                return Response({"error": "Datos de paradas no proporcionados."}, status=status.HTTP_400_BAD_REQUEST)

            # Eliminar las paradas existentes del itinerario
            ItineraryStop.objects.filter(itinerary=itinerary).delete()

            # Re-crear las paradas según los datos recibidos
            new_stops = []
            """
            Formato de stops_data_by_day:
            [
            {"touristic_place": X, "day_number": 1, "placement": 1},
            ...
            {"touristic_place": X, "day_number": 2, "placement": 1},
            ...
            ]
            """
            for stops_list in stops_data_by_day:
                touristic_place_id = stops_list.get('touristic_place')
                try:
                    # Obtener el objeto TouristicPlace a partir del ID
                    place = TouristicPlace.objects.get(id=touristic_place_id)
                    new_stops.append(
                        ItineraryStop(
                            itinerary = itinerary,
                            touristic_place = place,
                            day_number = int(stops_list.get('day_number')),
                            placement = int(stops_list.get('placement')) + 1
                        )
                    )
                except TouristicPlace.DoesNotExist:
                    print(f"Advertencia: No se encontró TouristicPlace con id {touristic_place_id}. Omitiendo.")
            if new_stops:
                ItineraryStop.objects.bulk_create(new_stops)
                return Response({"message": "Itinerario actualizado con éxito."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": f"Error al guardar: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            

    

@login_required
def itinerary_preview_view(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)
    stops_qs = ItineraryStop.objects.filter(itinerary=itinerary).select_related('touristic_place')

    stops_by_day = []
    current_day = None
    current_list = []
    for stop in stops_qs:
        if current_day is None:
            current_day = stop.day_number
            current_list = [stop]
        elif stop.day_number == current_day:
            current_list.append(stop)
        else:
            stops_by_day.append((current_day, current_list))
            current_day = stop.day_number
            current_list = [stop]

    if current_day is not None:
        stops_by_day.append((current_day, current_list))

    google_api_key = os.environ.get('GOOGLE_API_KEY')

    context = {
        'itinerary': itinerary,
        'stops_by_day': stops_by_day,
        'GOOGLE_API_KEY': google_api_key,
    }

    return render(request, 'itineraries/preview_itinerary.html', context)


# --- ▼▼▼ NUEVAS VISTAS PARA ACCIONES SOCIALES (AGREGADO) ▼▼▼ ---

@login_required
@require_POST
def toggle_itinerary_like(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    if request.user in itinerary.likes.all():
        itinerary.likes.remove(request.user)
        liked = False
    else:
        itinerary.likes.add(request.user)
        liked = True
        
        # --- NOTIFICACIÓN DE LIKE ---
        if itinerary.user != request.user:
            Notification.objects.create(
                recipient=itinerary.user,
                actor=request.user,
                message=f"A {request.user.username} le gustó tu itinerario '{itinerary.title}'",
                link="#" 
            )
    
    return JsonResponse({
        'status': 'success', 
        'liked': liked, 
        'count': itinerary.likes.count()
    })

@login_required
@require_POST
def toggle_itinerary_save(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    if request.user in itinerary.saved_by.all():
        itinerary.saved_by.remove(request.user)
        saved = False
    else:
        itinerary.saved_by.add(request.user)
        saved = True
        
    return JsonResponse({
        'status': 'success', 
        'saved': saved
    })

# --- LÓGICA DE CALIFICACIÓN ---

@login_required
@require_POST
def rate_itinerary(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    try:
        rating_val = int(request.POST.get('rating'))
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Valor inválido'}, status=400)

    if rating_val < 1 or rating_val > 5:
        return JsonResponse({'status': 'error', 'message': 'La calificación debe ser entre 1 y 5'}, status=400)

    # update_or_create: Si ya calificó, actualiza las estrellas; si no, crea una nueva.
    review, created = ItineraryReview.objects.update_or_create(
        itinerary=itinerary,
        user=request.user,
        defaults={'rating': rating_val}
    )
    
    # Notificar al dueño solo si es la primera vez que califica
    if created and itinerary.user != request.user:
         Notification.objects.create(
            recipient=itinerary.user,
            actor=request.user,
            message=f"{request.user.username} calificó tu itinerario '{itinerary.title}' con {rating_val} estrellas",
            link=f"/itineraries/{itinerary.id}/view/"
        )

    return JsonResponse({
        'status': 'success', 
        'new_average': itinerary.get_average_rating() 
    })

# --- COMENTARIOS EN ITINERARIOS (ANIDADOS) ---

def serialize_comments_recursive(comments_qs):
    """ 
    Función auxiliar recursiva para estructurar comentarios y respuestas.
    """
    data = []
    for c in comments_qs:
        if hasattr(c.user, 'profile') and c.user.profile.profile_picture:
            avatar_url = c.user.profile.profile_picture.url
        else:
            avatar_url = '/static/img/default-avatar.png'
        
        # Buscamos las respuestas de ESTE comentario (children)
        replies_qs = c.replies.all().order_by('created_at')
        replies_data = serialize_comments_recursive(replies_qs)
        
        data.append({
            'id': c.id,
            'user': c.user.username,
            'avatar': avatar_url,
            'text': c.text,
            'created_at': c.created_at.strftime('%d %b %Y %H:%M'),
            'is_owner': True, # Simplificado para validación visual
            'replies': replies_data # <--- LISTA DE RESPUESTAS ANIDADAS
        })
    return data

@login_required
def load_itinerary_comments(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    # Solo cargamos los comentarios PRINCIPALES (los que no tienen padre)
    root_comments = itinerary.comments.filter(parent__isnull=True).select_related('user', 'user__profile').order_by('created_at')
    
    comments_data = serialize_comments_recursive(root_comments)
    return JsonResponse({'comments': comments_data})

@login_required
@require_POST
def add_itinerary_comment(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    text = request.POST.get('text')
    parent_id = request.POST.get('parent_id') # <--- Capturamos si es respuesta
    
    if text:
        parent_comment = None
        if parent_id:
            try:
                parent_comment = ItineraryComment.objects.get(id=parent_id)
            except ItineraryComment.DoesNotExist:
                pass

        # Creamos el comentario (con o sin padre)
        comment = ItineraryComment.objects.create(
            itinerary=itinerary, 
            user=request.user, 
            text=text,
            parent=parent_comment
        )
        
        # Notificación
        if itinerary.user != request.user:
            msg = f"{request.user.username} respondió a un comentario" if parent_comment else f"{request.user.username} comentó en tu itinerario"
            Notification.objects.create(
                recipient=itinerary.user,
                actor=request.user,
                message=msg,
                link="#"
            )

        if hasattr(request.user, 'profile') and request.user.profile.profile_picture:
            avatar_url = request.user.profile.profile_picture.url
        else:
            avatar_url = '/static/img/default-avatar.png'
        
        new_comment_data = {
            'id': comment.id,
            'user': request.user.username,
            'avatar': avatar_url,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%d %b %Y %H:%M'),
            'is_owner': True,
            'replies': [] # Un comentario nuevo nace sin respuestas
        }
        return JsonResponse({'status': 'success', 'new_comment': new_comment_data})
    
    return JsonResponse({'status': 'error', 'message': 'El comentario no puede estar vacío'}, status=400)# Vista API para optimizar el orden de las paradas de un día usando el algoritmo del "Vecino más Cercano"
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def optimize_stops_view(request, itinerary_id):
    """
    Endpoint de API para optimizar el orden de las paradas de un día
    usando el algoritmo del "Vecino más Cercano".
    Recibe: { "day_number": 1, "place_ids": [10, 45, 22, 5] }
    Devuelve: { "optimized_route": [ ... (lista serializada) ... ], "warnings": [...] }
    """
    
    # 1. Validar el itinerario y permisos
    try:
        itinerary = Itinerary.objects.get(id=itinerary_id, user=request.user, status='draft')
    except Itinerary.DoesNotExist:
        return Response({"error": "No se encontró el itinerario o no tienes permiso."}, status=status.HTTP_404_NOT_FOUND)

    # 2. Obtener datos del POST
    place_ids = request.data.get('place_ids', [])
    day_number = request.data.get('day_number')

    if not place_ids or len(place_ids) < 3:
        return Response({"error": "Se necesitan al menos 3 paradas para optimizar."}, status=status.HTTP_400_BAD_REQUEST)

    # 3. Obtener los objetos TouristicPlace de la BD
    # Usamos un dict para poder reordenar los objetos que ya tenemos
    places_lookup = {
        place.id: place for place in TouristicPlace.objects.filter(id__in=place_ids)
    }
    
    # Asegurarnos de que los IDs recibidos existen
    ordered_places = []
    for pid in place_ids:
        if pid in places_lookup:
            ordered_places.append(places_lookup[pid])
    
    if len(ordered_places) < 3:
        return Response({"error": "Paradas no válidas."}, status=status.HTTP_400_BAD_REQUEST)

    # 4. Implementar el Algoritmo "Vecino más Cercano"
    
    # (Regla de negocio: ej. 15km)
    MAX_RANGE_KM = 15.0 
    warnings = []
    
    optimized_route = []
    remaining_places = ordered_places.copy() # Copia de la lista

    # El punto de inicio es FIJO (el primero de la lista)
    current_place = remaining_places.pop(0)
    optimized_route.append(current_place)

    while remaining_places:
        nearest_neighbor = None
        min_distance = float('inf')

        # Encontrar el vecino más cercano
        for next_place in remaining_places:
            distance = haversine(
                current_place.lat, current_place.long,
                next_place.lat, next_place.long
            )
            if distance < min_distance:
                min_distance = distance
                nearest_neighbor = next_place
        
        # Validar la regla de negocio del "rango máximo"
        if min_distance > MAX_RANGE_KM:
            warnings.append(
                f"Advertencia: El tramo de '{current_place.name}' a '{nearest_neighbor.name}' "
                f"es de {min_distance:.1f} km, que supera el límite de {MAX_RANGE_KM} km."
            )

        # Moverse al vecino más cercano
        current_place = nearest_neighbor
        optimized_route.append(current_place)
        remaining_places.remove(nearest_neighbor)

    # 5. Devolver la ruta optimizada
    # Usamos el mismo serializer que usa tu frontend para que los datos coincidan
    serializer = TouristicPlaceSerializer(optimized_route, many=True)
    
    return Response({
        "optimized_route": serializer.data,
        "warnings": warnings
    })


# Vista API para guardar el itinerario después de la vista previa
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def publish_itinerary_api_view(request, itinerary_id):
    """
    Endpoint de API para publicar (guardar definitivamente) un itinerario.
    Cambia su estado de 'draft' a 'published'.
    """
    try:
        itinerary = Itinerary.objects.get(id=itinerary_id, user=request.user)
    except Itinerary.DoesNotExist:
        return Response({"error": "No se encontró el itinerario o no tienes permiso."}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Cambiar el estado a 'published'
        itinerary.status = 'published'
        itinerary.save()
    except Exception as e:
        return Response({"error": f"Error al publicar el itinerario: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"success": "Itinerario publicado correctamente."})

# Vista para ver los detalles de un itinerario ya publicado
@login_required
def view_itinerary_view(request, itinerary_id):
    """
    Muestra los detalles de un itinerario publicado.
    El usuario debe ser el propietario del itinerario.
    Contexto enviado a la plantilla:
      - itinerary: objeto Itinerary
      - stops_by_day: lista de tuplas (day_number, [stops ordenadas por placement])
    """
    # Obtén el itinerario sin filtrar por usuario: comprobar permisos abajo
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    stops_qs = ItineraryStop.objects.filter(itinerary=itinerary).select_related('touristic_place')

    # Permisos de visualización:
    # - El propietario siempre puede ver
    # - Si no es propietario: sólo puede ver itinerarios publicados
    #   y que sean 'public' o 'friends' (en este último caso, debe ser amigo)
    is_owner = (request.user == itinerary.user)
    if not is_owner:
        # Debe estar publicado
        if itinerary.status != 'published':
            raise Http404('Itinerario no disponible.')

        # Comprobar privacidad
        privacy = getattr(itinerary, 'privacy', 'public')
        if privacy == 'public':
            pass
        elif privacy == 'friends':
            try:
                friends_ids = [f.id for f in Friend.objects.friends(itinerary.user)]
            except Exception:
                friends_ids = []
            if request.user.id not in friends_ids:
                raise Http404('No tienes permiso para ver este itinerario.')
        else:
            # 'private' u otras opciones => no permitido
            raise Http404('No tienes permiso para ver este itinerario.')

    stops_by_day = []
    current_day = None
    current_list = []
    for stop in stops_qs:
        if current_day is None:
            current_day = stop.day_number
            current_list = [stop]
        elif stop.day_number == current_day:
            current_list.append(stop)
        else:
            stops_by_day.append((current_day, current_list))
            current_day = stop.day_number
            current_list = [stop]

    if current_day is not None:
        stops_by_day.append((current_day, current_list))

    google_api_key = os.environ.get('GOOGLE_API_KEY')

    context = {
        'itinerary': itinerary,
        'stops_by_day': stops_by_day,
        'GOOGLE_API_KEY': google_api_key,
        'is_owner': is_owner,
    }

    return render(request, 'itineraries/view_itinerary.html', context)

# Vista para listar los itinerarios del usuario autenticado
@login_required
def my_itineraries_view(request):
    """
    Muestra la lista de itinerarios del usuario autenticado.
    Contexto enviado a la plantilla:
      - itineraries: lista de Itinerary del usuario
    """
    # Ordenar por fecha de creación descendente
    itineraries = Itinerary.objects.filter(user=request.user).order_by('-created_at')

    # Envia tambien los amigos del usuario para posibles usos en la plantilla
    friends = Friend.objects.friends(request.user)
    friend_ids = [f.id for f in friends]
    relevant_users = friend_ids + [request.user.id]
    online_friends = friends 

    # Lógica de filtrado
    status_filter = request.GET.get('status')

    if status_filter == 'published':
        itineraries = itineraries.filter(status='published')
    elif status_filter == 'draft':
        itineraries = itineraries.filter(status='draft')
    # Si el filtro es 'all' o no está presente, mostramos todos

    # Sugerencias y Status
    candidates = User.objects.exclude(id__in=relevant_users).order_by('?')[:5]
    users_with_status = []
    
    sent_map = {uid: rid for uid, rid in FriendshipRequest.objects.filter(from_user=request.user).values_list('to_user_id', 'id')}
    received_map = {uid: rid for uid, rid in FriendshipRequest.objects.filter(to_user=request.user).values_list('from_user_id', 'id')}

    for candidate in candidates:
        status = 'NONE'
        req_id = None
        if candidate.id in sent_map:
            status = 'PENDING_SENT'
            req_id = sent_map[candidate.id]
        elif candidate.id in received_map:
            status = 'PENDING_RECEIVED'
            req_id = received_map[candidate.id]
            
        users_with_status.append({'user': candidate, 'status': status, 'request_id': req_id})

    context = {
        'itineraries': itineraries,
        'online_friends': online_friends,
        'users_with_status': users_with_status,
        'status_filter': status_filter or 'all', # Para mantener el estado del filtro en la plantilla
    }

    return render(request, 'feed/user_itineraries.html', context)


# Vista para eliminar un itinerario
@require_POST # Solo permite POST para mayor seguridad
@login_required
def delete_itinerary_view(request, itinerary_id):
    """
    Elimina un itinerario del usuario autenticado.
    Redirige a la vista de 'mis itinerarios' después de la eliminación.
    """
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)
    
    try:
        itinerary.delete()
        # Mensaje de éxito y recarga
        messages.success(request, "El itinerario ha sido eliminado correctamente.")
        return redirect('itineraries:my_itineraries')
    except Exception as e:
        messages.error(request, f'Error al eliminar el itinerario: {str(e)}')


@require_POST
@login_required
def update_privacy_view(request, itinerary_id):
    import json
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        new_privacy = data.get('privacy')
        
        if new_privacy in ['public', 'friends', 'private']:
            itinerary.privacy = new_privacy
            itinerary.save()
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Opción inválida'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


