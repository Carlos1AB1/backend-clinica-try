import requests
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)

class JWTAuthentication(BaseAuthentication):
    """
    Autenticación JWT distribuida para el microservicio de reportes
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Verificar token con el servicio de autenticación
            response = requests.post(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/verify-token/",
                json={'token': token},
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                # Crear objeto de usuario mock con los datos del token
                user = type('User', (), user_data)()
                return (user, token)
            else:
                raise AuthenticationFailed('Token inválido')
                
        except requests.RequestException as e:
            logger.error(f"Error al verificar token con auth-service: {e}")
            raise AuthenticationFailed('Error de autenticación')

class JWTAuthenticationMiddleware:
    """
    Middleware para agregar información del usuario a todas las requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Agregar usuario a la request si no existe
        if not hasattr(request, 'user'):
            request.user = AnonymousUser()
        
        response = self.get_response(request)
        return response 