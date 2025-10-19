from django.db import models
from django.contrib.auth.models import User
from apps.itineraries.models import Itinerary # Importa el modelo de la otra app

# --- Modelos de la App `posts` ---

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100, blank=True)
    text = models.TextField(blank=True) # Un post puede ser solo una foto
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Post de {self.user.username} - {self.title}'

class PostPicture(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='pictures')
    pic_url = models.ImageField(upload_to='post_pics/')

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField() # Un comentario debe tener texto
    created_at = models.DateTimeField(auto_now_add=True)

class CommentPicture(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='pictures')
    url = models.ImageField(upload_to='comment_pics/')