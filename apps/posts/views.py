# apps/posts/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post
# --- LÍNEA CORREGIDA ---
from friendship.models import Friend # Antes decía 'from apps.friends.models'
# --- FIN DE LA CORRECCIÓN ---
from django.contrib.auth import get_user_model # Usamos get_user_model para User

User = get_user_model() # Obtenemos tu modelo de User

@login_required
def feed_view(request):
    # 1. Obtener la lista de IDs de mis amigos
    # Usamos la librería 'friendship' que ya instalamos
    friend_ids = Friend.objects.friends(request.user).values_list('id', flat=True)
    
    # 2. Obtener los posts de mis amigos Y mis propios posts
    # Usamos __in para filtrar por la lista de IDs
    posts = Post.objects.filter(
        author_id__in=list(friend_ids) + [request.user.id]
    ).order_by('-created_at') # Más nuevos primero

    # 3. Obtener sugerencias de amigos (ej: 5 usuarios que NO sean mis amigos y no sea yo)
    suggested_friends = User.objects.exclude(
        id__in=list(friend_ids) + [request.user.id]
    ).order_by('?')[:5] # '?' es aleatorio, pero puede ser lento

    # 4. Enviar los datos a la plantilla
    context = {
        'posts': posts,
        'suggested_friends': suggested_friends
    }
    
    return render(request, 'feed/feed.html', context)