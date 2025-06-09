from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user(self):
        """Test creación de usuario básico"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, User.Role.RECEPCIONISTA)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_admin_user(self):
        """Test creación de usuario administrador"""
        user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )
        self.assertEqual(user.role, User.Role.ADMIN)

class AuthenticationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_login_success(self):
        """Test login exitoso"""
        url = reverse('user-login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        """Test login con credenciales inválidas"""
        url = reverse('user-login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_unauthorized(self):
        """Test que solo admin puede crear usuarios"""
        url = reverse('user-list')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'password2': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list_authenticated(self):
        """Test que usuarios autenticados pueden ver la lista"""
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password(self):
        """Test cambio de contraseña"""
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        url = reverse('user-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newtestpass123',
            'new_password2': 'newtestpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la contraseña cambió
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newtestpass123')) 