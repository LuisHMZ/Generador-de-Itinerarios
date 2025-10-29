# apps/users/adapters.py

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account import app_settings
from allauth.account.models import EmailConfirmation, EmailAddress
from allauth.account.utils import user_email
# Importa la función para obtener el sitio actual
from django.contrib.sites.shortcuts import get_current_site

class CustomAccountAdapter(DefaultAccountAdapter):

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Sobrescribe el método original para CORREGIR el AttributeError
        que ocurría al intentar acceder al usuario desde emailconfirmation.
        """
        current_site = get_current_site(request)
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)

        # ---- ¡LA LÍNEA CORREGIDA! ----
        # El objeto 'emailconfirmation' tiene una relación ForeignKey llamada 'email_address'
        # al objeto EmailAddress. Accedemos al usuario a través de esa relación.
        ctx = {
            "user": emailconfirmation.email_address.user, # Acceso correcto al usuario
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
            "email": emailconfirmation.email_address.email, # Obtenemos el email desde el objeto EmailAddress
        }
        # -----------------------------

        if signup:
            email_template = "account/email/email_confirmation_signup"
        else:
            email_template = "account/email/email_confirmation"

        # El método send_mail heredado se encarga del envío real
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)
