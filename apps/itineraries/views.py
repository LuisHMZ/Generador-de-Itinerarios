# apps/itineraries/views.py

import requests    # Para llamar a la API de Google Places
import os          # Para leer variables de entorno

from django.conf import settings # Para acceder a la configuración del proyecto
from django.shortcuts import render, get_object_or_404, redirect     # Para renderizar plantillas HTML y obtener objetos o 404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required  # Para requerir login en vistas basadas en funciones

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

# --- Definimos el Modelo de User UNA SOLA VEZ ---
User = get_user_model()


# --- VISTA DEL FEED SOCIAL (home_view) ---
@login_required
def home_view(request):
    """
    Esta vista maneja la página principal ('/home/')
    y ahora sirve el NUEVO diseño del feed (feed/feed.html)
    con datos REALES de la base de datos (Posts y Amigos).
    """
    if request.user.is_authenticated:
        
        user = request.user
        
        # --- 1. LÓGICA DE POSTS ---
        try:
            friend_ids_list = [f.id for f in Friend.objects.friends(user)]
            posts = Post.objects.filter(
                author_id__in=friend_ids_list + [user.id]
            ).order_by('-created_at')
        except Exception as e:
            print(f"Error obteniendo posts: {e}")
            posts = []

        # --- 2. LÓGICA DE AMIGOS (Sugerencias y Estado) ---
        try:
            friends_ids = [f.id for f in Friend.objects.friends(user)]
            sent_requests = FriendshipRequest.objects.filter(from_user=user, rejected__isnull=True)
            sent_ids = sent_requests.values_list('to_user_id', flat=True)
            received_requests = FriendshipRequest.objects.filter(to_user=user, rejected__isnull=True)
            received_ids = received_requests.values_list('from_user_id', flat=True)

            all_other_users = User.objects.exclude(id=user.id)
            
            users_with_status = []
            for other_user in all_other_users:
                status = 'NONE'
                request_id = None
                
                if other_user.id in friends_ids:
                    status = 'FRIENDS'
                elif other_user.id in sent_ids:
                    status = 'PENDING_SENT'
                    req = sent_requests.filter(to_user=other_user).first()
                    if req: request_id = req.id
                elif other_user.id in received_ids:
                    status = 'PENDING_RECEIVED'
                    req = received_requests.filter(from_user=other_user).first()
                    if req: request_id = req.id

                users_with_status.append({
                    'user': other_user,
                    'status': status,
                    'request_id': request_id, 
                })
        except Exception as e:
            print(f"Error obteniendo sugerencias de amigos: {e}")
            users_with_status = []

        # --- 3. LÓGICA DE NOTIFICACIONES ---
        try:
            # Buscamos las notificaciones NO LEÍDAS para este usuario
            notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')
        except Exception as e:
            print(f"Error obteniendo notificaciones: {e}")
            notifications = []

        # 4. Enviar los datos a la NUEVA plantilla
        context = {
            'posts': posts, 
            'users_with_status': users_with_status,
            'notifications': notifications
        }
        
        return render(request, 'feed/home_feed.html', context)
    
    else:
        return redirect('account_login')


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

    local_results = []
    place_ids_found_locally = set()

    # --- 1. Buscar en la Base de Datos Local ---
    try:
        local_places = TouristicPlace.objects.filter(name__icontains=query)[:10]
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
            search_body = {'textQuery': query, 'languageCode': 'es', 'maxResultCount': 10}
            
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
                    google_v1_id = place_data_basic.get('name')
                    if not google_v1_id:
                        continue

                    existing_place = TouristicPlace.objects.filter(external_api_id=google_v1_id).first()
                    place_obj = None

                    if existing_place:
                        if existing_place.id not in place_ids_found_locally:
                            place_obj = existing_place
                    else:
                        # --- 3. Llamar a Place Details (v1) ---
                        details_url = f"https://places.googleapis.com/v1/{google_v1_id}"
                        
                        fields_mask = (
                            'id,displayName,formattedAddress,location,websiteUri,internationalPhoneNumber,'
                            'regularOpeningHours,rating,editorialSummary,photos'
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
                            print(f"!!! [ERROR] procesando detalles: {e_proc_details}")

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


# Vistas para la creación de itinerarios (HTML)

@login_required
def create_itinerary_view(request):
    context = {
        'itinerary': None,
        'mode': 'Crear',
    }
    return render(request, 'itineraries/create_edit_itinerary.html', context)

@login_required
def add_stops_view(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)

    recommended_places = []
    popular_places = [] 

    try:
        profile = request.user.profile
        preferred_categories = profile.preferred_categories.all()

        if preferred_categories.exists():
            recommended_places = TouristicPlace.objects.filter(
                categories__in=preferred_categories
            ).distinct().prefetch_related('categories')[:6]
        else:
            recommended_places = TouristicPlace.objects.order_by('?')[:6]

        popular_places = TouristicPlace.objects.exclude(
            id__in=[p.id for p in recommended_places]
        ).order_by('?')[:6]

    except Exception as e:
        print(f"Error al obtener recomendaciones: {e}")

    google_api_key = os.environ.get('GOOGLE_API_KEY') or ""

    context = {
        'itinerary': itinerary,
        'recommended_places': recommended_places,
        'popular_places': popular_places,
        'google_api_key': google_api_key,
    }

    return render(request, 'itineraries/add_stops.html', context)


@login_required
def edit_itinerary_view(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)
    context = {
        'itinerary': itinerary, 
        'mode': 'Editar',        
    }
    return render(request, 'itineraries/create_edit_itinerary.html', context)


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
    

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def itinerary_stops_api_view(request, itinerary_id):
    try:
        itinerary = Itinerary.objects.get(id=itinerary_id, user=request.user)
        stops = ItineraryStop.objects.filter(itinerary=itinerary).select_related('touristic_place')
        serialized_stops = ItineraryStopDetailSerializer(stops, many=True).data
        return Response(serialized_stops)
    
    except Itinerary.DoesNotExist:
        return Response({"error": "Itinerario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Error interno del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

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

    context = {
        'itinerary': itinerary,
        'stops_by_day': stops_by_day,
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
            link="#"
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
    
    return JsonResponse({'status': 'error', 'message': 'El comentario no puede estar vacío'}, status=400)