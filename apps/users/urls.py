# apps/users/urls.py

from rest_framework import routers
from .api import UserViewSet

routers = routers.DefaultRouter()

routers.register('', UserViewSet, basename='users')

urlpatterns = routers.urls