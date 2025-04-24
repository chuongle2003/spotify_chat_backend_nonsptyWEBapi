from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User

class PermissionTests(TestCase):
    def setUp(self):
        # Tạo các loại người dùng khác nhau
        self.client = APIClient()
        
        # Regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='password123'
        )
        
        # Staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            is_staff=True
        )
        
        # Content manager
        self.content_manager = User.objects.create_user(
            username='content',
            email='content@example.com',
            password='password123',
            is_staff=True,
            can_manage_content=True
        )
        
        # User manager
        self.user_manager = User.objects.create_user(
            username='usermanager',
            email='usermanager@example.com',
            password='password123',
            is_staff=True,
            can_manage_users=True
        )
        
        # Admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123'
        )
    
    def test_public_endpoint_access(self):
        """Test that anyone can access public endpoints"""
        url = reverse('public-users')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_permissions(self):
        """Test regular user permissions"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Can access their own profile
        url = reverse('user-detail', args=[self.regular_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cannot access admin endpoints
        url = reverse('admin-user-detail', args=[self.regular_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_staff_permissions(self):
        """Test staff permissions"""
        self.client.force_authenticate(user=self.staff_user)
        
        # Can access user endpoint
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cannot access user management
        url = reverse('usermanagement-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_content_manager_permissions(self):
        """Test content manager permissions"""
        self.client.force_authenticate(user=self.content_manager)
        
        # TODO: Add tests for content management endpoints
        # This will depend on the actual implementation of your music app
        pass
    
    def test_user_manager_permissions(self):
        """Test user manager permissions"""
        self.client.force_authenticate(user=self.user_manager)
        
        # Can access user management
        url = reverse('usermanagement-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Can toggle user active status
        url = reverse('usermanagement-toggle-active', args=[self.regular_user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cannot toggle staff status (only admin can)
        url = reverse('usermanagement-toggle-staff', args=[self.regular_user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_permissions(self):
        """Test admin permissions"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Can access everything
        url = reverse('usermanagement-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Can toggle staff status
        url = reverse('usermanagement-toggle-staff', args=[self.regular_user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Can set permissions
        url = reverse('usermanagement-set-permissions', args=[self.regular_user.id])
        data = {
            'can_manage_content': True,
            'can_manage_users': False,
            'can_manage_playlists': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the permissions were updated
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.can_manage_content)
        self.assertFalse(self.regular_user.can_manage_users)
        self.assertTrue(self.regular_user.can_manage_playlists)
