# Create your views here.
import requests     # Para llamar a la API de Google Places
import os         # Para leer variables de entorno
import json       # Para formatear debug con json.dumps

from django.conf import settings # Para acceder a la configuración del proyecto
from django.shortcuts import render, get_object_or_404, redirect     # Para renderizar plantillas HTML y obtener objetos o 404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required  # Para requerir login en vistas basadas en funciones

from django.core.files.base import ContentFile # Para manejar archivos de imagen

from rest_framework.response import Response    # Para devolver respuestas API
from rest_framework.decorators import api_view, permission_classes  # Para definir vistas API y permisos
from rest_framework import viewsets, permissions, status    # Para ViewSets y permisos

from .models import Itinerary, ItineraryStop, TouristicPlace, Category # Importa tus modelos
from .serializers import ItinerarySerializer, TouristicPlaceSerializer, CategorySerializer, ItineraryStopDetailSerializer  # Importa tus serializers

from .utils import haversine  # Importa la función de utilidad para calcular distancias

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

# Vista para la página principal (condicional)
def home_view(request):
    if request.user.is_authenticated:
        # Lógica para mostrar el feed (ej. obtener posts)
        # return render(request, 'posts/feed.html', context)
        # Por ahora, una simple redirección o placeholder:
        return render(request, 'itineraries/provisional_home.html') # Crea esta plantilla simple
    else:
        # Muestra la página de bienvenida (que tiene los enlaces login/registro)
        return render(request, 'itineraries/provisional_home.html') # Tu plantilla de bienvenida

