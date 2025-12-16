from django.db import models
from django.contrib.auth import get_user_model
from apps.itineraries.models import Itinerary

User = get_user_model()

# --- Modelos de la App `posts` ---

class Post(models.Model):
    VISIBILITY_CHOICES = (
        ('public', 'Público'),
        ('friends', 'Solo Amigos'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100, blank=True)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    visibility = models.CharField(
        max_length=10, 
        choices=VISIBILITY_CHOICES, 
        default='public',
        help_text="Define quién puede ver esta publicación"
    )
    # --- NUEVO CAMPO ---
    is_active = models.BooleanField(default=True, help_text="Desactívalo para ocultar el post (Moderación)")
    # -------------------
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    saved_by = models.ManyToManyField(User, related_name='saved_posts', blank=True)

    def __str__(self):
        return f'Post de {self.user.username} - {self.title}'

class PostPicture(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='pictures')
    pic_url = models.ImageField(upload_to='post_pics/')

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    
    # --- ARREGLO DEL ERROR ---
    # Cambiamos related_name='comments' a 'feed_comments' para evitar choque
    itinerary = models.ForeignKey(
        Itinerary, 
        on_delete=models.CASCADE, 
        related_name='feed_comments', 
        null=True, 
        blank=True
    )
    # -------------------------

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    def __str__(self):
        return f'Comentario de {self.user.username}'

    def save(self, *args, **kwargs):
        if not self.post and not self.itinerary:
            raise ValueError("El comentario debe estar vinculado a un Post o a un Itinerario.")
        super().save(*args, **kwargs)

class CommentPicture(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='pictures')
    url = models.ImageField(upload_to='comment_pics/')


# --- NUEVOS MODELOS PARA NO TOCAR LA APP DE ITINERARIOS ---

class SavedItinerary(models.Model):
    """Modelo para guardar itinerarios sin modificar la app original"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itinerary_saves')
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='saves_from_feed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'itinerary') # Un usuario no guarda el mismo itinerario 2 veces

class ItineraryRating(models.Model):
    """Modelo para calificar itinerarios (Estrellas)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itinerary_ratings')
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='feed_ratings')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)]) # 1 a 5 estrellas
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'itinerary') # Solo una calificación por usuario