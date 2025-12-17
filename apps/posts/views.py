#apps/post/views.py
from django.utils.timesince import timesince
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required, user_passes_test 
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CreatePostForm

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
        Q(user=user) | Q(visibility='public') | (Q(user_id__in=friend_ids) & Q(visibility='friends')), is_active=True
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
        
        # Solo notificamos si el usuario no se dio like a sí mismo
        if post.user != user: 
            # Generamos el link relativo limpio: /home/?open_post=123
            link = f"{reverse('home')}?open_post={post.id}"
            
            Notification.objects.create(
                recipient=post.user,
                actor=user,
                message=f"A {user.username} le gustó tu publicación.",
                link=link
            )

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
            # Link para abrir el post específico
            link = f"{reverse('home')}?open_post={post.id}"
            
            Notification.objects.create(
                recipient=post.user, 
                actor=request.user, 
                message=f"{request.user.username} comentó tu post.", 
                link=link
            )
            
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
            # Link específico para itinerarios
            link = f"{reverse('home')}?open_itinerary={itinerary.id}"
            
            Notification.objects.create(
                recipient=itinerary.user, 
                actor=request.user, 
                message=f"{request.user.username} comentó tu itinerario.", 
                link=link
            )
            
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
    # Obtener avatar (igual que antes)
    avatar = c.user.profile.profile_picture.url if c.user.profile.profile_picture else '/static/img/default-avatar.png'
    
    # --- CORRECCIÓN AQUÍ ---
    # Usamos 'replies' porque así lo definiste en tu models.py
    replies_qs = c.replies.all().order_by('created_at')
    
    # Llamada recursiva: formateamos también las respuestas hijas
    replies_data = [format_comment_data(r, current_user) for r in replies_qs]
    # -----------------------

    return {
        'id': c.id,
        'user': c.user.username,
        'avatar': avatar,
        'text': c.text,
        'created_at': timesince(c.created_at),
        'likes_count': c.likes.count(),
        'is_liked': current_user in c.likes.all(),
        'is_owner': current_user == c.user,
        'replies': replies_data  # Antes esto era [], ahora enviamos las respuestas reales
    }

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
        
        # Notificar al dueño del comentario (si no es uno mismo)
        if comment.user != user:
            target_link = '#'
            
            # Determinamos si el comentario está en un Post o en un Itinerario
            if comment.post:
                target_link = f"{reverse('home')}?open_post={comment.post.id}"
            elif comment.itinerary:
                target_link = f"{reverse('home')}?open_itinerary={comment.itinerary.id}"
            
            Notification.objects.create(
                recipient=comment.user,
                actor=user,
                message=f"A {user.username} le gustó tu comentario.",
                link=target_link
            )
            
    return JsonResponse({'status': 'success', 'liked': liked, 'count': comment.likes.count()})

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.user or (comment.post and request.user == comment.post.user) or (comment.itinerary and request.user == comment.itinerary.user):
        comment.delete(); return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=403)


@login_required
def create_post_page_view(request):
    """
    Vista para renderizar la pantalla completa de creación de posts (post.html).
    """
    if request.method == 'POST':
        # Nota: Asegúrate de que tu CreatePostForm acepte el argumento 'user'
        # si así lo definiste. Si no, quita 'user=request.user'.
        form = CreatePostForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            form.save_m2m() # Guardar relaciones ManyToMany si las hay
            messages.success(request, '¡Publicación creada con éxito!')
            return redirect('profile_view', username=request.user.username)
        else:
            messages.error(request, 'Error al crear el post. Revisa el formulario.')
    else:
        form = CreatePostForm(user=request.user)

    return render(request, 'users/post.html', {'form': form})

@login_required
def search_view(request):
    query = request.GET.get('q', '').strip()
    
    users = []
    posts = []
    itineraries = []

    if query:
        # 1. Buscar Personas (por username o nombre)
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id) # No buscarme a mí mismo

        # 2. Buscar Posts (Solo públicos o de amigos - simplificado a públicos por ahora para búsqueda general)
        # Nota: Puedes refinar esto con lógica de amigos si quieres ser muy estricto.
        posts = Post.objects.filter(
            text__icontains=query, 
            visibility='public'
        ).select_related('user', 'user__profile').prefetch_related('pictures', 'likes', 'comments').order_by('-created_at')

        # 3. Buscar Itinerarios
        itineraries = Itinerary.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        ).select_related('user').order_by('-start_date')

        # Procesar posts e itinerarios para el feed (like status, etc)
        # Reutilizamos la lógica que ya tienes para saber si diste like
        for post in posts:
            post.feed_type = 'post'
        
        # Si tienes la función process_itineraries importada, úsala aquí:
        # itineraries = process_itineraries(itineraries, request.user) 
        # Si no, al menos marca el feed_type:
        for itin in itineraries:
            itin.feed_type = 'itinerary'

    return render(request, 'feed/search.html', {
        'query': query,
        'users': users,
        'posts': posts,
        'itineraries': itineraries,
        'is_saved_view': False # Para reutilizar estilos si hace falta
    })

def es_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(es_admin)
def admin_post_preview(request, post_id):
    # 1. Obtenemos el post
    post = get_object_or_404(Post, id=post_id)
    
    # 2. Capturamos el ID del reporte (si viene en la URL) para el botón "Volver"
    source_report_id = request.GET.get('report_id')
    
    # 3. Renderizamos el template que creaste
    return render(request, 'social/admin_post_preview.html', {
        'post': post,
        'source_report_id': source_report_id
    })

@login_required
@user_passes_test(es_admin)
def admin_toggle_post_visibility(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Invertimos el valor: Si es True pasa a False, y viceversa
    post.is_active = not post.is_active 
    post.save()
    
    # Redirigimos a la página desde donde se hizo click (el preview)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# ==========================================
# VISTAS PARA CAMBIAR PRIVACIDAD Y ELIMINAR POSTS
# ==========================================

@login_required
@require_POST
def update_post_privacy_view(request, post_id):
    """Cambia la privacidad de un post"""
    import json
    post = get_object_or_404(Post, id=post_id)
    
    # Verificar que el usuario es el propietario del post
    if post.user != request.user:
        return JsonResponse({'status': 'error', 'message': 'No tienes permiso para editar este post'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_visibility = data.get('visibility')
        
        if new_visibility in ['public', 'friends', 'private']:
            post.visibility = new_visibility
            post.save()
            return JsonResponse({'status': 'success', 'visibility': new_visibility})
        else:
            return JsonResponse({'status': 'error', 'message': 'Privacidad inválida'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Datos inválidos'}, status=400)

@login_required
@require_POST
def delete_post_view(request, post_id):
    """Elimina un post"""
    post = get_object_or_404(Post, id=post_id)
    
    # Verificar que el usuario es el propietario del post
    if post.user != request.user:
        return JsonResponse({'status': 'error', 'message': 'No tienes permiso para eliminar este post'}, status=403)
    
    try:
        post.delete()
        return JsonResponse({'status': 'success', 'message': 'Post eliminado correctamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)