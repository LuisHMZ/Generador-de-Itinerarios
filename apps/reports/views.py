from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Report
from apps.users.models import User
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
import json
from apps.alertas.models import Notification
from django.urls import reverse
# Función auxiliar admin
def es_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@require_POST
def create_report_api(request):
    """
    API para crear reportes vía AJAX desde cualquier lugar.
    Espera JSON: { "model_type": "user", "object_id": 1, "reason": "..." }
    """
    try:
        data = json.loads(request.body)
        model_type = data.get('model_type') # Ejemplo: 'user', 'itinerary'
        object_id = data.get('object_id')
        reason = data.get('reason')

        if not reason:
            return JsonResponse({'error': 'El motivo es obligatorio'}, status=400)

        # Buscar el ContentType correcto (ej. si model_type es 'user', busca auth.User)
        # Nota: Asegurarse de que el string coincida con el 'model' de Django (minúsculas)
        try:
            # Filtro de seguridad: Solo permitir modelos válidos definidos en tu Report
            if model_type not in ['user', 'itinerary', 'post', 'comment', 'review']:
                return JsonResponse({'error': 'Tipo de contenido no válido'}, status=400)
            
            ct = ContentType.objects.get(model=model_type)
        except ContentType.DoesNotExist:
            return JsonResponse({'error': 'Modelo no encontrado'}, status=400)

        # Crear el reporte
        Report.objects.create(
            reporter=request.user,
            content_type=ct,
            object_id=object_id,
            reason=reason
        )

        return JsonResponse({'message': 'Reporte enviado correctamente.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(es_admin)
def admin_reports_list(request):
    # Obtener reportes ordenados (más recientes primero)
    # Usamos select_related para optimizar la carga del reportero y content_type
    reports_list = Report.objects.all().select_related('reporter', 'content_type').order_by('-created_at')

    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        reports_list = reports_list.filter(status=status_filter)

    # Paginación
    paginator = Paginator(reports_list, 15)
    page_number = request.GET.get('page')
    reports = paginator.get_page(page_number)

    return render(request, 'reports/admin-reportes.html', {
        'reports': reports,
        'current_status': status_filter
    })

@login_required
@user_passes_test(es_admin)
@require_POST
def admin_report_change_status(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    new_status = request.POST.get('status')
    
    if new_status in Report.Status.values:
        report.status = new_status
        report.save()
        messages.success(request, f'Reporte #{report.id} actualizado a {report.get_status_display()}.')
    else:
        messages.error(request, 'Estado inválido.')
        
    return redirect('admin_reports_list')

@login_required
@user_passes_test(es_admin)
def admin_report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    # LÓGICA PARA IDENTIFICAR AL "ACUSADO" (Target User)
    # Dependiendo de qué se reportó, el dueño es diferente
    target_user = None
    obj = report.content_object
    
    if obj:
        if report.content_type.model == 'user':
            target_user = obj # El objeto es el usuario mismo
        elif hasattr(obj, 'user'):
            target_user = obj.user # Itinerarios, Posts, Comentarios suelen tener campo 'user'
        elif hasattr(obj, 'owner'): # Por si acaso se llama owner
            target_user = obj.owner

    # PROCESAR EL ENVÍO DE NOTIFICACIÓN
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Caso 1: Cambiar Estado
        if action == 'change_status':
            new_status = request.POST.get('status')
            report.status = new_status
            report.save()
            messages.success(request, f'Estado del reporte actualizado a {report.get_status_display()}.')
        
        elif action == 'notify_user':
            mensaje_texto = request.POST.get('notification_message')
            
            if target_user and mensaje_texto:
                
                # Link por defecto (seguro)
                link_destino = "/perfil/" 
                
                try:
                    modelo = report.content_type.model
                    
                    # --- [CRUCIAL] ESTA LÍNEA DEBE IR ANTES DE LOS IF ---
                    objeto = report.content_object 
                    # ----------------------------------------------------

                    # Verificamos que el objeto siga existiendo (que no sea None)
                    if objeto:
                        if modelo == 'itinerary':
                            link_destino = reverse('itineraries:view_itinerary', args=[objeto.id])
                        
                        elif modelo == 'user':
                            link_destino = reverse('profile_view', args=[objeto.username])

                        elif modelo == 'post':
                            link_destino = reverse('home') + f"?open_post={objeto.id}"
                            
                        elif modelo == 'comment':
                            # Verificamos si es de post o itinerario
                            if hasattr(objeto, 'post') and objeto.post:
                                link_destino = reverse('home') + f"?open_post={objeto.post.id}"
                            elif hasattr(objeto, 'itinerary') and objeto.itinerary:
                                link_destino = reverse('view_itinerary', args=[objeto.itinerary.id])
                    else:
                        print("El objeto reportado parece haber sido eliminado.")

                except Exception as e:
                    print(f"No se pudo generar link específico: {e}")

                # --- 2. Crear la Notificación ---
                Notification.objects.create(
                    recipient=target_user,
                    actor=request.user,
                    message=f"Aviso de Admin: {mensaje_texto}",
                    link=link_destino  # <--- AQUI VA EL LINK DINÁMICO
                )
                messages.success(request, f'Notificación enviada a @{target_user.username}.')
            else:
                messages.error(request, 'No se pudo notificar (usuario no encontrado o mensaje vacío).')
        # -------------------------------------------------
        
        return redirect('admin_report_detail', report_id=report.id)

    return render(request, 'reports/admin-reporte-detalle.html', {
        'report': report,
        'target_user': target_user,
        'content_type_name': report.content_type.model
    })
# Create your views here.
