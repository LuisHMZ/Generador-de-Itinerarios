from .models import Profile, UserConnection, Notification, PasswordHistory
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .serializers import UserSerializer
from rest_framework.decorators import action

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def me(self,request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
