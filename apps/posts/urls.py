# apps/posts/urls.py
from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Ruta alternativa para el feed (si la usas)
    path('feed/', views.feed_view, name='feed'),
    
    # Ruta para ver posts guardados
    path('saved/', views.saved_posts_view, name='saved_posts_view'),
    
    # --- NUEVAS RUTAS PARA LOS BOTONES ---
    path('like/<int:post_id>/', views.toggle_like, name='toggle_like'),
    path('save/<int:post_id>/', views.toggle_save, name='toggle_save'),

    path('comments/load/<int:post_id>/', views.load_comments, name='load_comments'),
    path('comments/add/<int:post_id>/', views.add_comment, name='add_comment'),
    
    path('comments/like/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('comments/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
]