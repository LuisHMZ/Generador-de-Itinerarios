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
from allauth.socialaccount.models import SocialAccount    
import traceback # Para depurar errores
from django.core.files.base import ContentFile
import requests

from django.contrib.auth.signals import user_logged_in, user_login_failed
from .models import LoginLog
from django.db.models import Q

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
    
    # =======================================================
    # 1. LOGICA DE DATOS SOCIALES (Google/Facebook)
    # =======================================================
    # allauth pasa el objeto 'sociallogin' en kwargs si es un registro social
    sociallogin = kwargs.get('sociallogin')
    
    if sociallogin:
        print(f"SIGNAL: Registro vía proveedor social: {sociallogin.account.provider}")
        
        # Intentamos obtener o crear el perfil (por si acaso no existe)
        profile, created = Profile.objects.get_or_create(user=user)
        
        if sociallogin.account.provider == 'google':
            # Google devuelve los datos en 'extra_data'
            data = sociallogin.account.extra_data
            print(f"DEBUG GOOGLE DATA: {data.keys()}") # Para que veas qué datos te llegan en la consola
            
            # Google suele enviar: 'given_name', 'family_name', 'picture', 'email', 'name'
            
            # 1. Guardar Foto de Perfil (Si no tiene una ya)
            picture_url = data.get('picture')
            if picture_url and not profile.profile_picture:
                try:
                    # Opcional: Descargar y guardar la imagen localmente
                    # O simplemente guardar la URL si tu campo fuera CharField (pero es ImageField)
                    print(f"SIGNAL: Intentando descargar foto de: {picture_url}")
                    response = requests.get(picture_url)
                    if response.status_code == 200:
                        # Guardamos el archivo en el campo ImageField
                        profile.profile_picture.save(f"google_avatar_{user.id}.jpg", ContentFile(response.content), save=True)
                        print("SIGNAL: Foto de Google guardada en el perfil.")
                except Exception as e:
                    print(f"SIGNAL ERROR: No se pudo guardar la foto de Google: {e}")

            # 2. Bio (Podemos poner algo por defecto o dejarlo vacío)
            if not profile.bio:
                profile.bio = f"¡Hola! Soy nuevo en MexTur."
            
            # 3. Fecha de Nacimiento
            # Como Google no la manda, la dejamos tal cual (NULL).
            # El usuario tendrá que llenarla manualmente en su perfil.
            
            profile.save()
    
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

    
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    LoginLog.objects.create(
        user=user,
        username_attempt=user.username,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        status='success'
    )

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    username_ingresado = credentials.get('username', 'Desconocido')
    
    usuario_encontrado = User.objects.filter(
        Q(username=username_ingresado) | Q(email=username_ingresado)
    ).first()
    
    LoginLog.objects.create(
        user=usuario_encontrado, # Ahora sí encontrará al usuario si usó su email
        username_attempt=username_ingresado,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        status='failed'
    )