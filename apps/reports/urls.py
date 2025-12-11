from django.urls import path
from . import views  # Asegúrate de importar tus vistas

urlpatterns = [

    # Esta es la nueva ruta para el reporte:
    path('api/create-report/', views.create_report_api, name='create_report_api'),
]