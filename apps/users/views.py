# apps/users/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from .forms import SimpleSignupForm
from .models import Profile # Importa tu modelo Profile
# Importa el formulario de autenticación de Django y las funciones de login/logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.utils import timezone

from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.adapter import get_adapter
from allauth.account.signals import user_signed_up # <-- ¡AÑADE ESTA!
from django.contrib.auth import get_user_model # Necesario para el sender
User = get_user_model()

import json # Necesario si decidieras enviar JSON desde JS en el futuro
import traceback

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

# Vista para inicio de sesión simple (Solo Django Auth, AllAuth aun no implementada)
def simple_login_view(request):
    if request.user.is_authenticated:
        # Detectar si es una petición AJAX/Fetch (usa la cabecera X-Requested-With)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({'status': 'already_authenticated', 'message': 'Ya has iniciado sesión.'})
        else:
            return redirect('simple_register')  # Aún no tenemos home, se redirige al registro
    
    # Manejo del formulario de login aquí
    if request.method == 'POST':
        # Detecta si es una petición AJAX/Fetch (busca la cabecera X-Requested-With)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        # Usa el autenticador de Django
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            # Obtiene el usuario validado
            user = form.get_user()
            email_record = EmailAddress.objects.filter(user=user, email=user.email).first()
            if not email_record or not email_record.verified:
                return JsonResponse({
                'status': 'error',
                'message': 'Debes verificar tu correo antes de iniciar sesión.'
            }, status=403)
            # Inicia la sesión del usuario
            auth_login(request, user)

            # Responde según si es fetch o no
            if is_ajax:
                # Si es AJAX, devuelve JSON de éxito y redirige
                # ANTES SE TENÍA:
                # redirect_url = request.session.get('next', '/')  # Intenta obtener la URL previa o usa '/'
                # VERSIÓN MODIFICADA
                # Obtenemos la URL a la que redirigir si el usuario vino de otra página,
                # y si no, usamos reverse() para obtener la URL real de 'home'
                redirect_url = request.session.get('next', reverse('home'))
                return JsonResponse({'status': 'success', 'message': '¡Inicio de sesión exitoso!', 'redirect_url': redirect_url})
            else:
                # Si no es AJAX, redirige a la página principal u otra página adecuada
                return redirect('home')
        else:
            # Si el formulario no es válido
            if is_ajax:
                # Devuelve los errores como JSON, con estado 400
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
                # El return render al final manejará mostrar el form con errores
    
    else: # Si es una petición GET (mostrar el formulario)
        form = AuthenticationForm()

    # Renderiza la plantilla para GET o para POST fallido (no AJAX)
    return render(request, 'users/simple_login.html', {'form': form})

# Vista para cerrar sesión
def simple_logout_view(request):
    """
    Cierra la sesión del usuario actual.
    """
    # Detectar si es una petición AJAX/Fetch (usa la cabecera X-Requested-With)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    auth_logout(request)
    if is_ajax:
        return JsonResponse({'status': 'success', 'message': 'Sesión cerrada.'})
    else:
        return redirect('home')  
