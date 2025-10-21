# apps/users/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .forms import SimpleSignupForm
from .models import Profile # Importa tu modelo Profile
# Importa el formulario de autenticación de Django y las funciones de login/logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout

import json # Necesario si decidieras enviar JSON desde JS en el futuro

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

# Vista para inicio de sesión simple (Solo Django Auth, AllAuth aun no implementada)
def simple_login_view(request):
    if request.user.is_authenticated:
        # Detectar si es una petición AJAX/Fetch (usa la cabecera X-Requested-With)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({'status': 'already_authenticated', 'message': 'Ya has iniciado sesión.'})
        else:
            return redirect('home')  # Redirige a la página principal u otra página adecuada
    
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
                # Si es AJAX, devuelve JSON de éxito y redirige
                redirect_url = request.session.get('next', '/')  # Intenta obtener la URL previa o usa '/'
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
    # Detectar si es una petición AJAX/Fetch (usa la cabecera X-Requested-With)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    auth_logout(request)
    if is_ajax:
        return JsonResponse({'status': 'success', 'message': 'Sesión cerrada.'})
    else:
        return redirect('/')  # Redirige a la página principal u otra página adecuada
