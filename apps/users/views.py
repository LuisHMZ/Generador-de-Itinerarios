from django.db.models import Q  
from django.shortcuts import render, redirect, get_object_or_404 
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.utils import timezone

from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.adapter import get_adapter
from allauth.account.signals import user_signed_up # <-- ¡AÑADE ESTA!
from django.contrib.auth import get_user_model # Necesario para el sender
User = get_user_model()
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

# --- IMPORTACIONES PARA EL FEED MIXTO ---
from itertools import chain
from operator import attrgetter
from django.utils import timezone
from datetime import timedelta

# --- MODELOS Y FORMULARIOS ---
from .forms import SimpleSignupForm
from .models import Profile 
from apps.posts.forms import CreatePostForm
from apps.alertas.models import Notification
from apps.posts.models import Post
from apps.itineraries.models import Itinerary
from friendship.models import Friend, FriendshipRequest 
from friendship.exceptions import AlreadyFriendsError, AlreadyExistsError 

User = get_user_model()


# --- VISTAS DE AUTENTICACIÓN (Register, Login, Logout) ---
import traceback

def simple_register_view(request):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        form = SimpleSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                profile = user.profile
                profile.birth_date = form.cleaned_data.get('birth_date')
                profile.save()
            except Profile.DoesNotExist:
                # Backup por si la señal falla (o aún no se ha ejecutado)
                Profile.objects.create(user=user, birth_date=form.cleaned_data.get('birth_date'))
            # --- ¡NUEVO Y CORREGIDO! ENVIAR CORREO DE VERIFICACIÓN USANDO EL ADAPTADOR ---
            # --- ¡DISPARA LA SEÑAL MANUALMENTE! ---
            print(f"VIEW: Usuario '{user.username}' creado. Intentando enviar correo directamente...")
            email_sent = False
            try:
                    email_address, created = EmailAddress.objects.get_or_create(
                        user=user,
                        email=user.email,
                        defaults={'primary': True, 'verified': False}
                    )
                    if not email_address.verified:
                        confirmation = EmailConfirmation.create(email_address)
                        if confirmation and confirmation.key:
                            print(f"VIEW: EmailConfirmation creado con Key: '{confirmation.key}'")
                            confirmation.sent = timezone.now()
                            confirmation.save(update_fields=['sent']) # Guarda solo este campo
                            print(f"VIEW: Campo 'sent' establecido manualmente a {confirmation.sent}")
                            # -----------------------------

                            # Llama a send() (que intentará establecer 'sent' de nuevo, pero no importa
                            get_adapter(request).send_confirmation_mail(request, confirmation, signup=True)
                            email_sent = True
                            print(f'VIEW: Correo de confirmación enviado a {user.email}')
                        else:
                             print("VIEW ERROR: Fallo al crear EmailConfirmation o la clave está vacía.")
                    else:
                        print(f"VIEW: Email {user.email} ya estaba verificado.")
                        email_sent = True # Considerarlo "enviado" ya que está verificado

            except Exception as e:
                    print(f"VIEW ERROR: Error enviando email de confirmación para {user.email}: {e}")
                    traceback.print_exc()
                # ------------------------------------------

                # --- Respuesta ---
            success_message = '¡Registro casi completo!'
            if email_sent:
                    success_message += ' Se ha enviado un correo de verificación a tu email.'
            else:
                    success_message += ' Hubo un problema enviando el correo. Contacta soporte.'
            # Responde según si es fetch o no
            """ if is_ajax:
                return JsonResponse({'status': 'success', 'message': '¡Registro exitoso!'})
            else:
                messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
                # Redirige a la página de login (puedes usar la de allauth si la mantienes)
                return redirect('account_login') """
            if is_ajax:
                # Le decimos al frontend que el registro fue OK, pero necesita verificar
                return JsonResponse({'status': 'success', 'message': success_message})
            else:
                messages.success(request, success_message)
                # Ya no redirigimos a login, sino a una página informativa o a home
                # Podrías crear una plantilla que diga "Revisa tu email"
                return redirect('') # O a una URL específica 'account_email_verification_sent' si la creas
            # --- FIN AJUSTE RESPUESTA ---
        else:
            if is_ajax:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            else:
                messages.error(request, 'Por favor corrige los errores abajo.')
                # El return render al final manejará mostrar el form con errores

    else: # Si es una petición GET (mostrar el formulario)
        form = SimpleSignupForm()
    return render(request, 'users/simple_register.html', {'form': form})

