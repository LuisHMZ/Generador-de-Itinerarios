#apps/messaging/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# --- Modelos de la App `messaging` ---

class Conversation(models.Model):
    # La tabla intermedia se crea automáticamente con esta relación
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # --- CAMBIOS AQUÍ ---
    # 1. Content ahora puede estar vacío (blank=True, null=True)
    content = models.TextField(blank=True, null=True) 

    # 2. Nuevo campo Image
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True) 
    # --------------------
        
    created_at = models.DateTimeField(auto_now_add=True)
    

    is_read = models.BooleanField(default=False)

class MessageReadStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('message', 'user')



    
    
    
    