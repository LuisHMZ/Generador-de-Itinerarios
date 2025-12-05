<<<<<<< HEAD
from django.db.models import Q  
from django.shortcuts import render, redirect, get_object_or_404 
=======
# apps/users/views.py

from django.shortcuts import render, redirect, get_object_or_404
>>>>>>> origin/feature/email-verification
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
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
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
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.decorators import user_passes_test

from .models import LoginLog

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
                return redirect('home') # O a una URL específica 'account_email_verification_sent' si la creas
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
<<<<<<< HEAD
        return redirect('home') 
=======
        # Detectar si es una petición AJAX/Fetch (usa la cabecera X-Requested-With)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({'status': 'already_authenticated', 'message': 'Ya has iniciado sesión.'})
        else:
            return redirect('home')  # Aún no tenemos home, se redirige al registro
>>>>>>> origin/feature/email-verification
    
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        form = AuthenticationForm(request, data=request.POST)
<<<<<<< HEAD
=======
        username_data = request.POST.get('username') # El form de Django usa 'username' para el input
        password_data = request.POST.get('password')
        # --- 1. VERIFICACIÓN MANUAL DE SUSPENSIÓN ---
        
        # ---------------------------------------------


>>>>>>> origin/feature/email-verification
        if form.is_valid():
            user = form.get_user()
            email_record = EmailAddress.objects.filter(user=user, email=user.email).first()
            if email_record and not email_record.verified:
                if is_ajax:
                    # AQUÍ ESTABA EL PROBLEMA: Devolvemos JSON con status 403
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Debes verificar tu correo electrónico antes de iniciar sesión.'
                    }, status=403)
                else:
                    messages.error(request, 'Debes verificar tu correo electrónico antes de iniciar sesión.')
                    return render(request, 'users/simple_login.html', {'form': form})
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
<<<<<<< HEAD
=======
            # Si el formulario no es válido
            if username_data and password_data:
                # Buscamos si el usuario existe para ver si está suspendido
                user_check = User.objects.filter(
                    Q(username=username_data) | Q(email=username_data)
                ).first()
                
                # Si existe, la contraseña es correcta, PERO está inactivo
                if user_check and user_check.check_password(password_data) and not user_check.is_active:
                    if is_ajax:
                        return JsonResponse({
                            'status': 'suspended',
                            'redirect_url': reverse('account_suspended'),
                            'message': 'Tu cuenta ha sido suspendida.'
                        }, status=403)
                    else:
                        return redirect('account_suspended')

            # Si no estaba suspendido, entonces es contraseña incorrecta real
>>>>>>> origin/feature/email-verification
            if is_ajax:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
<<<<<<< HEAD
    else:
=======
    
    else: # Si es una petición GET (mostrar el formulario)
>>>>>>> origin/feature/email-verification
        form = AuthenticationForm()
    return render(request, 'users/simple_login.html', {'form': form})

