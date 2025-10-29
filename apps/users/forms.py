# apps/users/forms.py

from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.models import User
import re

class SimpleSignupForm(BaseUserCreationForm):
    # Añade los campos que UserCreationForm no tiene por defecto
    first_name = forms.CharField(max_length=30, required=True, label='Nombre(s)')
    last_name = forms.CharField(max_length=150, required=True, label='Apellidos')
    email = forms.EmailField(max_length=254, required=True, help_text='Obligatorio.')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Fecha de Nacimiento', required=False)
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