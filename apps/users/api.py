from .models import Profile, UserConnection, Notification, PasswordHistory
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .serializers import UserSerializer
from rest_framework.decorators import action

class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing User instances.
    Attributes:
        queryset (QuerySet): The set of User objects to operate on.
        serializer_class (Serializer): The serializer class used for User objects.
        permission_classes (list): List of permission classes that control access.
    Methods:
        me(request):
            Returns the serialized data of the currently authenticated user.
            Accessible via GET request at the 'me' action endpoint.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self,request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