def simple_login_view(request):
    if request.user.is_authenticated:
        return redirect('home') 
    
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            email_record = EmailAddress.objects.filter(user=user, email=user.email).first()
            if not email_record or not email_record.verified:
                return JsonResponse({
                'status': 'error',
                'message': 'Debes verificar tu correo antes de iniciar sesión.'
            }, status=403)
            # Inicia la sesión del usuario
            auth_login(request, user)
            messages.success(request, f'Ha iniciado sesión exitosamente como {user.first_name or user.username}.')
            # Responde según si es fetch o no
            if is_ajax:
                redirect_url = request.session.get('next', reverse('home'))
                return JsonResponse({'status': 'success', 'message': '¡Inicio de sesión exitoso!', 'redirect_url': redirect_url})
            else:
                return redirect('home')
        else:
            if is_ajax:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'users/simple_login.html', {'form': form})

def simple_logout_view(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    auth_logout(request)
    if is_ajax:
        return JsonResponse({'status': 'success', 'message': 'Sesión cerrada.'})
    else:
        return redirect('simple_login')


# # --- VISTA DEL FEED PRINCIPAL (MIXTO) ---

# @login_required
# def home_feed_view(request):
#     """
#     Feed principal: Muestra Posts + Itinerarios mezclados.
#     """
#     # 1. Formulario para crear post
#     create_post_form = CreatePostForm(user=request.user)

#     # 2. Filtro de usuarios (Amigos + Yo)
#     try:
#         my_friends = Friend.objects.friends(request.user)
#         users_to_show = [f.id for f in my_friends] + [request.user.id]
#     except Exception:
#         users_to_show = [request.user.id]
#         my_friends = []

#    # 3. Obtener POSTS
#     try:
#         posts = Post.objects.filter(
#             Q(user__in=users_to_show) | Q(visibility='public') 
#         ).select_related(
#             'user', 'user__profile'
#         ).prefetch_related(
#             'pictures', 'likes', 'saved_by', 'comments'
#         ).distinct()
#     except Exception:
#         posts = []

#     # 4. Obtener ITINERARIOS
#     itineraries = Itinerary.objects.filter(
#          user_id__in=users_to_show 
#     ).select_related('user')

#     # 5. Etiquetar tipos
#     for post in posts:
#         post.feed_type = 'post'
#     for itinerary in itineraries:
#         itinerary.feed_type = 'itinerary'

#     # 6. Fusionar y Ordenar
#     feed_items = sorted(
#         chain(posts, itineraries),
#         key=attrgetter('created_at'),
#         reverse=True
#     )

#     # 7. Lógica de Amigos / Online
#     users_list = User.objects.exclude(id=request.user.id)
#     time_threshold = timezone.now() - timedelta(minutes=15)
#     online_friends = []
#     for friend in my_friends:
#         if friend.last_login and friend.last_login > time_threshold:
#             online_friends.append(friend)

#     users_with_status = []
#     for user in users_list:
#         status_data = {'user': user, 'status': None, 'request_id': None}
#         if user in my_friends:
#             status_data['status'] = 'FRIENDS'
#         else:
#             sent = FriendshipRequest.objects.filter(from_user=request.user, to_user=user, rejected__isnull=True).first()
#             if sent:
#                 status_data['status'] = 'PENDING_SENT'
#                 status_data['request_id'] = sent.id
#             else:
#                 recv = FriendshipRequest.objects.filter(from_user=user, to_user=request.user, rejected__isnull=True).first()
#                 if recv:
#                     status_data['status'] = 'PENDING_RECEIVED'
#                     status_data['request_id'] = recv.id
#         users_with_status.append(status_data)

#     context = {
#         'feed_items': feed_items,      
#         'users_with_status': users_with_status,
#         'online_friends': online_friends,
#         'create_post_form': create_post_form,
#     }
#     return render(request, 'feed/home_feed.html', context)


# --- VISTAS DE AMISTAD ---

@login_required
def send_friend_request(request, to_user_id):
    recipient = get_object_or_404(User, id=to_user_id)
    sender = request.user
    if sender == recipient:
        messages.error(request, "No puedes enviarte solicitud a ti mismo.")
        return redirect('home') 
    
    try:
        if Friend.objects.are_friends(sender, recipient):
            raise AlreadyFriendsError
        if FriendshipRequest.objects.filter(from_user=sender, to_user=recipient, rejected__isnull=True).exists() or \
           FriendshipRequest.objects.filter(from_user=recipient, to_user=sender, rejected__isnull=True).exists():
            raise AlreadyExistsError

        # Limpiar rechazos previos
        FriendshipRequest.objects.filter(from_user=sender, to_user=recipient, rejected__isnull=False).delete()
        FriendshipRequest.objects.filter(from_user=recipient, to_user=sender, rejected__isnull=False).delete()

        FriendshipRequest.objects.create(from_user=sender, to_user=recipient)

        try:
            link = request.build_absolute_uri(reverse('friend_requests_view'))
        except Exception:
            link = '#'
        Notification.objects.create(recipient=recipient, actor=sender, message=f'{sender.username} te ha enviado una solicitud de amistad.', link=link)
        messages.success(request, f"Solicitud enviada a {recipient.username}.")
        
    except AlreadyFriendsError:
        messages.error(request, f"Ya eres amigo de {recipient.username}.")
    except AlreadyExistsError:
        messages.error(request, f"Ya existe una solicitud pendiente.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect('home')

@login_required
def friend_requests_view(request):
    # --- CORRECCIÓN: Usamos los nombres exactos que el HTML espera ---
    friend_requests = FriendshipRequest.objects.filter(to_user=request.user, rejected__isnull=True).order_by('-created')
    friends = Friend.objects.friends(request.user)
    
    context = {
        'friend_requests': friend_requests, # Antes era 'pending_requests'
        'friends': friends,                 # Antes era 'my_friends'
    }
    return render(request, 'feed/friend_requests.html', context)

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendshipRequest, id=request_id, to_user=request.user)
    try:
        friend_request.accept()
        try:
            link = request.build_absolute_uri(reverse('profile_view', args=[request.user.username]))
        except Exception:
            link = '#' 
        Notification.objects.create(recipient=friend_request.from_user, actor=request.user, message=f'{request.user.username} aceptó tu solicitud.', link=link)
        messages.success(request, f"¡Ahora eres amigo de {friend_request.from_user.username}!")
    except Exception as e:
        messages.error(request, f"Error al aceptar: {e}")
    return redirect('friend_requests_view') # Redirige a la misma lista para ver cambios

@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendshipRequest, id=request_id, to_user=request.user)
    try:
        friend_request.reject()
        messages.warning(request, f"Has rechazado la solicitud.")
    except Exception as e:
        messages.error(request, f"Error al rechazar: {e}")
    return redirect('friend_requests_view')

