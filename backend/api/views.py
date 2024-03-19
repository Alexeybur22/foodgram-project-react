from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import TokenObtainSerializer
from rest_framework import filters, status, viewsets
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from .serializers import UserRegistrationSerializer, UserSerializer
from rest_framework.response import Response


User = get_user_model()


class TokenObtainViewSet(TokenObtainPairView):
    """Представление для получения пользовательских JWT-токенов."""

    serializer_class = TokenObtainSerializer


class UserViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    ListModelMixin,
    viewsets.GenericViewSet
):
    
    queryset = User.objects.all()
    serializer_class = UserSerializer


    @action(detail=False,
            methods=('get'),
            permission_classes=(IsAuthenticated,),
            serializer_class=UserSerializer)
    def me(self, request):
        serializer = UserSerializer(request.user,
                                       data=request.data,
                                       partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    