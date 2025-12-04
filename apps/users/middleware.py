from django.utils import timezone
from .models import Profile

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Si el usuario está autenticado, actualizamos su última vez visto
        if request.user.is_authenticated:
            # Usamos update() directamente para ser más eficientes y no traer todo el objeto
            Profile.objects.filter(user=request.user).update(last_seen=timezone.now())

        return response