# apps/users/middleware.py

from .models import Profile
from django.utils import timezone
from django.contrib.auth import get_user_model

class ActiveUserMiddleware: #ActivateUserUpdateMiddleware #class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Actualizamos la hora de 'last_login' ahora mismo
            # Usamos .update() directo en la DB para que sea rápido y no dispare señales
            get_user_model().objects.filter(pk=request.user.pk).update(last_login=timezone.now())
            
            # Si el usuario está autenticado, actualizamos su última vez visto
            # Usamos update() directamente para ser más eficientes y no traer todo el objeto
            Profile.objects.filter(user=request.user).update(last_seen=timezone.now())
        return response