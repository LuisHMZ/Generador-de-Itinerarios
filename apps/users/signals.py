from django.contrib.auth.models import User
from django.db.models.signals import post_save
from .models import Profile # Importa Profile desde models.py AQUI
from django.dispatch import receiver
from django.conf import settings # Para verificar la configuración
    
# Importa la señal específica de allauth
from allauth.account.signals import user_signed_up
# Importa las herramientas de allauth para enviar el correo
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.account import app_settings as allauth_settings # Para verificar config
    
import traceback # Para depurar errores

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def save_user_profile(sender, instance, **kwargs):
    # Usamos get_or_create para más seguridad
    profile, created = Profile.objects.get_or_create(user=instance)
    if not created:
        # Solo intenta guardar si ya existía, evita doble guardado al crear
        profile.save()


# El decorador @receiver conecta esta función a la señal
@receiver(user_signed_up)
def handle_user_signup(sender, request, user, **kwargs):
    print("*"*10 + f" DEBUG: SEÑAL user_signed_up RECIBIDA para usuario: {user.username} ({user.email}) " + "*"*10)
    # Verifica si la verificación por email está activada en settings
    if (allauth_settings.EMAIL_VERIFICATION == allauth_settings.EmailVerificationMethod.MANDATORY or
        allauth_settings.EMAIL_VERIFICATION == allauth_settings.EmailVerificationMethod.OPTIONAL):

        print(f"SIGNAL: Usuario {user.username} registrado. Intentando enviar correo de verificación...") # Log

        email_sent = False
        try:
            # Obtenemos o creamos el EmailAddress (allauth podría ya haberlo creado)
            email_address, created = EmailAddress.objects.get_or_create(
                user=user,
                email=user.email,
                defaults={'primary': True, 'verified': False}
            )

            # Si el email ya estaba verificado por alguna razón, no enviamos
            if email_address.verified:
                print(f"SIGNAL: Email {user.email} ya estaba verificado. No se envía correo.")
                return # Salimos de la función
            print(f"SIGNAL: Llamando a get_adapter().send_confirmation_mail con EmailAddress ID: {email_address.id}...")
            from allauth.account.models import EmailConfirmation # Import local
            confirmation = EmailConfirmation.create(email_address)
            if not confirmation or not confirmation.key:
                raise ValueError("Fallo al crear EmailConfirmation o clave vacía ANTES de send_confirmation_mail")
            print(f"SIGNAL: EmailConfirmation creado con Key: '{confirmation.key}'. Pasando al adaptador...")
            # Usamos el adaptador para enviar el correo (la forma correcta)
            # Pasamos signup=True para el flujo correcto
            print(f"SIGNAL: Llamando a get_adapter().send_confirmation_mail...")
            # get_adapter(request).send_confirmation_mail(request, email_address, signup=True) # <-- INCORRECTO
            get_adapter(request).send_confirmation_mail(request, confirmation, signup=True) # <-- CORRECTO
            email_sent = True
            print(f"SIGNAL: Correo de confirmación enviado exitosamente a {user.email}")
        except ValueError as ve: # Captura nuestro error de clave vacía
            print(f"SIGNAL ERROR (ValueError): {ve}")
        except Exception as e:
            print(f"SIGNAL ERROR GENERAL: Error en handle_user_signup para {user.email}: {e}")
            traceback.print_exc()
    else:
        print(f"SIGNAL: Verificación de email NO está activa ({allauth_settings.EMAIL_VERIFICATION}). No se envía correo.")
        