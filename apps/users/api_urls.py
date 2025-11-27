# apps/users/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api as views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]