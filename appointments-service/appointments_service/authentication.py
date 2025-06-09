import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not authorization_header:
            return None
            
        try:
            token = authorization_header.split(' ')[1]
            return self.verify_token(token)
        except (IndexError, ValueError):
            raise AuthenticationFailed('Token inválido')
    
    def verify_token(self, token):
        try:
            # Verificar el token con el microservicio de autenticación
            response = requests.post(
                f"{settings.AUTH_SERVICE_URL}/api/users/token_verify/",
                data={'token': token},
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return (user_data, token)
            else:
                raise AuthenticationFailed('Token inválido o expirado')
                
        except requests.exceptions.RequestException:
            raise AuthenticationFailed('Error al verificar token')
        except Exception:
            raise AuthenticationFailed('Error de autenticación') 