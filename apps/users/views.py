# apps/users/views.py

from django.shortcuts import render, redirect, get_object_or_404 
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import json 

from .forms import SimpleSignupForm
from .models import Profile # Importa tu modelo Profile

# --- Importaciones de la Lógica Social (Agregado por Luis) ---
from apps.alertas.models import Notification
from apps.posts.models import Post
from friendship.models import Friend, FriendshipRequest 
from friendship.exceptions import AlreadyFriendsError, AlreadyExistsError # Necesario para el manejo de excepciones
from django.utils import timezone
from datetime import timedelta
# --- Fin de importaciones sociales ---


# --- Definimos el Modelo de User UNA SOLA VEZ ---
User = get_user_model()


# Vista de registro simple (Tu código original)
def simple_register_view(request):
    if request.method == 'POST':
        # Detecta si es una petición AJAX/Fetch (busca la cabecera X-Requested-With)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        form = SimpleSignupForm(request.POST)

        if form.is_valid():
            user = form.save() # UserCreationForm guarda el usuario y hashea la contraseña

            # Intenta guardar la fecha de nacimiento en el Profile
            # (Asume que la señal post_save ya creó el Profile)
            try:
                profile = user.profile
                profile.birth_date = form.cleaned_data.get('birth_date')
                profile.save()
            except Profile.DoesNotExist:
                # Backup por si la señal falla (o aún no se ha ejecutado)
                Profile.objects.create(user=user, birth_date=form.cleaned_data.get('birth_date'))

            # Responde según si es fetch o no
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': '¡Registro exitoso!'})
            else:
                messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
                # Redirige a la página de login (puedes usar la de allauth si la mantienes)
                return redirect('account_login')
        else:
            # Si el formulario no es válido
            if is_ajax:
                # Devuelve los errores como JSON, con estado 400
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            else:
                messages.error(request, 'Por favor corrige los errores abajo.')
                # El return render al final manejará mostrar el form con errores

    else: # Si es una petición GET (mostrar el formulario)
        form = SimpleSignupForm()

    # Renderiza la plantilla para GET o para POST fallido (no AJAX)
    return render(request, 'users/simple_register.html', {'form': form})

# Vista para inicio de sesión simple (Tu código original)
def simple_login_view(request):
    if request.user.is_authenticated:
        # Detectar si es una petición AJAX/Fetch (usa la cabecera X-Requested-With)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({'status': 'already_authenticated', 'message': 'Ya has iniciado sesión.'})
        else:
            return redirect('home') # El LOGIN_REDIRECT_URL debería manejar esto
    
    # Manejo del formulario de login aquí
    if request.method == 'POST':
        # Detecta si es una petición AJAX/Fetch (busca la cabecera X-Requested-With)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        # Usa el autenticador de Django
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            # Obtiene el usuario validado
            user = form.get_user()
            # Inicia la sesión del usuario
            auth_login(request, user)

            # Responde según si es fetch o no
            if is_ajax:
                # Obtenemos la URL a la que redirigir si el usuario vino de otra página
                redirect_url = request.session.get('next', reverse('home'))
                return JsonResponse({'status': 'success', 'message': '¡Inicio de sesión exitoso!', 'redirect_url': redirect_url})
            else:
                return redirect('home')
        else:
            # Si el formulario no es válido
            if is_ajax:
                # Devuelve los errores como JSON, con estado 400
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
    
    else: # Si es una petición GET (mostrar el formulario)
        form = AuthenticationForm()

    # Renderiza la plantilla para GET o para POST fallido (no AJAX)
    return render(request, 'users/simple_login.html', {'form': form})

# Vista para cerrar sesión (Tu código original)
def simple_logout_view(request):
    """Cierra la sesión del usuario actual."""
    # Detectar si es una petición AJAX/Fetch (usa la cabecera X-Requested-With)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    auth_logout(request)
    if is_ajax:
        return JsonResponse({'status': 'success', 'message': 'Sesión cerrada.'})
    else:
        return redirect('simple_login')

# VISTA DEL FEED PRINCIPAL 