def simple_logout_view(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    auth_logout(request)
    if is_ajax:
        return JsonResponse({'status': 'success', 'message': 'Sesión cerrada.'})
    else:
<<<<<<< HEAD
        return redirect('simple_login')


# --- VISTA DEL FEED PRINCIPAL (MIXTO) ---

@login_required
def home_feed_view(request):
    """
    Feed principal: Muestra Posts + Itinerarios mezclados.
    """
    # 1. Formulario para crear post
    create_post_form = CreatePostForm(user=request.user)

    # 2. Filtro de usuarios (Amigos + Yo)
    try:
        my_friends = Friend.objects.friends(request.user)
        users_to_show = [f.id for f in my_friends] + [request.user.id]
    except Exception:
        users_to_show = [request.user.id]
        my_friends = []

   # 3. Obtener POSTS
    try:
        posts = Post.objects.filter(
            Q(user__in=users_to_show) | Q(visibility='public') 
        ).select_related(
            'user', 'user__profile'
        ).prefetch_related(
            'pictures', 'likes', 'saved_by', 'comments'
        ).distinct()
    except Exception:
        posts = []

    # 4. Obtener ITINERARIOS
    itineraries = Itinerary.objects.filter(
         user_id__in=users_to_show 
    ).select_related('user')

    # 5. Etiquetar tipos
    for post in posts:
        post.feed_type = 'post'
    for itinerary in itineraries:
        itinerary.feed_type = 'itinerary'

    # 6. Fusionar y Ordenar
    feed_items = sorted(
        chain(posts, itineraries),
        key=attrgetter('created_at'),
        reverse=True
    )

    # 7. Lógica de Amigos / Online
    users_list = User.objects.exclude(id=request.user.id)
    time_threshold = timezone.now() - timedelta(minutes=15)
    online_friends = []
    for friend in my_friends:
        if friend.last_login and friend.last_login > time_threshold:
            online_friends.append(friend)

    users_with_status = []
    for user in users_list:
        status_data = {'user': user, 'status': None, 'request_id': None}
        if user in my_friends:
            status_data['status'] = 'FRIENDS'
        else:
            sent = FriendshipRequest.objects.filter(from_user=request.user, to_user=user, rejected__isnull=True).first()
            if sent:
                status_data['status'] = 'PENDING_SENT'
                status_data['request_id'] = sent.id
            else:
                recv = FriendshipRequest.objects.filter(from_user=user, to_user=request.user, rejected__isnull=True).first()
                if recv:
                    status_data['status'] = 'PENDING_RECEIVED'
                    status_data['request_id'] = recv.id
        users_with_status.append(status_data)

    context = {
        'feed_items': feed_items,      
        'users_with_status': users_with_status,
        'online_friends': online_friends,
        'create_post_form': create_post_form,
    }
    return render(request, 'feed/home_feed.html', context)


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
=======
        return redirect('home')  

def account_suspended_view(request):
    """Muestra la página informativa de cuenta suspendida."""
    return render(request, 'users/account_suspended.html')

# --- ¡AQUÍ COMIENZA LA NUEVA LÓGICA DEL PANEL ADMIN! ---

@staff_member_required(login_url='simple_login') # Protege la vista: solo Staff puede entrar
def admin_users_view(request):
    """
    Vista personalizada para gestionar usuarios con el diseño de admin-permisos.html.
    Muestra una lista paginada de usuarios, con búsqueda y filtros.
    """
    # 1. Obtener todos los usuarios (ordenados por fecha de registro descendente)
    users_list = User.objects.all().order_by('-date_joined')

    # 2. Filtro de Búsqueda (por username, email, nombre o apellido)
    query = request.GET.get('q')
    if query:
        users_list = users_list.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    # 3. Filtro "Ver solo suspendidos"
    # El checkbox del HTML envía 'on' si está marcado
    show_suspended = request.GET.get('suspendidos') == 'on'
    if show_suspended:
        users_list = users_list.filter(is_active=False)

    # 4. Paginación (10 usuarios por página)
    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'users': page_obj,           # Objeto de página (contiene la lista y metadatos)
        'search_query': query or '', # Para mantener el texto en el buscador
        'show_suspended': show_suspended # Para mantener el estado del switch
    }
    
    # Renderiza la plantilla personalizada que crearemos/adaptaremos
    return render(request, 'admin_custom/users.html', context)

