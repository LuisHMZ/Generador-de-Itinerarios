# Create your views here.
import requests     # Para llamar a la API de Google Places
import os         # Para leer variables de entorno

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
            search_body = {'textQuery': query, 'languageCode': 'es', 'maxResultCount': 10}
            
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
                            'photos'
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
                            print(f"!!! [ERROR] procesando detalles v1: {e_proc_details}")

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
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def itinerary_stops_api_view(request, itinerary_id):
    """
    Endpoint de API para obtener las paradas de un itinerario específico.
    """
    try:
        # Obtiene el itinerario asegurándose que pertenece al usuario autenticado
        itinerary = Itinerary.objects.get(id=itinerary_id, user=request.user)
        
        # Obtiene las paradas del itinerario (modelo intermedio) y los lugares turísticos asociados
        # Usamos select_related para traer el objeto `touristic_place` en la misma consulta.
        stops = ItineraryStop.objects.filter(itinerary=itinerary).select_related('touristic_place')

        # Serializamos las paradas: cada parada incluye el `touristic_place` anidado
        # y los campos `day_number` y `placement` que definen el orden.
        serialized_stops = ItineraryStopDetailSerializer(stops, many=True).data

        return Response(serialized_stops)
    
    except Itinerary.DoesNotExist:
        return Response({"error": "Itinerario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error obteniendo lugares del itinerario: {e}")
        return Response({"error": "Error interno del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

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

