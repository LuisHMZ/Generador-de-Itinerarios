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
from friendship.models import Friend, FriendshipRequest
from apps.alertas.models import Notification 
from apps.itineraries.models import Itinerary

User = get_user_model()

# ==========================================
# FUNCIÓN AUXILIAR
# ==========================================
def process_itineraries(itineraries, user):
    if not itineraries: return []
    itin_ids = [i.id for i in itineraries]
    
    my_saves = set(SavedItinerary.objects.filter(user=user, itinerary_id__in=itin_ids).values_list('itinerary_id', flat=True))
    my_ratings = {r.itinerary_id: r.score for r in ItineraryRating.objects.filter(user=user, itinerary_id__in=itin_ids)}

    print(f"DEBUG: Procesando {len(itineraries)} itinerarios para {user.username}.")

    for itin in itineraries:
        itin.feed_type = 'itinerary'
        if not hasattr(itin, 'created_at'): itin.created_at = itin.start_date
        itin.is_saved_by_user = itin.id in my_saves
        itin.user_rating = my_ratings.get(itin.id, 0)
        itin.comments_count_val = itin.feed_comments.count()
        avg = itin.feed_ratings.aggregate(Avg('score'))['score__avg']
        itin.avg_rating = avg if avg else 0
    return itineraries

# ==========================================
# VISTAS FEED
# ==========================================
@login_required
def feed_view(request):
    user = request.user
    friends = Friend.objects.friends(user)
    friend_ids = [f.id for f in friends]
    relevant_users = friend_ids + [user.id]
    online_friends = friends 

    # Posts
    posts = Post.objects.filter(
        Q(user=user) | Q(visibility='public') | (Q(user_id__in=friend_ids) & Q(visibility='friends'))
    ).select_related('user', 'user__profile').prefetch_related('pictures', 'likes', 'saved_by', 'comments').distinct()
    for post in posts: post.feed_type = 'post'

    # Itinerarios: 
    # - Del usuario y sus amigos: mostrar 'friends' y 'public'
    # - De otros usuarios: mostrar solo 'public'
    """ raw_itineraries = list(
        Itinerary.objects.filter(
            Q(
                user_id__in=relevant_users,
                status='published',
                privacy__in=['friends', 'public']
            ) | Q(
                status='published',
                privacy='public'
            )
        ).select_related('user', 'user__profile').distinct()
    ) """# Itinerarios: 
    # - ACTIVOS (is_active=True) <--- Filtro de moderación
    # - PUBLICADOS (status='published')
    # - Lógica de privacidad (Amigos/Público)
    raw_itineraries = list(
        Itinerary.objects.filter(
            is_active=True,      # <--- AGREGADO: Oculta los baneados por admin
            status='published'   # <--- MOVIDO: Aplica a todos, lo sacamos de los Q
        ).filter(
            Q(
                user_id__in=relevant_users,
                privacy__in=['friends', 'public']
            ) | Q(
                privacy='public'
            )
        ).select_related('user', 'user__profile').distinct()
    )
    itineraries = process_itineraries(raw_itineraries, user)

    feed_items = sorted(chain(posts, itineraries), key=attrgetter('created_at'), reverse=True)
    
    # Sugerencias y Status
    candidates = User.objects.exclude(id__in=relevant_users).order_by('?')[:5]
    users_with_status = []
    
    sent_map = {uid: rid for uid, rid in FriendshipRequest.objects.filter(from_user=user).values_list('to_user_id', 'id')}
    received_map = {uid: rid for uid, rid in FriendshipRequest.objects.filter(to_user=user).values_list('from_user_id', 'id')}

    for candidate in candidates:
        status = 'NONE'
        req_id = None
        if candidate.id in sent_map:
            status = 'PENDING_SENT'
            req_id = sent_map[candidate.id]
        elif candidate.id in received_map:
            status = 'PENDING_RECEIVED'
            req_id = received_map[candidate.id]
            
        users_with_status.append({'user': candidate, 'status': status, 'request_id': req_id})

    return render(request, 'feed/home_feed.html', {
        'feed_items': feed_items, 
        'online_friends': online_friends,
        'users_with_status': users_with_status,
        'is_saved_view': False
    })

@login_required
def saved_posts_view(request):
    saved_posts = list(Post.objects.filter(saved_by=request.user).select_related('user', 'user__profile').prefetch_related('pictures', 'likes', 'saved_by', 'comments'))
    for p in saved_posts: 
        p.feed_type = 'post'
    saved_rels = SavedItinerary.objects.filter(user=request.user).select_related('itinerary', 'itinerary__user')
    # Obtener solo los itinerarios guardados que estén publicados y tengan privacy 'friends' o 'public'
    saved_itin_ids = [rel.itinerary_id for rel in saved_rels]
    """ raw_itineraries = list(
        Itinerary.objects.filter(
            id__in=saved_itin_ids,
            status='published',
            privacy__in=['friends', 'public']
        ).select_related('user', 'user__profile')
    ) """
    raw_itineraries = list(
        Itinerary.objects.filter(
            id__in=saved_itin_ids,
            status='published',
            privacy__in=['friends', 'public'],
            is_active=True  # <--- AGREGAR ESTO: Filtra los baneados/ocultos
        ).select_related('user', 'user__profile')
    )
    itineraries = process_itineraries(raw_itineraries, request.user)
    feed_items = sorted(chain(saved_posts, itineraries), key=attrgetter('created_at'), reverse=True)


    # Amigos y Online
    friends = Friend.objects.friends(request.user)
    friend_ids = [f.id for f in friends]
    relevant_users = friend_ids + [request.user.id]
    online_friends = friends 

    # Sugerencias y Status
    candidates = User.objects.exclude(id__in=relevant_users).order_by('?')[:5]
    users_with_status = []
    
    sent_map = {uid: rid for uid, rid in FriendshipRequest.objects.filter(from_user=request.user).values_list('to_user_id', 'id')}
    received_map = {uid: rid for uid, rid in FriendshipRequest.objects.filter(to_user=request.user).values_list('from_user_id', 'id')}

    for candidate in candidates:
        status = 'NONE'
        req_id = None
        if candidate.id in sent_map:
            status = 'PENDING_SENT'
            req_id = sent_map[candidate.id]
        elif candidate.id in received_map:
            status = 'PENDING_RECEIVED'
            req_id = received_map[candidate.id]
            
        users_with_status.append({'user': candidate, 'status': status, 'request_id': req_id})


    context = {
        'feed_items': feed_items,
        'is_saved_view': True,
        'users_with_status': users_with_status,
        'online_friends': online_friends
    }
    return render(request, 'feed/home_feed.html', context)

