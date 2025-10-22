# apps/reports/models.py

"""
Modelo Report: representa reportes que usuarios (o anónimos) crean sobre
distintos objetos de la aplicación (usuario, publicación, comentario,
reseña, itinerario). Usa GenericForeignKey para poder apuntar a varios
modelos objetivo sin acoplar el modelo Report a uno solo.
"""

# Importaciones principales:
# - models: para definir campos y opciones de Django ORM.
# - User: modelo de usuario de Django, usado como el reportero.
# - ContentType / GenericForeignKey: para la relación genérica a objetos.
# - ValidationError: para señales de validación en clean().
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError

class Report(models.Model):
    # Enum para los tipos de contenido permitidos.
    # Sirve como referencia y como lista de valores aceptables en la validación.
    class ContentTypeChoices(models.TextChoices):
        USER = 'user', 'Usuario'
        POST = 'post', 'Publicación'
        COMMENT = 'comment', 'Comentario'
        REVIEW = 'review', 'Reseña'
        ITINERARY = 'itinerary', 'Itinerario'
    
    # Enum para el estado del reporte en el flujo de moderación.
    # Provee etiquetas legibles (por ejemplo get_status_display()).
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente de Revisión'
        REVIEWED = 'REVIEWED', 'Revisado' 
        DISMISSED = 'DISMISSED', 'Desestimado'

    # Usuario que envía el reporte. Usamos SET_NULL para no eliminar
    # reportes si el usuario original se borra, y null=True para permitir
    # reportes anónimos.
    reporter = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_reports"
    ) 

    # Motivo/Descripción del reporte.
    reason = models.TextField(
        help_text="Motivo del reporte.",
        default=""
    )

    # Fecha de creación: establecida automáticamente al crear el objeto.
    created_at = models.DateTimeField(auto_now_add=True) 
    
    # Estado del reporte en el flujo interno (pendiente, revisado, desestimado).
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Relación genérica: identifica el objeto objetivo del reporte.
    # ContentType identifica el modelo; object_id es la PK del objeto en
    # ese modelo; content_object resuelve la instancia concreta.
    # Nota: esta flexibilidad sacrifica integridad referencial a nivel de BD.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE) 
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def clean(self):
        """
        Validación personalizada que asegura que el ContentType del reporte
        corresponda a uno de los tipos lógicos definidos en
        `ContentTypeChoices`.

        Esto evita que, por error o manipulación, se creen reportes apuntando
        a modelos que la aplicación no espera manejar.
        """
        allowed_models = {choice.value for choice in self.ContentTypeChoices}
        # content_type.model devuelve el nombre del modelo en minúsculas
        model_name = self.content_type.model if self.content_type else None
        if model_name and model_name not in allowed_models:
            # Asociamos el error al campo `content_type` para mejorar el
            # feedback en formularios y APIs.
            raise ValidationError({'content_type': f"Tipo de contenido no permitido: {model_name}. Tipos permitidos: {', '.join(sorted(allowed_models))}."})

    def save(self, *args, **kwargs):
        # Llamamos full_clean() para ejecutar validaciones (incluyendo
        # clean()) antes de persistir. Esto ayuda a detectar errores en
        # cualquier punto que intente guardar el modelo.
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        # Representación legible para admin/logs. Usamos get_status_display()
        # para mostrar la etiqueta legible del estado.
        reporter_name = self.reporter.username if self.reporter else "Anónimo"
        return f"Reporte de {reporter_name} sobre {self.content_object} ({self.get_status_display()})"

    class Meta:
        # Orden por defecto: más recientes primero.
        ordering = ['-created_at']
        # Índice compuesto útil para buscar reportes por objeto objetivo.
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]