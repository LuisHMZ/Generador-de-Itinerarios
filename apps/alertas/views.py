#apps/alertas/views.py
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST

# -----------------------------------------------------------------
# VISTA 1: "EL LECTOR" (MODIFICADA)
# -----------------------------------------------------------------
@login_required
def api_alertas(request):
    """
    Busca TODAS las notificaciones (leídas o no) para el historial del modal.
    Limitamos a 20 para no sobrecargar el modal.
    """
    # --- ▼▼▼ LÍNEA MODIFICADA ▼▼▼ ---
    notifications = Notification.objects.filter(
        recipient=request.user
        # ¡YA NO FILTRAMOS POR is_read=False!
    ).order_by('-created_at')[:20] # <-- Añadimos un límite
    # --- ▲▲▲ FIN DE LA MODIFICACIÓN ▲▲▲ ---
    
    data_para_js = []
    for notif in notifications:
        data_para_js.append({
            'id': notif.id,
            'message': notif.message,
            'link': notif.link,
            'time': f'hace {timesince(notif.created_at)}',
            # Opcional: podríamos añadir un campo 'is_read' para mostrarlas atenuadas
            # 'is_read': notif.is_read 
        })
        
    return JsonResponse(data_para_js, safe=False)

# -----------------------------------------------------------------
# VISTA 2: "EL ESCRITOR" (SIN CAMBIOS)
# -----------------------------------------------------------------
@login_required
@require_POST
def mark_notifications_as_read(request):
    """
    Marca todas las notificaciones NO LEÍDAS como LEÍDAS.
    (Esta vista está perfecta, no cambia)
    """
    try:
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# -----------------------------------------------------------------
# VISTA 3: "EL CONTADOR" (NUEVA)
# -----------------------------------------------------------------
@login_required
def get_unread_notification_count(request):
    """
    Devuelve solo el NÚMERO de notificaciones NO LEÍDAS.
    """
    try:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'status': 'success', 'unread_count': count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



#--------------------------Nuevo-----------------------------------


# -----------------------------------------------------------------
# VISTA 4: "EL BADGE HTMX" (AGREGAR AL FINAL)
# -----------------------------------------------------------------
@login_required
def badge_notification_html(request):
    """
    Vista exclusiva para HTMX.
    Devuelve HTML (<span>5</span>) o vacío si no hay alertas.
    """
    # Cuenta las no leídas
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    # Si es 0, devolvemos vacío para que HTMX oculte el badge
    if count == 0:
        return HttpResponse("")
    
    # Si hay notificaciones, devolvemos el HTML exacto del badge
    html_badge = f'<span class="notification-count" id="notification-badge-count">{count}</span>'
    
    return HttpResponse(html_badge)