# ==========================================
# ACCIONES AJAX (CON NOTIFICACIONES CORREGIDAS)
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
            # --- CORRECCIÓN: Generar LINK para Post ---
            try:
                base_url = reverse('/')
                link = request.build_absolute_uri(f"{base_url}?open_post={post.id}")
            except:
                link = '#'
            Notification.objects.create(recipient=post.user, actor=user, message=f"A {user.username} le gustó tu publicación.", link=link)
    return JsonResponse({'status': 'success', 'liked': liked, 'count': post.likes.count()})

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
             # --- CORRECCIÓN: Generar LINK para Post ---
             try:
                base_url = reverse('/')
                link = request.build_absolute_uri(f"{base_url}?open_post={post.id}")
             except:
                link = '#'
             Notification.objects.create(recipient=post.user, actor=request.user, message=f"{request.user.username} comentó tu post.", link=link)
        return JsonResponse({'status': 'success', 'new_comment': format_comment_data(comment, request.user)})
    return JsonResponse({'status': 'error'}, status=400)

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
             # --- CORRECCIÓN: Generar LINK DIFERENTE para Itinerario ---
             try:
                base_url = reverse('')
                # Usamos '?open_itinerary=' para distinguir
                link = request.build_absolute_uri(f"{base_url}?open_itinerary={itinerary.id}")
             except:
                link = '#'
             Notification.objects.create(recipient=itinerary.user, actor=request.user, message=f"{request.user.username} comentó tu itinerario.", link=link)
        return JsonResponse({'status': 'success', 'new_comment': format_comment_data(comment, request.user)})
    return JsonResponse({'status': 'error'}, status=400)

# ... (El resto de funciones: toggle_save, rate_itinerary, load_comments, etc. NO cambian) ...
@login_required
@require_POST
def toggle_save(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    if user in post.saved_by.all(): post.saved_by.remove(user); saved = False
    else: post.saved_by.add(user); saved = True
    return JsonResponse({'status': 'success', 'saved': saved})

@login_required
@require_POST
def create_post_view(request):
    form = CreatePostForm(request.user, request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.user = request.user
        post.save()
        if form.cleaned_data.get('image'): PostPicture.objects.create(post=post, pic_url=form.cleaned_data.get('image'))
        return JsonResponse({'status': 'success'})
    else: return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
@require_POST
def toggle_save_itinerary(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    obj, created = SavedItinerary.objects.get_or_create(user=request.user, itinerary=itinerary)
    if not created: obj.delete(); saved = False
    else: saved = True
    return JsonResponse({'status': 'success', 'saved': saved})

@login_required
@require_POST
def rate_itinerary(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    score = request.POST.get('score')
    if not score or not score.isdigit(): return JsonResponse({'status': 'error'}, status=400)
    ItineraryRating.objects.update_or_create(user=request.user, itinerary=itinerary, defaults={'score': int(score)})
    avg = itinerary.feed_ratings.aggregate(Avg('score'))['score__avg']
    return JsonResponse({'status': 'success', 'new_average': round(avg or 0, 1)})

@login_required
@require_GET
def load_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.filter(parent__isnull=True).select_related('user', 'user__profile').order_by('created_at')
    data = [format_comment_data(c, request.user) for c in comments]
    return JsonResponse({'status': 'success', 'comments': data})

@login_required
@require_GET
def load_itinerary_comments(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    comments = itinerary.feed_comments.filter(parent__isnull=True).select_related('user', 'user__profile').order_by('created_at')
    data = [format_comment_data(c, request.user) for c in comments]
    return JsonResponse({'status': 'success', 'comments': data})

def format_comment_data(c, current_user):
    avatar = c.user.profile.profile_picture.url if c.user.profile.profile_picture else '/static/img/default-avatar.png'
    return {'id': c.id, 'user': c.user.username, 'avatar': avatar, 'text': c.text, 'created_at': timesince(c.created_at), 'likes_count': c.likes.count(), 'is_liked': current_user in c.likes.all(), 'is_owner': current_user == c.user, 'replies': []}

@login_required
@require_POST
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.likes.all(): comment.likes.remove(request.user); liked = False
    else: comment.likes.add(request.user); liked = True
    return JsonResponse({'status': 'success', 'liked': liked, 'count': comment.likes.count()})

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.user or (comment.post and request.user == comment.post.user) or (comment.itinerary and request.user == comment.itinerary.user):
        comment.delete(); return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=403)