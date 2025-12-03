from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

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
    categories = models.ManyToManyField(Category, related_name="places")

    def __str__(self):
        return self.name

class Itinerary(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('published', 'Publicado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True) 
    banner_pic = models.ImageField(upload_to='itinerary_banners/', null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft'
    )

    # Likes y Guardados
    likes = models.ManyToManyField(User, related_name='liked_itineraries', blank=True)
    saved_by = models.ManyToManyField(User, related_name='saved_itineraries', blank=True)

    # --- NUEVO CAMPO: PRIVACIDAD (Audiencia) ---
    PRIVACY_CHOICES = [
        ('public', 'Público'),       # Visible para todos en el Feed
        ('friends', 'Solo Amigos'),  # Visible solo para seguidores/amigos
        ('private', 'Solo Yo'),      # Oculto (como un archivo personal)
    ]
    privacy = models.CharField(
        max_length=10, 
        choices=PRIVACY_CHOICES, 
        default='public' # O 'private', según tu preferencia
    )

    def total_likes(self):
        return self.likes.count()

    def get_average_rating(self):
        reviews = self.itinerary_reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    def __str__(self):
        return self.title

class ItineraryStop(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)
    touristic_place = models.ForeignKey(TouristicPlace, on_delete=models.CASCADE)
    day_number = models.PositiveSmallIntegerField()
    placement = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('itinerary', 'day_number', 'placement')
        ordering = ['day_number', 'placement']

    def __str__(self):
        return f'Parada en {self.touristic_place.name} para {self.itinerary.title}'

# --- MODELOS DE INTERACCIÓN ---

class ItineraryComment(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # --- NUEVO CAMPO PARA RESPUESTAS ---
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    # -----------------------------------

    def __str__(self):
        return f'Comentario de {self.user.username} en {self.itinerary.title}'

class ItineraryReview(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='itinerary_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Calificación de 1 a 5 estrellas"
    )
    comment = models.TextField(blank=True, help_text="Opinión escrita (opcional)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('itinerary', 'user')

    def __str__(self):
        return f'{self.rating}★ de {self.user.username} a {self.itinerary.title}'

class Review(models.Model):
    touristic_place = models.ForeignKey(TouristicPlace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)