# Vista API para buscar lugares turísticos usando Google Places API
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])  # Solo usuarios autenticados pueden usar esta vista
def search_places_api_view(request):
    """
    Endpoint de API para buscar lugares turísticos (v1)
    Usando ID v1 ('places/...') como clave única.
    """
    query = request.query_params.get('query', None)
    print(f"\n--- [NUEVA BÚSQUEDA] Query recibido: '{query}' ---")
    if not query:
        return Response({"error": "Parámetro 'query' es requerido."}, status=status.HTTP_400_BAD_REQUEST)

    local_results = []
    place_ids_found_locally = set()

    # --- 1. Buscar en la Base de Datos Local ---
    try:
        local_places = TouristicPlace.objects.filter(name__icontains=query)[:10]
        local_results = TouristicPlaceSerializer(local_places, many=True).data
        place_ids_found_locally = {place['id'] for place in local_results}
        print(f"--- [DEBUG] Búsqueda local encontró: {len(local_results)} resultados.")
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
                'maxResultCount': 10,
                # --- FILTRO DE UBICACIÓN CORREGIDO (Rectángulo) ---
                'locationRestriction': {
                    'rectangle': {
                        # Esquina Suroeste (low)
                        'low': {
                            'latitude': 18.3,    # Sur de Morelos
                            'longitude': -100.4   # Oeste de Edomex
                        },
                        # Esquina Noreste (high)
                        'high': {
                            'latitude': 21.3,    # Norte de Hidalgo
                            'longitude': -96.7    # Este de Puebla
                        }
                    }
                }
            }
            
            # Pedimos el 'id' (v1) y 'displayName'
            search_headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': api_key,
                'X-Goog-FieldMask': 'places.name,places.displayName' # Pedimos el ID v1
            }
            
            print(f"--- [DEBUG] Llamando a Text Search v1...")
            
            try:
                search_response = requests.post(search_url, json=search_body, headers=search_headers, timeout=10)
                search_response.raise_for_status()
                search_data = search_response.json()

                print(f"--- [DEBUG] Respuesta de Text Search v1: Lugares: {len(search_data.get('places', []))}")

                for place_data_basic in search_data.get('places', []):

                    # Obtenemos el ID v1 (ej. 'places/ChIJ...')
                    google_v1_id = place_data_basic.get('name') # 'name' contiene el ID v1
                    if not google_v1_id:
                        print("--- [DEBUG] Lugar de Google sin 'name' v1, omitiendo.")
                        continue

                    # ¡CAMBIO CLAVE! Buscamos en la BD por el ID v1
                    existing_place = TouristicPlace.objects.filter(external_api_id=google_v1_id).first()
                    place_obj = None

                    if existing_place:
                        print(f"--- [DEBUG] El lugar '{existing_place.name}' ya existe en la BD local.")
                        if existing_place.id not in place_ids_found_locally:
                            place_obj = existing_place
                    else:
                        print(f"--- [DEBUG] Lugar nuevo. Llamando a Place Details v1 para: {google_v1_id}")
                        # --- 3. Llamar a Place Details (v1) ---
                        # La URL correcta es v1/{name}, donde {name} es 'places/ChIJ...'
                        details_url = f"https://places.googleapis.com/v1/{google_v1_id}"
                        
                        # Máscara de campos para Place Details v1
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
                        
                        # 1. Mueve la máscara de campos a las cabeceras
                        details_headers = {
                            'X-Goog-Api-Key': api_key,
                            'X-Goog-FieldMask': fields_mask  # Así es como la API v1 lee los campos
                        }

                        # 2. Deja 'params' solo con los parámetros que SÍ van en la URL
                        details_params = {'languageCode': 'es'}


                        try:
                            # 3. La llamada ahora es correcta
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
                            
                            # ¡CAMBIO CLAVE! Guardamos usando el ID v1 como clave única
                            # Usamos update_or_create para obtener el objeto (creado o actualizado)
                            place_obj, created = TouristicPlace.objects.update_or_create(
                                external_api_id=google_v1_id,
                                defaults=defaults
                            )
                            
                            # --- INICIO: LÓGICA DE FOTOS ---
                            # FOTO 1: Revisar si el lugar NO tiene foto y la API SÍ trajo
                            if not place_obj.photo and 'photos' in place_detail and len(place_detail['photos']) > 0:
                                # FOTO 2: Obtener el 'name' (resource name) de la primera foto
                                photo_resource_name = place_detail['photos'][0].get('name')
                                
                                if photo_resource_name:
                                    print(f"--- [DEBUG] Foto encontrada. Descargando desde: {photo_resource_name}")
                                    # FOTO 3: Construir la URL de descarga (¡es un endpoint diferente!)
                                    # Usamos 800px como un tamaño razonable
                                    photo_url = (
                                        f"https://places.googleapis.com/v1/{photo_resource_name}/media"
                                        f"?key={api_key}&maxWidthPx=800"
                                    )
                                    
                                    try:
                                        # FOTO 4: Descargar la imagen
                                        photo_response = requests.get(photo_url, timeout=10)
                                        photo_response.raise_for_status()
                                        
                                        # FOTO 5: Obtener los bytes de la imagen
                                        image_content = photo_response.content
                                        
                                        # FOTO 6: Guardar los bytes en el ImageField
                                        # El nombre de archivo debe ser único
                                        file_name = f"{google_v1_id.split('/')[-1]}.jpg" 
                                        place_obj.photo.save(file_name, ContentFile(image_content), save=True)
                                        print(f"--- [DEBUG] ¡ÉXITO! Foto guardada en {place_obj.photo.url}")
                                        
                                    except requests.exceptions.RequestException as e_photo:
                                        print(f"!!! [ERROR] FOTO: No se pudo descargar: {e_photo}")
                            # --- FIN: LÓGICA DE FOTOS ---

                            print(f"--- [DEBUG] ¡ÉXITO! Lugar guardado/creado: {place_obj.name}")

                        except requests.exceptions.RequestException as e_details:
                            print(f"!!! [ERROR] llamando a Google Place Details v1: {e_details.response.text if e_details.response else e_details}")
                        except Exception as e_proc_details:
                            print(f"!!! [ERROR] procesando detalles v1: {e_proc_details.response.text if e_proc_details.response else e_proc_details}")

                    if place_obj and place_obj.id not in place_ids_found_locally:
                        serialized_place = TouristicPlaceSerializer(place_obj).data
                        google_results_processed.append(serialized_place)
                        place_ids_found_locally.add(place_obj.id)

            except requests.exceptions.RequestException as e_search:
                 print(f"!!! [ERROR] llamando a Google Text Search v1: {e_search.response.text if e_search.response else e_search}")
            except Exception as e_proc_search:
                 print(f"!!! [ERROR] procesando búsqueda v1: {e_proc_search}")

    # --- 4. Combinar Resultados ---
    combined_results = local_results + google_results_processed
    print(f"--- [DEBUG] Resultados combinados finales (enviando al JS): {len(combined_results)} ítems")
    return Response(combined_results)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def nearby_places_api_view(request):
    """
    Endpoint para obtener lugares cercanos (server-side) usando Places Nearby Search (Web Service).
    Parámetros GET esperados: lat (required), lng (required), radius_km (opcional, default tomado de settings o 15)
    Retorna una lista de lugares con campos simplificados: place_id, name, types, rating, address/vicinity, geometry, photo_url (si existe).
    """
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    try:
        radius_km = float(request.query_params.get('radius_km', ''))
    except Exception:
        # Valor por defecto: si existe en settings usa RECOMMENDATION_RADIUS_KM, sino 15.0 km
        radius_km = float(getattr(settings, 'RECOMMENDATION_RADIUS_KM', 15.0))

    if not lat or not lng:
        return Response({'error': "Parámetros 'lat' y 'lng' son requeridos."}, status=status.HTTP_400_BAD_REQUEST)

    api_key = os.environ.get('GOOGLE_API_KEY') or getattr(settings, 'GOOGLE_API_KEY', None)
    if not api_key:
        return Response({'error': 'Google API key no configurada en el servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # (No rate-limiting: petición simple al servicio de Places)

    # Vamos a apegarnos a la documentación 100% y usar solo Tabla A
    # Esta es una lista mucho más curada para recomendaciones
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
        # (Asegúrate de tener DEFAULT_NEARBY_TYPES y ALLOWED_GOOGLE_TYPES definidos)
        tipos_a_incluir = DEFAULT_NEARBY_TYPES 
        place_type = request.query_params.get('type')
        if place_type:
            if place_type in ALLOWED_GOOGLE_TYPES:
                 tipos_a_incluir = [place_type]
            else:
                return Response({'error': f"Tipo '{place_type}' no soportado."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Definir el Field Mask (pedimos todo lo necesario para guardar)
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

        # 2. Construir el Body (¡con el 'circle' correcto!)
        search_body = {
            "languageCode": "es",
            "includedTypes": tipos_a_incluir,
            "maxResultCount": 10, 
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(lat),
                        "longitude": float(lng)
                    },
                    "radius": int(radius_km * 1000)
                }
            }
        }
        
        # 3. Headers
        search_headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': fields_mask
        }

        # 4. Llamar a searchNearby
        search_url = 'https://places.googleapis.com/v1/places:searchNearby'
        resp = requests.post(search_url, json=search_body, headers=search_headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        results = data.get('places', [])

        # --- INICIO DE LA NUEVA LÓGICA DE GUARDADO ---
        
        # Necesitamos estas importaciones (asegúrate de que estén al inicio de views.py)
        # from .models import TouristicPlace
        # from .serializers import TouristicPlaceSerializer
        # from django.core.files.base import ContentFile

        processed_objects = [] # Lista para guardar los OBJETOS de nuestra BD

        for place_data in results:
            # Usamos el 'name' (resource name v1) como ID externo único
            google_v1_id = place_data.get('name')
            if not google_v1_id:
                continue

            # 5. Mapear datos (igual que en search_places_api_view)
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
            
            # 6. Guardar o Actualizar en nuestra BD
            place_obj, created = TouristicPlace.objects.update_or_create(
                external_api_id=google_v1_id,
                defaults=defaults
            )
            
            # 7. Lógica de descarga de fotos (igual que en search_places_api_view)
            if not place_obj.photo and 'photos' in place_data and len(place_data['photos']) > 0:
                photo_resource_name = place_data['photos'][0].get('name')
                if photo_resource_name:
                    print(f"--- [DEBUG-Nearby] Foto encontrada. Descargando desde: {photo_resource_name}")
                    photo_url = f"https://places.googleapis.com/v1/{photo_resource_name}/media?key={api_key}&maxWidthPx=800"
                    try:
                        photo_response = requests.get(photo_url, timeout=10)
                        photo_response.raise_for_status()
                        file_name = f"{google_v1_id.split('/')[-1]}.jpg" 
                        place_obj.photo.save(file_name, ContentFile(photo_response.content), save=True)
                        print(f"--- [DEBUG-Nearby] ¡ÉXITO! Foto guardada en {place_obj.photo.url}")
                    except requests.exceptions.RequestException as e_photo:
                        print(f"!!! [ERROR-Nearby] FOTO: No se pudo descargar: {e_photo}")

            processed_objects.append(place_obj)
        
        # 8. Serializar los OBJETOS de nuestra BD
        # Esto nos da { "id": 58, "name": "...", "photo_url": "/media/...", ... }
        serializer = TouristicPlaceSerializer(processed_objects, many=True)
        return Response(serializer.data)
        
        # --- FIN DE LA NUEVA LÓGICA ---

    except requests.exceptions.RequestException as e:
        print(f"Error calling Places Nearby: {e}")
        return Response({'error': 'Error al llamar al servicio externo de Places.'}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        print(f"Unexpected error in nearby_places_api_view: {e}")
        return Response({'error': 'Error interno del servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Vistas para la creación de itinerarios (HTML)
"""
Estas vistas permiten a los usuarios crear y editar itinerarios a través de páginas web.
Incluye la vista para agregar paradas al itinerario con recomendaciones personalizadas.
"""

@login_required
def create_itinerary_view(request):
    """
    Vista para MOSTRAR el formulario de creación de itinerario (Paso 1).
    El guardado (POST) lo manejará la API a través de JavaScript.
    """
    # Solo maneja GET para mostrar el formulario vacío
    context = {
        'itinerary': None, # Pasa None para indicar que es creación
        'mode': 'Crear',    # Indica al template que estamos en modo creación
    }
    return render(request, 'itineraries/create_edit_itinerary.html', context)

@login_required # Solo usuarios logueados pueden continuar con la creacion del itinerario
def add_stops_view(request, itinerary_id):
    """
    Vista para mostrar la página 'Añadir Paradas' y cargar recomendaciones.
    """
    # Obtenemos el itinerario que se está editando (o creando)
    # Asegúrate de que el usuario actual sea el dueño
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)

    # --- Lógica para Recomendaciones ---
    recommended_places = []
    popular_places = [] # Dejaremos esto simple por ahora

    try:
        profile = request.user.profile
        preferred_categories = profile.preferred_categories.all()

        if preferred_categories.exists():
            # Busca lugares que pertenezcan a las categorías preferidas del usuario
            # Excluye lugares que ya podrían estar en el itinerario (si aplica)
            recommended_places = TouristicPlace.objects.filter(
                categories__in=preferred_categories
            ).distinct().prefetch_related('categories')[:6] # Limita a 6 recomendaciones
            # El .distinct() es importante si un lugar tiene varias categorías preferidas
        else:
            # Si no hay preferencias, muestra lugares aleatorios o los más populares
            recommended_places = TouristicPlace.objects.order_by('?')[:6] # '?' para aleatorio (puede ser lento en BD grandes)

        # Lógica simple para "Populares": por ahora, solo más lugares aleatorios diferentes
        popular_places = TouristicPlace.objects.exclude(
            id__in=[p.id for p in recommended_places] # Excluye los ya recomendados
        ).order_by('?')[:6]

    except Exception as e:
        print(f"Error al obtener recomendaciones: {e}")
        # En caso de error, simplemente no mostramos recomendaciones

    google_api_key = os.environ.get('GOOGLE_API_KEY')
    if not google_api_key:
        print("Advertencia: GOOGLE_API_KEY no encontrada.")
        google_api_key = "" # Evita errores en la plantilla


    # --- Prepara el contexto para la plantilla ---
    context = {
        'itinerary': itinerary,
        'recommended_places': recommended_places,
        'popular_places': popular_places,
        # Puedes pasar el itinerario actual como JSON si el JS lo necesita al cargar
        # 'current_itinerary_json': ...,
        'google_api_key': google_api_key,
    }

    # Renderiza la plantilla HTML
    return render(request, 'itineraries/add_stops.html', context) # Asume que el HTML está en templates/itineraries/


@login_required
def edit_itinerary_view(request, itinerary_id):
    """
    Vista para MOSTRAR el formulario de edición de itinerario (Paso 1).
    El guardado (POST/PATCH) lo manejará la API a través de JavaScript.
    """
    # Obtiene el itinerario existente o da 404
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)
    
    # Solo maneja GET para mostrar el formulario con datos
    context = {
        'itinerary': itinerary, # Pasa el objeto para rellenar el form en el HTML
        'mode': 'Editar',       # Indica al template que estamos en modo edición
    }
    return render(request, 'itineraries/create_edit_itinerary.html', context)


# Vista de seguridad para el autocompletado y el uso de la API de Geocoding de Google
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])  # Solo usuarios autenticados pueden usar esta vista
def geocode_autocomplete_api_view(request):
    """
    Proxy endpoint for geocoding/autocomplete suggestions.
    Calls an external API securely using the backend API key.
    """
    query = request.query_params.get('query', None)
    if not query or len(query) < 3:
        return Response({"error": "Query parameter 'query' is required (min 3 chars)."}, status=status.HTTP_400_BAD_REQUEST)

    # --- CHOOSE YOUR GEOCODING API ---
    # Example using Google Places Autocomplete API
    # Support both env var names for flexibility
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE API key not found (expected GOOGLE_API_KEY or GOOGLE_API_KEY).")
        return Response({"error": "Server configuration error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    external_api_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    # Restrict to Mexico using components=country:mx
    params = {
        'input': query,
        'key': api_key,
        'language': 'es',
        'types': '(cities)', # Example: restrict to cities
        'components': 'country:mx',
    }

    try:
        response = requests.get(external_api_url, params=params, timeout=5)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        # Process Google's response - Autocomplete returns 'predictions'
        if data.get('status') != 'OK':
            print(f"Google API Error: {data.get('status')} - {data.get('error_message')}")
            return Response({"error": "Could not fetch suggestions from provider."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        predictions = data.get('predictions', [])

        # Desired Mexican states (normalized checks)
        desired_states = [
            'estado de méxico', 'estado de mexico', 'méxico', 'mexico', # Estado de México may appear as 'Estado de México' or 'México'
            'ciudad de méxico', 'cdmx',
            'morelos', 'hidalgo', 'tlaxcala', 'puebla'
        ]

        # Helper to check if an administrative_area_level_1 matches desired states
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

        # To avoid excessive Place Details calls, limit how many predictions we inspect
        MAX_DETAILS_CALLS = 6
        suggestions = []

        # For each prediction, call Place Details (limited) and filter by admin area
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"

        details_calls = 0
        for p in predictions:
            if details_calls >= MAX_DETAILS_CALLS:
                break
            place_id = p.get('place_id')
            if not place_id:
                continue

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
                # Count this as a details call even if not OK, to avoid loops
                details_calls += 1
            except requests.exceptions.RequestException as e:
                print(f"Error calling Place Details for {place_id}: {e}")
                details_calls += 1
                continue

        # If we found allowed suggestions, return them
        if suggestions:
            return Response(suggestions)

        # Fallback: if filtering by state returned nothing, return the (Mexico-only) predictions limited
        fallback = [{"description": p.get('description')} for p in predictions][:10]
        return Response(fallback)

    except requests.exceptions.RequestException as e:
        print(f"Error calling external geocoding API: {e}")
        return Response({"error": "Error connecting to geocoding service."}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception as e:
        print(f"Unexpected error in geocode autocomplete: {e}")
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
        # Obtiene el itinerario asegurándose que pertenece al usuario autenticado
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

            
            

    

# Vista para visualizar el itinerario antes de ser creado definitivamente
# itineraries/<int:itinerary_id>/preview/
@login_required
def itinerary_preview_view(request, itinerary_id):
    """
    Muestra una vista previa del itinerario (no lo publica ni lo guarda).
    El usuario debe ser el propietario del itinerario.
    Contexto enviado a la plantilla:
      - itinerary: objeto Itinerary
      - stops_by_day: lista de tuplas (day_number, [stops ordenadas por placement])
    """
    # Obtiene el itinerario asegurando que pertenece al usuario autenticado
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)

    # Obtén las paradas ordenadas (el modelo ya define ordering por day_number, placement)
    stops_qs = ItineraryStop.objects.filter(itinerary=itinerary).select_related('touristic_place')

    # Agrupar por día
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

    context = {
        'itinerary': itinerary,
        'stops_by_day': stops_by_day,
    }

    return render(request, 'itineraries/preview_itinerary.html', context)

# Vista API para optimizar el orden de las paradas de un día usando el algoritmo del "Vecino más Cercano"
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
    # Obtiene el itinerario asegurando que pertenece al usuario autenticado y está publicado
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user, status='published')

    # Obtén las paradas ordenadas (el modelo ya define ordering por day_number, placement)
    stops_qs = ItineraryStop.objects.filter(itinerary=itinerary).select_related('touristic_place')

    # Agrupar por día
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

    context = {
        'itinerary': itinerary,
        'stops_by_day': stops_by_day,
    }

    return render(request, 'itineraries/view_itinerary.html', context)