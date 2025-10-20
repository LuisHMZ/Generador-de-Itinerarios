# apps/users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SimpleSignupForm(UserCreationForm):
    # Añade los campos que UserCreationForm no tiene por defecto
    first_name = forms.CharField(max_length=30, required=True, label='Nombre(s)')
    last_name = forms.CharField(max_length=150, required=True, label='Apellidos')
    email = forms.EmailField(max_length=254, required=True, help_text='Obligatorio.')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Fecha de Nacimiento', required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        # Añade los campos extra a los que ya maneja UserCreationForm (username, password1, password2)
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'birth_date')

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