@login_required
def remove_friend(request, user_id):
    friend_to_remove = get_object_or_404(User, id=user_id)
    sender = request.user
    try:
        Friend.objects.remove_friend(sender, friend_to_remove)
        messages.success(request, f"Eliminaste a {friend_to_remove.username} de tus amigos.")
    except Exception as e:
        messages.error(request, f"Error al eliminar: {e}")
    return redirect('friend_requests_view')

@login_required
def cancel_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendshipRequest, id=request_id, from_user=request.user)
    try:
        friend_request.delete()
        messages.success(request, "Solicitud cancelada.")
    except Exception as e:
        messages.error(request, f"Error al cancelar: {e}")
    return redirect('home')


# --- VISTA DE PERFIL ---

@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    try:
        user_posts = Post.objects.filter(user=profile_user).select_related('user', 'user__profile').prefetch_related('pictures').order_by('-created_at')
    except Exception:
        user_posts = []
    
    is_self = (request.user == profile_user)
    friendship_status = None
    pending_request_id = None 
    
    if not is_self:
        if Friend.objects.are_friends(request.user, profile_user):
            friendship_status = 'FRIENDS'
        else:
            sent = FriendshipRequest.objects.filter(from_user=request.user, to_user=profile_user, rejected__isnull=True).first()
            if sent:
                friendship_status = 'PENDING_SENT'
                pending_request_id = sent.id 
            else:
                recv = FriendshipRequest.objects.filter(from_user=profile_user, to_user=request.user, rejected__isnull=True).first()
                if recv:
                    friendship_status = 'PENDING_RECEIVED'
                    pending_request_id = recv.id 
                else:
                    friendship_status = 'NOT_FRIENDS'
            
    context = {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'is_self': is_self,
        'friendship_status': friendship_status,
        'pending_request_id': pending_request_id, 
    }
    return render(request, 'users/profile.html', context)