@staff_member_required(login_url='simple_login')
@require_POST # Solo acepta peticiones POST por seguridad
def admin_toggle_user_status(request, user_id):
    """
    Acción para Suspender (Desactivar) o Reactivar un usuario.
    Equivalente a la acción personalizada que hicimos en admin.py,
    pero para usar desde la interfaz web personalizada.
    """
    try:
        user = User.objects.get(pk=user_id)
        
        # Protección: No permitir que un admin se suspenda a sí mismo por accidente
        if user == request.user:
            messages.error(request, "No puedes suspender tu propia cuenta.")
            return redirect('admin_users')
        # Si el usuario objetivo es Staff Y yo NO soy Superuser -> ERRORs
        if user.is_staff and not request.user.is_superuser:
            messages.error(request, "No tienes permisos para suspender a otro Administrador.")
            return redirect('admin_users')
            # Invierte el estado actual:
            # Si is_active es True (Activo) -> Pasa a False (Suspendido)
            # Si is_active es False (Suspendido) -> Pasa a True (Activo)
        user.is_active = not user.is_active
        user.save()
            
        estado = "reactivado" if user.is_active else "suspendido"

        try:
            # Caso 1: Acabamos de SUSPENDER (is_active ahora es False)
            if not user.is_active: 
                asunto = 'Notificación de Suspensión de Cuenta - MexTur'
                template = 'account/email/account_suspended.html'
                
            # Caso 2: Acabamos de REACTIVAR (is_active ahora es True)
            else: 
                asunto = 'Cuenta Reactivada - MexTur'
                template = 'account/email/account_reactivated.html' # <--- Usamos la nueva plantilla

            # Renderizamos el HTML (funciona para ambos casos)
            html_message = render_to_string(template, {
                'username': user.username
            })
                
            # Obtenemos el plaintext automáticamente del HTML
            plain_message = strip_tags(html_message)

            # Enviamos el correo
            send_mail(
                asunto,
                plain_message,
                settings.EMAIL_HOST_USER,
                [user.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error enviando correo: {e}")
            # -----------------------------
            # Mensaje flash de éxito
        messages.success(request, f"El usuario {user.username} ha sido {estado} exitosamente.")
            
    except User.DoesNotExist:
        messages.error(request, "El usuario que intentas modificar no existe.")
    
    # Redirige de vuelta a la lista de usuarios (admin_users_view)
    return redirect('admin_users')

@staff_member_required(login_url='simple_login')
@require_POST 
def delete_user(request, user_id):
    # 1. Obtener el usuario o dar error 404 si no existe
    usuario_a_eliminar = get_object_or_404(User, id=user_id)

    # 2. VALIDACIÓN: Evitar que el admin se borre a sí mismo
    if usuario_a_eliminar == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta mientras tienes la sesión iniciada.")
        return redirect('admin_users') # Cambia esto por el 'name' de tu URL de la tabla

    # 3. VALIDACIÓN: Evitar borrar superusuarios si no eres superusuario (Opcional)
    if (usuario_a_eliminar.is_staff or usuario_a_eliminar.is_superuser) and not request.user.is_superuser:
        messages.error(request, "Solo los Superusuarios pueden eliminar a miembros Administradores.")
        return redirect('admin_users')

    # 4. Guardar nombre para el mensaje y ELIMINAR
    email_destino = usuario_a_eliminar.email 
    nombre_usuario = usuario_a_eliminar.username
    usuario_a_eliminar.delete()
    # --- ENVIAR CORREO HTML ---
    asunto = 'Aviso de eliminación de cuenta - MexTur'
    try:
        # Asegúrate de que la ruta coincida con tu carpeta real: 'account/email/...'
        html_message = render_to_string('account/email/account_deleted.html', {
            'username': nombre_usuario # <--- CORREGIDO: Usamos la variable que guardamos arriba
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            asunto,
            plain_message,
            settings.EMAIL_HOST_USER,
            [email_destino], # <--- CORREGIDO: Ahora esta variable sí existe
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error enviando correo: {e}")

    # 7. Mensaje de éxito y redirección
    messages.success(request, f"El usuario '{nombre_usuario}' ha sido eliminado permanentemente.")
    return redirect('admin_users')
    
@staff_member_required(login_url='simple_login')
def admin_user_detail_view(request, user_id):
    # 1. Obtenemos el usuario objetivo
    target_user = get_object_or_404(User, id=user_id)
    
    # 2. Intentamos obtener su perfil (si existe)
    # Usamos getattr para evitar errores si por alguna razón no tiene perfil creado
    profile = getattr(target_user, 'profile', None)

    context = {
        'target_user': target_user,
        'profile': profile
    }
    return render(request, 'users/admin_user_profile.html', context)    

@login_required
@staff_member_required(login_url='simple_login')
def admin_login_logs(request):
    # 1. Obtener todos los logs (más recientes primero)
    logs_list = LoginLog.objects.all().order_by('-timestamp')

    # 2. Filtros (Opcional: Búsqueda por usuario o IP)
    query = request.GET.get('q')
    if query:
        logs_list = logs_list.filter(
            Q(username_attempt__icontains=query) | 
            Q(ip_address__icontains=query)
        )

    # 3. Paginación (20 registros por página)
    paginator = Paginator(logs_list, 20)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    return render(request, 'users/admin-login-logs.html', {'logs': logs})
>>>>>>> origin/feature/email-verification
