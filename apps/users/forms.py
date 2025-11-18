# apps/users/forms.py

from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.models import User
import re
from allauth.account.models import EmailAddress
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
class SimpleSignupForm(BaseUserCreationForm):
    # Añade los campos que UserCreationForm no tiene por defecto
    first_name = forms.CharField(max_length=30, required=True, label='Nombre(s)')
    last_name = forms.CharField(max_length=150, required=True, label='Apellidos')
    email = forms.EmailField(max_length=254, required=True, help_text='Obligatorio.')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Fecha de Nacimiento', required=False)
    consent = forms.BooleanField(
        required=True, # ¡Esta es la validación de seguridad!
        label="Sí, acepto los términos y condiciones y la política de privacidad.",
        error_messages={
            'required': 'Debes aceptar los términos y condiciones para registrarte.'
        }
    )
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-callback': 'onRecaptchaSuccess',       # Llama a esta función JS en éxito
                'data-expired-callback': 'onRecaptchaExpired'  # Llama a esta en expiración
            }
        ),
        label="" # Ocultamos la etiqueta por defecto, el widget es suficiente
    )
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        # Permite letras (incluyendo acentos), espacios y apóstrofes/guiones comunes en nombres
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]+$", first_name):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return first_name

    # --- VALIDACIÓN PERSONALIZADA PARA APELLIDO ---
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]+$", last_name):
            raise forms.ValidationError("El apellido solo puede contener letras y espacios.")
        return last_name
    class Meta(BaseUserCreationForm.Meta):
        model = User
        # Añade los campos extra a los que ya maneja UserCreationForm (username, password1, password2)
        fields = BaseUserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'birth_date')

    def clean_email(self):
        """
        Valida que el correo electrónico no esté ya en uso por otra cuenta,
        comprobando tanto el modelo User como el modelo EmailAddress de allauth.
        """
        email = self.cleaned_data.get('email')
        if not email:
            return email # El validador 'required' se encargará
        
        email = email.lower() # Normalizar a minúsculas
        
        # 1. Comprueba si el email ya existe en la tabla User
        #    (para usuarios creados por admin o flujos antiguos)
        if User.objects.filter(email__iexact=email).exists():
             raise forms.ValidationError("Ya existe una cuenta con esta dirección de correo electrónico.")
             
        # 2. Comprueba si el email ya existe en la tabla EmailAddress de allauth
        #    (para usuarios de login social o que ya han verificado)
        if EmailAddress.objects.filter(email__iexact=email, verified=True).exists():
             raise forms.ValidationError("Ya existe una cuenta verificada con esta dirección de correo electrónico.")

        # ¡Pasa la validación! Devuelve el email limpio.
        return email
    # -----------------------------------------------

    def signup(self, request, user):
        """
        Método requerido por django-allauth cuando se usa un formulario de signup personalizado.
        Guarda los campos adicionales en el User y crea/actualiza el Profile con birth_date.
        """
        # Guardar campos del User
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        user.save()

        # Guardar/crear el Profile y la birth_date si está presente
        try:
            from .models import Profile
        except Exception:
            Profile = None

        birth_date = self.cleaned_data.get('birth_date')
        if Profile is not None:
            profile, created = Profile.objects.get_or_create(user=user)
            if birth_date:
                profile.birth_date = birth_date
            profile.save()

        return user