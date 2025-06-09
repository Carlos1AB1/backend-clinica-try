from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import uuid
from django.core.mail import send_mail
from django.conf import settings
from .models import User, PasswordResetToken
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, TokenObtainPairSerializer,
    TokenVerifySerializer
)

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == User.Role.ADMIN

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['login', 'request_password_reset', 'reset_password', 'token_verify']:
            return [permissions.AllowAny()]
        elif self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            return Response(
                {'error': 'Credenciales inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def token_verify(self, request):
        serializer = TokenVerifySerializer(data=request.data)
        if serializer.is_valid():
            try:
                token = AccessToken(serializer.validated_data['token'])
                user = User.objects.get(id=token['user_id'])
                return Response(UserSerializer(user).data)
            except (InvalidToken, TokenError, User.DoesNotExist):
                return Response(
                    {'error': 'Token inválido'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def request_password_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(email=serializer.validated_data['email'])
                token = str(uuid.uuid4())
                expires_at = timezone.now() + timedelta(minutes=30)
                
                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )

                reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/reset-password/{token}"
                send_mail(
                    'Recuperación de Contraseña',
                    f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                    settings.EMAIL_HOST_USER or 'noreply@veterinaria.com',
                    [user.email],
                    fail_silently=False,
                )
                return Response({'message': 'Se ha enviado un correo con las instrucciones'})
            except User.DoesNotExist:
                return Response(
                    {'error': 'No existe un usuario con ese correo'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                token = PasswordResetToken.objects.get(
                    token=serializer.validated_data['token'],
                    is_used=False
                )
                if not token.is_valid():
                    return Response(
                        {'error': 'El token ha expirado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                user = token.user
                user.set_password(serializer.validated_data['new_password'])
                user.save()

                token.is_used = True
                token.save()

                return Response({'message': 'Contraseña actualizada correctamente'})
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {'error': 'Token inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Contraseña actual incorrecta'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Contraseña actualizada correctamente'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 