@login_required
def home_feed_view(request):
    """
    Esta vista maneja el feed principal, mostrando posts públicos,
    lista de usuarios y amigos en línea.
    """
    
    # 1. Obtenemos todas las publicaciones
    try:
        all_posts = Post.objects.all().select_related(
            'user', 'user__profile'
        ).prefetch_related(
            'pictures' 
        ).order_by('-created_at')
    except Exception as e:
        print(f"Error obteniendo posts: {e}") 
        all_posts = []

    # 2. Listas de usuarios y amigos
    users_list = User.objects.exclude(id=request.user.id)
    my_friends = Friend.objects.friends(request.user)
    pending_requests = FriendshipRequest.objects.filter(to_user=request.user, rejected__isnull=True)

    # --- ▼▼▼ LÓGICA DE AMIGOS EN LÍNEA (NUEVO) ▼▼▼ ---
    # Consideramos "En línea" si se conectó en los últimos 15 minutos
    time_threshold = timezone.now() - timedelta(minutes=15)
    online_friends = []
    
    for friend in my_friends:
        if friend.last_login and friend.last_login > time_threshold:
            online_friends.append(friend)
    # --- ▲▲▲ FIN LÓGICA NUEVA ▲▲▲ ---

    users_with_status = []
    for user in users_list:
        status_data = {
            'user': user,
            'status': None,
            'request_id': None
        }
        
        if user in my_friends:
            status_data['status'] = 'FRIENDS'
        else:
            sent_request = FriendshipRequest.objects.filter(from_user=request.user, to_user=user, rejected__isnull=True).first()
            if sent_request:
                status_data['status'] = 'PENDING_SENT'
                status_data['request_id'] = sent_request.id
            else:
                received_request = FriendshipRequest.objects.filter(from_user=user, to_user=request.user, rejected__isnull=True).first()
                if received_request:
                    status_data['status'] = 'PENDING_RECEIVED'
                    status_data['request_id'] = received_request.id

        users_with_status.append(status_data)

    context = {
        'posts': all_posts, 
        'users_with_status': users_with_status,
        'online_friends': online_friends, # <-- Pasamos la lista a la plantilla
    }
    return render(request, 'feed/home_feed.html', context)

# VISTA PARA ENVIAR SOLICITUD DE AMISTAD

@login_required
def send_friend_request(request, to_user_id):
    """
    Procesa el envío de una solicitud de amistad.
    """
    recipient = get_object_or_404(User, id=to_user_id)
    sender = request.user
    
    if sender == recipient:
        messages.error(request, "No puedes enviarte una solicitud a ti mismo.")
        return redirect('home') 
    
    try:
        # 1. Verificar si ya son amigos
        if Friend.objects.are_friends(sender, recipient):
            raise AlreadyFriendsError

        # 2. Verificar si hay solicitudes ACTIVAS (Pendientes y NO rechazadas)
        #    rejected__isnull=True significa "que no ha sido rechazada"
        if FriendshipRequest.objects.filter(from_user=sender, to_user=recipient, rejected__isnull=True).exists() or \
           FriendshipRequest.objects.filter(from_user=recipient, to_user=sender, rejected__isnull=True).exists():
            raise AlreadyExistsError

        # --- ▼▼▼ LÓGICA NUEVA: LIMPIEZA DE RECHAZADOS ▼▼▼ ---
        # Si hubo una solicitud anterior que FUE RECHAZADA, la borramos
        # para permitir un nuevo intento.
        FriendshipRequest.objects.filter(from_user=sender, to_user=recipient, rejected__isnull=False).delete()
        FriendshipRequest.objects.filter(from_user=recipient, to_user=sender, rejected__isnull=False).delete()
        # --- ▲▲▲ FIN DE LÓGICA NUEVA ▲▲▲ ---

        # 3. Crear la nueva solicitud
        FriendshipRequest.objects.create(from_user=sender, to_user=recipient)

        # 4. Crear Notificación
        try:
            link = request.build_absolute_uri(reverse('friend_requests_view'))
        except Exception:
            link = '#'

        Notification.objects.create(
            recipient=recipient,
            actor=sender,
            message=f'{sender.username} te ha enviado una solicitud de amistad.',
            link=link
        )

        messages.success(request, f"Solicitud enviada a {recipient.username}.")
        
    except AlreadyFriendsError:
        messages.error(request, f"Error: Ya eres amigo de {recipient.username}.")
    except AlreadyExistsError:
        messages.error(request, f"Error: Ya existe una solicitud pendiente con {recipient.username}.")
    except Exception as e:
        messages.error(request, f"Error desconocido en BD: {e}")
        
    return redirect('home')


# VISTA PARA LISTAR SOLICITUDES RECIBIDAS
@login_required
def friend_requests_view(request):
    """
    Muestra la lista de solicitudes de amistad PENDIENTES 
    y la lista de AMIGOS ACTUALES.
    """
    # 1. Solicitudes pendientes (tu código original)
    pending_requests = FriendshipRequest.objects.filter(
        to_user=request.user, 
        rejected__isnull=True  
    ).order_by('-created')
    
    # --- ▼▼▼ AÑADE ESTA LÍNEA ▼▼▼ ---
    # 2. Amigos actuales
    my_friends = Friend.objects.friends(request.user)
    # --- ▲▲▲ FIN DEL CÓDIGO AÑADIDO ▲▲▲ ---

    context = {
        'pending_requests': pending_requests,
        'has_requests': pending_requests.exists(),
        'my_friends': my_friends, # <-- Añadido al contexto
    }
    return render(request, 'feed/friend_requests.html', context)


# VISTA PARA ACEPTAR SOLICITUD
# En: apps/users/views.py

