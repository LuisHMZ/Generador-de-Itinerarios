from django.contrib import admin
from .models import Report

# Register your models here.

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    # Ajusta estos nombres según tu models.py real
    list_display = ('id', 'reporter', 'content_type', 'object_id', 'created_at', 'reason', 'status')
    
    # Filtros laterales
    list_filter = ('content_type', 'created_at', 'status')
    
    # Campos de búsqueda
    # Nota: reporter__username asume que el campo ForeignKey se llama 'reporter'
    search_fields = ('reason', 'reporter__username')