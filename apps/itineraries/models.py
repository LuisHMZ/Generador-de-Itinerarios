from django.db import models
from django.contrib.auth.models import User

# --- Modelos de la App `itineraries` ---

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

class TouristicPlace(models.Model):
    external_api_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    external_api_rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    website = models.URLField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    opening_hours = models.TextField(blank=True)
    photo = models.ImageField(upload_to='place_photos/', null=True, blank=True, help_text="Imagen representativa del lugar turístico.")
    # La tabla intermedia Place_Category se crea con esta relación
    categories = models.ManyToManyField(Category, related_name="places")


    def __str__(self):
        return self.name

class Itinerary(models.Model):

    # Opciones de status (Draft)
    STATUS_CHOICES = [
        ('draft', 'Borrador'),       # El usuario está creando
        ('published', 'Publicado'),   # El usuario terminó y guardó
        # ('archived', 'Archivado'), # Opcional a futuro
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True) # Corregido para no tener dos descripciones
    banner_pic = models.ImageField(upload_to='itinerary_banners/', null=True, blank=True)
    # Campos adicionales para creación/edición desde la UI
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=50, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    # Status (Draft)
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft'  # ¡Importante!
    )

    def __str__(self):
        return self.title

class ItineraryStop(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)
    touristic_place = models.ForeignKey(TouristicPlace, on_delete=models.CASCADE)
    day_number = models.PositiveSmallIntegerField()
    placement = models.PositiveSmallIntegerField() # El orden dentro del día

    class Meta:
        unique_together = ('itinerary', 'day_number', 'placement')
        ordering = ['day_number', 'placement'] # Para que siempre se muestren en orden

    def __str__(self):
        return f'Parada en {self.touristic_place.name} para {self.itinerary.title}'

class Review(models.Model):
    touristic_place = models.ForeignKey(TouristicPlace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