# VISTA PARA ACEPTAR SOLICITUD
@login_required
def accept_friend_request(request, request_id):
    """
    Procesa la aceptación de una solicitud de amistad por parte del receptor.
    """
    friend_request = get_object_or_404(FriendshipRequest, id=request_id, to_user=request.user)
    
    try:
        # 1. Se acepta la solicitud (tu código original)
        friend_request.accept()

        # --- ▼▼▼ CÓDIGO DE NOTIFICACIÓN AÑADIDO ▼▼▼ ---
        try:
            # ¡IMPORTANTE! Asegúrate de que el 'name=' de tu URL
            # para ver perfiles sea 'user_profile' (o como se llame)
            link = request.build_absolute_uri(reverse('user_profile', args=[request.user.username]))
        except Exception:
            link = '#' # Link de respaldo si falla el reverse

        Notification.objects.create(
            recipient=friend_request.from_user, # Notificación PARA el que la envió
            actor=request.user,                 # Creada POR el que aceptó
            message=f'{request.user.username} aceptó tu solicitud de amistad.',
            link=link
        )
        # --- ▲▲▲ FIN DEL CÓDIGO AÑADIDO ▲▲▲ ---

        messages.success(request, f"¡Has aceptado la solicitud de {friend_request.from_user.username}! Ahora son amigos.")
        
    except Exception as e:
        messages.error(request, f"Error al aceptar: {e}")
        
    return redirect('home')

# VISTA PARA RECHAZAR SOLICITUD
@login_required
def reject_friend_request(request, request_id):
    """
    Procesa el rechazo de una solicitud de amistad por parte del receptor.
    """
    friend_request = get_object_or_404(FriendshipRequest, id=request_id, to_user=request.user)
    try:
        friend_request.reject()
        messages.warning(request, f"Has rechazado la solicitud de {friend_request.from_user.username}.")
    except Exception as e:
        messages.error(request, f"Error al rechazar: {e}")
    return redirect('home')

# VISTA PARA ELIMINAR AMIGO (NUEVA)
@login_required
def remove_friend(request, user_id):
    """
    Procesa la eliminación de una amistad existente.
    """
    friend_to_remove = get_object_or_404(User, id=user_id)
    sender = request.user
    try:
        Friend.objects.remove_friend(sender, friend_to_remove)
        messages.success(request, f"Has eliminado a {friend_to_remove.username} de tu lista de amigos.")
    except Exception as e:
        messages.error(request, f"Error al eliminar amigo: {e}")
    return redirect('home')

# --- VISTA PARA CANCELAR SOLICITUD ENVIADA (NUEVA) ---
@login_required
def cancel_friend_request(request, request_id):
    """
    Procesa la cancelación de una solicitud de amistad ENVIADA por el usuario.
    """
    # 1. Obtener la solicitud, asegurándose de que el usuario logueado es el EMISOR
    friend_request = get_object_or_404(FriendshipRequest, id=request_id, from_user=request.user)
    
    # 2. Guardar el nombre del receptor para el mensaje
    recipient_name = friend_request.to_user.username
    
    try:
        # 3. Borrar la solicitud de la base de datos
        friend_request.delete()
        messages.success(request, f"Has cancelado tu solicitud de amistad a {recipient_name}.")
        print(f"\n--- DEBUG: SOLICITUD CANCELADA --- {request.user.username} canceló la solicitud a {recipient_name}")

    except Exception as e:
        messages.error(request, f"Error al cancelar la solicitud: {e}")
        print(f"\n--- DEBUG: ERROR AL CANCELAR --- {e}")
        
    return redirect('home')


@login_required
def profile_view(request, username):
    """
    Muestra el perfil de un usuario. Es dinámica:
    - Muestra "Editar" si es tu propio perfil.
    - Muestra "Añadir Amigo" si es de otro.
    """
    
    profile_user = get_object_or_404(User, username=username)
    
    try:
        user_posts = Post.objects.filter(user=profile_user).select_related(
            'user', 'user__profile'
        ).prefetch_related(
            'pictures'
        ).order_by('-created_at')
    except Exception as e:
        print(f"Error obteniendo posts para el perfil: {e}")
        user_posts = []
    
    is_self = (request.user == profile_user)
    
    # --- ▼▼▼ BLOQUE MODIFICADO ▼▼▼ ---
    friendship_status = None
    pending_request_id = None  # 1. Inicializamos la variable
    
    if not is_self:
        if Friend.objects.are_friends(request.user, profile_user):
            friendship_status = 'FRIENDS'
        else:
            # Revisa si yo le envié una solicitud
            sent_request = FriendshipRequest.objects.filter(from_user=request.user, to_user=profile_user, rejected__isnull=True).first()
            if sent_request:
                friendship_status = 'PENDING_SENT'
                pending_request_id = sent_request.id # 2. Guardamos el ID
            else:
                # Revisa si él me envió una solicitud
                received_request = FriendshipRequest.objects.filter(from_user=profile_user, to_user=request.user, rejected__isnull=True).first()
                if received_request:
                    friendship_status = 'PENDING_RECEIVED'
                    pending_request_id = received_request.id # 2. Guardamos el ID
                else:
                    friendship_status = 'NOT_FRIENDS'
    # --- ▲▲▲ FIN DEL BLOQUE ▲▲▲ ---
            
    context = {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'is_self': is_self,
        'friendship_status': friendship_status,
        'pending_request_id': pending_request_id, 
    }
    
    return render(request, 'users/profile.html', context)