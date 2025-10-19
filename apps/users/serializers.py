# apps/users/serializers.py

from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Define los campos del modelo User que quieres mostrar en la API
        fields = ['id', 'username', 'email', 'first_name', 'last_name']