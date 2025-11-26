from django.utils.timesince import timesince
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse 
from django.views.decorators.http import require_POST, require_GET
from django.urls import reverse
from django.db.models import Q, Avg
from itertools import chain
from operator import attrgetter

from .forms import CreatePostForm, CommentForm
from .models import Post, Comment, PostPicture, SavedItinerary, ItineraryRating
from friendship.models import Friend
from apps.alertas.models import Notification 
from apps.itineraries.models import Itinerary

User = get_user_model()

# ==========================================
# FUNCIÓN AUXILIAR (EL CEREBRO DE LOS DATOS)
# ==========================================
def process_itineraries(itineraries, user):
    """
    Inyecta datos sociales (likes, guardados, estrellas) a una lista de itinerarios.
    """
    if not itineraries:
        return []

    itin_ids = [i.id for i in itineraries]

    # 1. ¿Cuáles guardé YO?
    my_saves = set(SavedItinerary.objects.filter(
        user=user, 
        itinerary_id__in=itin_ids
    ).values_list('itinerary_id', flat=True))

    # 2. ¿Qué nota les puse YO?
    my_ratings = {
        r.itinerary_id: r.score 
        for r in ItineraryRating.objects.filter(user=user, itinerary_id__in=itin_ids)
    }

    # ESTE MENSAJE DEBE SALIR EN TU TERMINAL
    print(f"DEBUG: Procesando {len(itineraries)} itinerarios para {user.username}. Guardados encontrados: {len(my_saves)}")

    for itin in itineraries:
        itin.feed_type = 'itinerary'
        
        # Fecha para ordenar
        if not hasattr(itin, 'created_at'): 
            itin.created_at = itin.start_date
        
        # Inyectar datos
        itin.is_saved_by_user = itin.id in my_saves
        itin.user_rating = my_ratings.get(itin.id, 0)
        
        # Contar comentarios (usando el related_name correcto)
        itin.comments_count_val = itin.feed_comments.count()
        
        # Promedio general
        avg = itin.feed_ratings.aggregate(Avg('score'))['score__avg']
        itin.avg_rating = avg if avg else 0
        
    return itineraries


# ==========================================
# VISTAS PRINCIPALES (FEED Y GUARDADOS)
# ==========================================

@login_required
def feed_view(request):
    user = request.user
    friend_ids = [f.id for f in Friend.objects.friends(user)]
    relevant_users = friend_ids + [user.id]
    
    # 1. POSTS
    posts = Post.objects.filter(
        Q(user=user) | Q(visibility='public') | (Q(user_id__in=friend_ids) & Q(visibility='friends'))
    ).select_related('user', 'user__profile').prefetch_related('pictures', 'likes', 'saved_by', 'comments').distinct()
    
    for post in posts: post.feed_type = 'post'

    # 2. ITINERARIOS
    raw_itineraries = list(Itinerary.objects.filter(
        user_id__in=relevant_users
    ).select_related('user', 'user__profile'))
    
    # AQUÍ ESTABA EL ERROR ANTES: LLAMAMOS A LA FUNCIÓN DE PROCESAMIENTO
    itineraries = process_itineraries(raw_itineraries, user)

    # 3. Combinar
    feed_items = sorted(chain(posts, itineraries), key=attrgetter('created_at'), reverse=True)
    
    suggested_friends = User.objects.exclude(id__in=relevant_users).order_by('?')[:5]

    return render(request, 'feed/home_feed.html', {
        'feed_items': feed_items, 
        'suggested_friends': suggested_friends,
        'is_saved_view': False
    })

@login_required
def saved_posts_view(request):
    # 1. POSTS Guardados
    saved_posts = list(Post.objects.filter(saved_by=request.user).select_related('user', 'user__profile').prefetch_related('pictures', 'likes', 'saved_by', 'comments'))
    for p in saved_posts: p.feed_type = 'post'

    # 2. ITINERARIOS Guardados
    saved_rels = SavedItinerary.objects.filter(user=request.user).select_related('itinerary', 'itinerary__user')
    raw_itineraries = [rel.itinerary for rel in saved_rels]
    
    # Procesamos igual que en el feed
    itineraries = process_itineraries(raw_itineraries, request.user)

    feed_items = sorted(chain(saved_posts, itineraries), key=attrgetter('created_at'), reverse=True)
    
    return render(request, 'feed/home_feed.html', {'feed_items': feed_items, 'is_saved_view': True})


