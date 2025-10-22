# apps/reports/models.py

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError

class Report(models.Model):
    # Enum para los tipos de contenido (ya lo tenías)
    class ContentTypeChoices(models.TextChoices):
        USER = 'user', 'Usuario'
        POST = 'post', 'Publicación'
        COMMENT = 'comment', 'Comentario'
        REVIEW = 'review', 'Reseña'
        ITINERARY = 'itinerary', 'Itinerario'
    
    # Enum para el estado del reporte (¡Este faltaba!)
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente de Revisión'
        REVIEWED = 'REVIEWED', 'Revisado' 
        DISMISSED = 'DISMISSED', 'Desestimado'

    # Cambié 'user' a 'reporter' para más claridad
    reporter = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, # Mejor que CASCADE para reportes
        null=True,                 # Permite reportes anónimos o si el user se borra
        related_name="sent_reports"
    ) 
    # Cambié 'description' a 'reason'
    reason = models.TextField(help_text="Motivo del reporte.") 
    # Cambié 'creation_date' a 'created_at' por consistencia
    created_at = models.DateTimeField(auto_now_add=True) 
    
    # --- ¡EL CAMPO QUE FALTABA! ---
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING # Valor por defecto para nuevos reportes y existentes
    )
    
    # --- Relación Genérica (ya la tenías, pero quité content_type_model) ---
    # content_type_model = models.CharField(max_length=20, choices=ContentTypeChoices.choices) <-- Redundante
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE) 
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def clean(self):
        """
        Valida que el content_type esté entre los tipos permitidos por ContentTypeChoices.
        Esto previene que se creen Report objetos apuntando a modelos no deseados.
        """
        allowed_models = {choice.value for choice in self.ContentTypeChoices}
        # content_type.model devuelve el nombre del modelo en minúsculas
        model_name = self.content_type.model if self.content_type else None
        if model_name and model_name not in allowed_models:
            raise ValidationError({'content_type': f"Tipo de contenido no permitido: {model_name}. Tipos permitidos: {', '.join(sorted(allowed_models))}."})

    def save(self, *args, **kwargs):
        # Forzar validación antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        # Actualizado para incluir el status legible
        reporter_name = self.reporter.username if self.reporter else "Anónimo"
        return f"Reporte de {reporter_name} sobre {self.content_object} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]