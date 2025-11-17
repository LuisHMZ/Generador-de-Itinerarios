# apps/posts/urls.py
from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('feed/', views.feed_view, name='feed'),
    # ... (aquí también debe estar tu ruta 'create' que usamos en el botón)
    # path('crear/', views.crear_post_view, name='create'), 
]