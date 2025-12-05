# apps/users/middleware.py

from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Profile


class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Actualizamos 'last_login' eficientemente en el modelo User
            get_user_model().objects.filter(pk=request.user.pk).update(last_login=timezone.now())

            # Actualizamos 'last_seen' eficientemente en el Profile
            Profile.objects.filter(user=request.user).update(last_seen=timezone.now())

        return response