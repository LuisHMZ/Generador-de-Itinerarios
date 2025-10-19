from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# --- Modelos de la App `reports` ---

class Report(models.Model):
    class ContentTypeChoices(models.TextChoices):
        USER = 'user', 'Usuario'
        POST = 'post', 'Publicación'
        COMMENT = 'comment', 'Comentario'
        REVIEW = 'review', 'Reseña'
        ITINERARY = 'itinerary', 'Itinerario'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE) # El que reporta
    description = models.TextField()
    creation_date = models.DateTimeField(auto_now_add=True)
    
    # --- Relación Genérica para apuntar a cualquier modelo ---
    content_type_model = models.CharField(max_length=20, choices=ContentTypeChoices.choices)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')