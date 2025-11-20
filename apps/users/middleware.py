# apps/users/middleware.py

from django.utils import timezone
from django.contrib.auth import get_user_model

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            # Actualizamos la hora de 'last_login' ahora mismo
            # Usamos .update() directo en la DB para que sea rápido y no dispare señales
            get_user_model().objects.filter(pk=request.user.pk).update(last_login=timezone.now())
            
        return response