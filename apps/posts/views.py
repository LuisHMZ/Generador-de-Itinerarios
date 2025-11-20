# apps/posts/views.py

from django.utils.timesince import timesince
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse # <-- Necesario para AJAX
from django.views.decorators.http import require_POST # <-- Seguridad para los botones
from django.urls import reverse


from .forms import CommentForm
from .models import Comment, Post
from django.views.decorators.http import require_GET

# Modelos
from .models import Post
from friendship.models import Friend
from apps.alertas.models import Notification # <-- Para notificar el like

User = get_user_model()

# --- VISTAS DE LIKES Y GUARDADOS (NUEVAS) ---

# En: apps/posts/views.py

@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    
    if user in post.likes.all():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True
        
        if post.user != user: 
            try:
                # ▼▼▼ CAMBIO: Agregamos ?open_post=ID al enlace ▼▼▼
                base_url = reverse('home')
                link = request.build_absolute_uri(f"{base_url}?open_post={post.id}")
                # ▲▲▲ FIN DEL CAMBIO ▲▲▲
            except:
                link = '#'

            Notification.objects.create(
                recipient=post.user,
                actor=user,
                message=f"A {user.username} le gustó tu publicación.",
                link=link
            )
    
    return JsonResponse({'status': 'success', 'liked': liked, 'count': post.likes.count()})

@login_required
@require_POST
def toggle_save(request, post_id):
    """
    Guarda o quita de guardados una publicación.
    Devuelve JSON.
    """
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    
    if user in post.saved_by.all():
        # Si ya lo guardó, lo quitamos
        post.saved_by.remove(user)
        saved = False
    else:
        # Si no, lo guardamos
        post.saved_by.add(user)
        saved = True
        
    return JsonResponse({
        'status': 'success', 
        'saved': saved
    })


# --- VISTAS DE VISUALIZACIÓN ---

@login_required
def saved_posts_view(request):
    """
    Muestra las publicaciones que el usuario ha guardado.
    """
    # Filtramos los posts donde el usuario actual está en la lista 'saved_by'
    saved_posts = Post.objects.filter(saved_by=request.user).select_related(
        'user', 'user__profile'
    ).prefetch_related(
        'pictures' 
    ).order_by('-created_at')

    context = {
        'posts': saved_posts,
        'is_saved_view': True 
    }
    
    # Reutilizamos la plantilla del feed
    return render(request, 'feed/home_feed.html', context)


@login_required
def feed_view(request):
    # 1. Obtener la lista de IDs de mis amigos
    friend_ids = Friend.objects.friends(request.user)
    # Convertimos la lista de objetos User a una lista de IDs
    friend_ids = [f.id for f in friend_ids]
    
    # 2. Obtener los posts de mis amigos Y mis propios posts
    # Corregido: Usamos 'user_id__in' porque tu modelo Post tiene el campo 'user', no 'author'
    posts = Post.objects.filter(
        user_id__in=friend_ids + [request.user.id]
    ).select_related('user', 'user__profile').prefetch_related('pictures').order_by('-created_at')

    # 3. Obtener sugerencias de amigos
    suggested_friends = User.objects.exclude(
        id__in=friend_ids + [request.user.id]
    ).order_by('?')[:5]

    context = {
        'posts': posts,
        'suggested_friends': suggested_friends
    }
    
    return render(request, 'feed/feed.html', context)

@login_required
@require_GET
def load_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Traemos solo los comentarios principales (los que no tienen padre)
    comments = post.comments.filter(parent__isnull=True).select_related('user', 'user__profile').prefetch_related('likes', 'replies').order_by('created_at')
    
    def format_comment(c):
        # Función auxiliar para formatear datos
        avatar_url = c.user.profile.profile_picture.url if c.user.profile.profile_picture else '/static/img/default-avatar.png'
        return {
            'id': c.id,
            'user': c.user.username,
            'avatar': avatar_url,
            'text': c.text,
            'created_at': timesince(c.created_at),
            'likes_count': c.likes.count(),
            'is_liked': request.user in c.likes.all(),
            'is_owner': request.user == c.user or request.user == post.user, # Dueño del comentario o del post
            # Recursividad para respuestas (traemos los hijos)
            'replies': [format_comment(reply) for reply in c.replies.all().order_by('created_at')]
        }

    data_comments = [format_comment(c) for c in comments]
    return JsonResponse({'status': 'success', 'comments': data_comments})

# 2. AGREGAR COMENTARIO (Actualizado para recibir parent_id)
@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    parent_id = request.POST.get('parent_id') 

    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        
        if parent_id:
            parent_comment = get_object_or_404(Comment, id=parent_id)
            comment.parent = parent_comment

        comment.save()
        
        # ▼▼▼ CAMBIO: Enlace inteligente ▼▼▼
        try:
            base_url = reverse('home')
            link = request.build_absolute_uri(f"{base_url}?open_post={post.id}")
        except:
            link = '#'
        # ▲▲▲ FIN DEL CAMBIO ▲▲▲
        
        if post.user != request.user:
             Notification.objects.create(recipient=post.user, actor=request.user, message=f"{request.user.username} comentó tu publicación.", link=link)

        if parent_id:
             # Recuperamos el padre de nuevo para asegurar contexto
             parent_comment = get_object_or_404(Comment, id=parent_id)
             if parent_comment.user != request.user and parent_comment.user != post.user:
                Notification.objects.create(recipient=parent_comment.user, actor=request.user, message=f"{request.user.username} respondió a tu comentario.", link=link)

        # ... (El resto del retorno JSON sigue igual) ...
        avatar_url = request.user.profile.profile_picture.url if request.user.profile.profile_picture else '/static/img/default-avatar.png'
        return JsonResponse({'status': 'success', 'new_comment': {'id': comment.id, 'user': request.user.username, 'avatar': avatar_url, 'text': comment.text, 'created_at': 'justo ahora', 'likes_count': 0, 'is_liked': False, 'is_owner': True, 'replies': []}})
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

# 3. DAR LIKE A COMENTARIO (Nueva)
@login_required
@require_POST
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user
    
    if user in comment.likes.all():
        comment.likes.remove(user)
        liked = False
    else:
        comment.likes.add(user)
        liked = True
        
        if comment.user != user:
            try:
                # ▼▼▼ CAMBIO: Enlace al post padre ▼▼▼
                base_url = reverse('home')
                link = request.build_absolute_uri(f"{base_url}?open_post={comment.post.id}")
                # ▲▲▲ FIN DEL CAMBIO ▲▲▲
            except:
                link = '#'
                
            Notification.objects.create(recipient=comment.user, actor=user, message=f"A {user.username} le gustó tu comentario.", link=link)
    
    return JsonResponse({'status': 'success', 'liked': liked, 'count': comment.likes.count()})

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    # Solo el autor o dueño del post pueden borrar
    if request.user == comment.user or request.user == comment.post.user:
        comment.delete()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'No tienes permiso'}, status=403)