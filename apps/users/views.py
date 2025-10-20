# apps/users/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .forms import SimpleSignupForm
from .models import Profile # Importa tu modelo Profile
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