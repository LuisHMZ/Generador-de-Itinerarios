# apps/users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.simple_register_view, name='simple_register'),
    path('login/', views.simple_login_view, name='simple_login'),
    path('logout/', views.simple_logout_view, name='simple_logout'),
    ]