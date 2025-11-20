from django.db import models
from django.contrib.auth import get_user_model
from apps.itineraries.models import Itinerary

# Obtenemos el modelo de usuario una sola vez
User = get_user_model()

# --- Modelos de la App `posts` ---

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100, blank=True)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # --- ▼▼▼ CAMPOS NUEVOS (Integrados aquí) ▼▼▼ ---
    # Guarda quiénes le dieron like
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    
    # Guarda quiénes guardaron la publicación
    saved_by = models.ManyToManyField(User, related_name='saved_posts', blank=True)
    # --- ▲▲▲ FIN DE CAMPOS NUEVOS ▲▲▲ ---

    def __str__(self):
        return f'Post de {self.user.username} - {self.title}'

class PostPicture(models.Model):
    # 'Post' ya está definido arriba, así que esto funcionará bien
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='pictures')
    pic_url = models.ImageField(upload_to='post_pics/')

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Para respuestas (hilos): Un comentario puede tener un "padre"
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    
    # Para likes en comentarios
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    def __str__(self):
        return f'Comentario de {self.user.username}'

class CommentPicture(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='pictures')
    url = models.ImageField(upload_to='comment_pics/')