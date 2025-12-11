from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Report
import json

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

        # Buscar el ContentType correcto
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
