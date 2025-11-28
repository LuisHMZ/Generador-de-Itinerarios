from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('create/', views.create_post_view, name='create_post'),
    path('toggle-like/<int:post_id>/', views.toggle_like, name='toggle_like'),
    path('toggle-save/<int:post_id>/', views.toggle_save, name='toggle_save'),
    
    # --- RUTAS DE ITINERARIOS ---
    path('itinerary/toggle-save/<int:itinerary_id>/', views.toggle_save_itinerary, name='toggle_save_itinerary'),
    path('itinerary/rate/<int:itinerary_id>/', views.rate_itinerary, name='rate_itinerary'),
    
    # --- RUTAS DE COMENTARIOS (POSTS) ---
    # Quitamos el 'api/' del inicio porque ya viene incluido en la ruta principal
    path('comments/load/<int:post_id>/', views.load_comments, name='load_comments'),
    path('comments/add/<int:post_id>/', views.add_comment, name='add_comment'),
    
    # --- RUTAS DE COMENTARIOS (ITINERARIOS) ---
    path('itinerary/comments/load/<int:itinerary_id>/', views.load_itinerary_comments, name='load_itinerary_comments'),
    path('itinerary/comments/add/<int:itinerary_id>/', views.add_itinerary_comment, name='add_itinerary_comment'),
    
    # --- ACCIONES GENERALES ---
    path('comments/like/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('comments/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
]