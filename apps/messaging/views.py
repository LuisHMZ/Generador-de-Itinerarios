from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Max
from django.views.decorators.http import require_POST
from django.utils.timesince import timesince
from django.utils import timezone
from django.urls import reverse # <--- IMPORTANTE

from .models import Conversation, Message
from apps.alertas.models import Notification # <--- IMPORTANTE

User = get_user_model()

@login_required
def inbox_view(request):
    # Pasamos el usuario explícitamente por seguridad del template
    return render(request, 'messaging/chat.html', {'user': request.user})

@login_required
def get_conversations(request):
    conversations = request.user.conversations.annotate(
        last_msg_time=Max('messages__created_at')
    ).order_by('-last_msg_time')

    data = []
    for chat in conversations:
        other_user = chat.participants.exclude(id=request.user.id).first()
        if not other_user: continue 

        last_message = chat.messages.order_by('-created_at').first()
        preview = last_message.content if last_message else "Nueva conversación"
        
        avatar = other_user.profile.profile_picture.url if hasattr(other_user, 'profile') and other_user.profile.profile_picture else '/static/img/default-avatar.png'

        data.append({
            'id': chat.id,
            'name': other_user.username,     # Nombre visual
            'username': other_user.username, # Username para URLs (IMPORTANTE)
            'avatar': avatar,
            'preview': preview[:30] + '...' if len(preview) > 30 else preview,
            'time': timesince(last_message.created_at).split(',')[0] if last_message else '',
        })
    
    return JsonResponse({'conversations': data})

@login_required
def get_messages(request, conversation_id):
    chat = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Datos del OTRO usuario para el encabezado (en caso de recarga)
    other_user = chat.participants.exclude(id=request.user.id).first()
    other_username = other_user.username if other_user else ""
    other_avatar = other_user.profile.profile_picture.url if other_user and hasattr(other_user, 'profile') and other_user.profile.profile_picture else '/static/img/default-avatar.png'

    last_id = request.GET.get('last_id')
    if last_id:
        messages = chat.messages.filter(id__gt=last_id).order_by('created_at')
    else:
        messages = chat.messages.all().order_by('created_at')

    data = []
    for msg in messages:
        avatar = msg.user.profile.profile_picture.url if hasattr(msg.user, 'profile') and msg.user.profile.profile_picture else '/static/img/default-avatar.png'
        data.append({
            'id': msg.id,
            'content': msg.content,
            'is_me': (msg.user == request.user),
            'time': msg.created_at.strftime("%H:%M"),
            'avatar': avatar,
            'sender_name': msg.user.username
        })
        
    return JsonResponse({
        'messages': data,
        'chat_partner': {
            'name': other_user.username if other_user else "Usuario",
            'username': other_username,
            'avatar': other_avatar
        }
    })

@login_required
@require_POST
def send_message(request, conversation_id):
    chat = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'status': 'error', 'message': 'Mensaje vacío'}, status=400)
        
    Message.objects.create(conversation=chat, user=request.user, content=content)
    
    chat.updated_at = timezone.now()
    chat.save()

    # --- CREAR NOTIFICACIÓN PARA EL DESTINATARIO ---
    recipient = chat.participants.exclude(id=request.user.id).first()
    if recipient:
        # Creamos el link directo a este chat
        try:
            base_url = reverse('messaging:inbox') # /api/messaging/
            link = f"{base_url}?open_chat={chat.id}"
            
            Notification.objects.create(
                recipient=recipient,
                actor=request.user,
                message=f"Nuevo mensaje de {request.user.username}",
                link=link
            )
        except Exception as e:
            print(f"Error creando notificación: {e}")

    return JsonResponse({'status': 'success'})

@login_required
def start_conversation(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user: return redirect('messaging:inbox')

    chats = Conversation.objects.filter(participants=request.user).filter(participants=target)
    if chats.exists():
        chat = chats.first()
    else:
        chat = Conversation.objects.create()
        chat.participants.add(request.user, target)
    
    return redirect(f'/api/messaging/?open_chat={chat.id}')