# ==========================================
# ACCIONES AJAX
# ==========================================

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
            Notification.objects.create(recipient=post.user, actor=user, message=f"A {user.username} le gustó tu publicación.")
    return JsonResponse({'status': 'success', 'liked': liked, 'count': post.likes.count()})

@login_required
@require_POST
def toggle_save(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    if user in post.saved_by.all():
        post.saved_by.remove(user)
        saved = False
    else:
        post.saved_by.add(user)
        saved = True
    return JsonResponse({'status': 'success', 'saved': saved})

@login_required
@require_POST
def create_post_view(request):
    form = CreatePostForm(request.user, request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.user = request.user
        post.save()
        image = form.cleaned_data.get('image')
        if image:
            PostPicture.objects.create(post=post, pic_url=image)
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
@require_POST
def toggle_save_itinerary(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    obj, created = SavedItinerary.objects.get_or_create(user=request.user, itinerary=itinerary)
    if not created:
        obj.delete()
        saved = False
    else:
        saved = True
    return JsonResponse({'status': 'success', 'saved': saved})

@login_required
@require_POST
def rate_itinerary(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    score = request.POST.get('score')
    
    if not score or not score.isdigit():
        return JsonResponse({'status': 'error', 'message': 'Puntaje inválido'}, status=400)
    score = int(score)
    if score < 1 or score > 5:
        return JsonResponse({'status': 'error', 'message': 'Rango 1-5'}, status=400)

    ItineraryRating.objects.update_or_create(
        user=request.user, 
        itinerary=itinerary,
        defaults={'score': score}
    )
    
    avg = itinerary.feed_ratings.aggregate(Avg('score'))['score__avg']
    return JsonResponse({'status': 'success', 'new_average': round(avg or 0, 1)})


# ==========================================
# COMENTARIOS
# ==========================================

@login_required
@require_GET
def load_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.filter(parent__isnull=True).select_related('user', 'user__profile').order_by('created_at')
    data = [format_comment_data(c, request.user) for c in comments]
    return JsonResponse({'status': 'success', 'comments': data})

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        if request.POST.get('parent_id'):
            comment.parent = get_object_or_404(Comment, id=request.POST.get('parent_id'))
        comment.save()
        
        if post.user != request.user:
             Notification.objects.create(recipient=post.user, actor=request.user, message=f"{request.user.username} comentó tu post.")
        return JsonResponse({'status': 'success', 'new_comment': format_comment_data(comment, request.user)})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@require_GET
def load_itinerary_comments(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    comments = itinerary.feed_comments.filter(parent__isnull=True).select_related('user', 'user__profile').order_by('created_at')
    data = [format_comment_data(c, request.user) for c in comments]
    return JsonResponse({'status': 'success', 'comments': data})

@login_required
@require_POST
def add_itinerary_comment(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.itinerary = itinerary 
        if request.POST.get('parent_id'):
            comment.parent = get_object_or_404(Comment, id=request.POST.get('parent_id'))
        comment.save()
        
        if itinerary.user != request.user:
             Notification.objects.create(recipient=itinerary.user, actor=request.user, message=f"{request.user.username} comentó tu itinerario.")
        return JsonResponse({'status': 'success', 'new_comment': format_comment_data(comment, request.user)})
    return JsonResponse({'status': 'error'}, status=400)

def format_comment_data(c, current_user):
    avatar_url = c.user.profile.profile_picture.url if c.user.profile.profile_picture else '/static/img/default-avatar.png'
    return {
        'id': c.id,
        'user': c.user.username,
        'avatar': avatar_url,
        'text': c.text,
        'created_at': timesince(c.created_at),
        'likes_count': c.likes.count(),
        'is_liked': current_user in c.likes.all(),
        'is_owner': current_user == c.user,
        'replies': []
    }

@login_required
@require_POST
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    return JsonResponse({'status': 'success', 'liked': liked, 'count': comment.likes.count()})

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    is_owner = request.user == comment.user
    is_post_owner = comment.post and request.user == comment.post.user
    is_itin_owner = comment.itinerary and request.user == comment.itinerary.user
    if is_owner or is_post_owner or is_itin_owner:
        comment.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=403)