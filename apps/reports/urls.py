from django.urls import path
from . import views

urlpatterns = [
    path('panel/reportes/', views.admin_reports_list, name='admin_reports_list'),
    path('panel/reportes/estado/<int:report_id>/', views.admin_report_change_status, name='admin_report_change_status'),
    path('panel/reportes/ver/<int:report_id>/', views.admin_report_detail, name='admin_report_detail'),
    path('api/crear/', views.create_report_api, name='api_create_report'),
]