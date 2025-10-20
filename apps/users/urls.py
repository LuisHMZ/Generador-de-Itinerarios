# apps/users/urls.py

from django.urls import path, include
from rest_framework import routers
from .api import UserViewSet
from . import views

router = routers.DefaultRouter()

# Registrar el ViewSet de usuarios
router.register('', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    ]