"""
Tests for Mini App Email Connection Endpoints

Tests both connect-email and OTP verification endpoints with:
- Happy path scenarios
- Authentication variants (Bearer token vs telegram_id)
- Validation errors
- Security features (rate limiting, OTP expiry, attempts)
"""
import hashlib
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.core import mail

from rest_framework.test import APIClient
from rest_framework import status

from .models import User, EmailOTPTelegramLink
from .jwt_service import UnifiedJWTService


class MiniAppConnectEmailTests(TestCase):
    """Tests for POST /api/mini-app/auth/connect-email/"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/mini-app/auth/connect-email/'
        
        # Create a test user with telegram_id
        self.telegram_id = '123456789'
        self.user = User.objects.create(
            telegram_id=self.telegram_id,
            email=f'tg_{self.telegram_id}@telegram.local',
            first_name='Test',
            last_name='User',
            login_method=User.LOGIN_METHOD_TELEGRAM,
            created_via=User.CREATED_VIA_TELEGRAM,
        )
        self.user.set_unusable_password()
        self.user.save()
        
        # Generate tokens for authenticated tests
        tokens = UnifiedJWTService.create_tokens(self.user)
        self.access_token = tokens['access']
    
    def test_connect_email_with_bearer_token_success(self):
        """Test connecting email with Bearer token authentication."""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'otp_sent')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        
        # Verify OTP was created
        otp_record = EmailOTPTelegramLink.objects.filter(
            email='newuser@example.com',
            telegram_id=self.telegram_id
        ).first()
        self.assertIsNotNone(otp_record)
        self.assertFalse(otp_record.is_expired)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verification code', mail.outbox[0].subject.lower())
    
    def test_connect_email_with_telegram_id_success(self):
        """Test connecting email with telegram_id in body (unauthenticated)."""
        data = {
            'email': 'another@example.com',
            'password': 'SecurePass456',
            'telegram_id': self.telegram_id
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'otp_sent')
        
        # Verify OTP was created
        otp_record = EmailOTPTelegramLink.objects.filter(
            email='another@example.com'
        ).first()
        self.assertIsNotNone(otp_record)
    
    def test_connect_email_auto_creates_user(self):
        """Test that endpoint auto-creates user for new telegram_id."""
        new_telegram_id = '987654321'
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass789',
            'telegram_id': new_telegram_id
        }
        
        # User shouldn't exist yet
        self.assertFalse(User.objects.filter(telegram_id=new_telegram_id).exists())
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User should now exist
        user = User.objects.get(telegram_id=new_telegram_id)
        self.assertEqual(user.login_method, User.LOGIN_METHOD_TELEGRAM)
        self.assertFalse(user.has_usable_password())
    
    def test_connect_email_missing_telegram_id_and_token(self):
        """Test error when neither Bearer token nor telegram_id provided."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Bearer token or telegram_id', response.data['detail'])
    
    def test_connect_email_invalid_bearer_token(self):
        """Test error with invalid Bearer token."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_here')
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_connect_email_weak_password(self):
        """Test validation error for weak password."""
        data = {
            'email': 'test@example.com',
            'password': 'weak',
            'telegram_id': self.telegram_id
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', str(response.data).lower())
    
    def test_connect_email_placeholder_email_rejected(self):
        """Test that placeholder emails are rejected."""
        data = {
            'email': 'tg_123@telegram.local',
            'password': 'SecurePass123',
            'telegram_id': self.telegram_id
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('placeholder', str(response.data).lower())
    
    def test_connect_email_duplicate_email_different_user(self):
        """Test error when email already belongs to another user."""
        # Create another user with an email
        other_user = User.objects.create(
            telegram_id='111222333',
            email='taken@example.com',
            first_name='Other',
            last_name='User'
        )
        
        data = {
            'email': 'taken@example.com',
            'password': 'SecurePass123',
            'telegram_id': self.telegram_id
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already registered', response.data['detail'])
    
    def test_connect_email_invalidates_previous_otp(self):
        """Test that requesting new OTP invalidates previous ones."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'telegram_id': self.telegram_id
        }
        
        # First request
        response1 = self.client.post(self.url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Get first OTP
        otp1 = EmailOTPTelegramLink.objects.filter(
            email='test@example.com',
            telegram_id=self.telegram_id
        ).first()
        
        # Second request
        response2 = self.client.post(self.url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Reload first OTP - should be marked as verified (invalidated)
        otp1.refresh_from_db()
        self.assertIsNotNone(otp1.verified_at)
    
    @patch('account.miniapp_views.send_mail')
    def test_connect_email_handles_email_failure(self, mock_send_mail):
        """Test graceful handling of email sending failure."""
        mock_send_mail.side_effect = Exception('SMTP error')
        
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'telegram_id': self.telegram_id
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Failed to send OTP', response.data['detail'])


class MiniAppVerifyOTPTests(TestCase):
    """Tests for POST /api/mini-app/auth/OTP/"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/mini-app/auth/OTP/'
        
        # Create test user
        self.telegram_id = '123456789'
        self.user = User.objects.create(
            telegram_id=self.telegram_id,
            email=f'tg_{self.telegram_id}@telegram.local',
            first_name='Test',
            last_name='User',
            login_method=User.LOGIN_METHOD_TELEGRAM,
        )
        self.user.set_unusable_password()
        self.user.save()
        
        # Create OTP record
        self.email = 'verify@example.com'
        self.otp_code = '123456'
        self.otp_hash = hashlib.sha256(self.otp_code.encode()).hexdigest()
        self.password = 'SecurePass123'
        
        from django.contrib.auth.hashers import make_password
        self.otp_record = EmailOTPTelegramLink.objects.create(
            user=self.user,
            email=self.email,
            code_hash=self.otp_hash,
            password=make_password(self.password),
            telegram_id=self.telegram_id,
            expires_at=timezone.now() + timedelta(minutes=10),
            attempts=0
        )
    
    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        data = {
            'email': self.email,
            'otp': self.otp_code
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Verify user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, self.email)
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.check_password(self.password))
        
        # Verify OTP was marked as used
        self.otp_record.refresh_from_db()
        self.assertIsNotNone(self.otp_record.verified_at)
    
    def test_verify_otp_invalid_code(self):
        """Test error with invalid OTP code."""
        data = {
            'email': self.email,
            'otp': '999999'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid OTP', response.data['detail'])
        self.assertEqual(response.data['attempts_remaining'], 4)
        
        # Verify attempts incremented
        self.otp_record.refresh_from_db()
        self.assertEqual(self.otp_record.attempts, 1)
    
    def test_verify_otp_expired(self):
        """Test error with expired OTP."""
        # Set OTP to expired
        self.otp_record.expires_at = timezone.now() - timedelta(minutes=1)
        self.otp_record.save()
        
        data = {
            'email': self.email,
            'otp': self.otp_code
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', response.data['detail'])
    
    def test_verify_otp_too_many_attempts(self):
        """Test error when attempts limit exceeded."""
        # Set attempts to max
        self.otp_record.attempts = 5
        self.otp_record.save()
        
        data = {
            'email': self.email,
            'otp': self.otp_code
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Too many', response.data['detail'])
    
    def test_verify_otp_email_not_found(self):
        """Test error when no OTP found for email."""
        data = {
            'email': 'nonexistent@example.com',
            'otp': '123456'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_verify_otp_invalid_format(self):
        """Test validation error for invalid OTP format."""
        data = {
            'email': self.email,
            'otp': 'abc123'  # Contains letters
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verify_otp_updates_login_method(self):
        """Test that login_method is updated after email verification."""
        data = {
            'email': self.email,
            'otp': self.otp_code
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User should now have BOTH login method
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_method, User.LOGIN_METHOD_BOTH)
    
    def test_verify_otp_allows_simultaneous_login(self):
        """Test that user can login via both email and telegram after linking."""
        # Verify OTP
        data = {
            'email': self.email,
            'otp': self.otp_code
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user
        self.user.refresh_from_db()
        
        # Should be able to authenticate with password
        self.assertTrue(self.user.check_password(self.password))
        
        # Should still have telegram_id
        self.assertEqual(self.user.telegram_id, self.telegram_id)
        
        # Can generate tokens (for both login methods)
        tokens = UnifiedJWTService.create_tokens(self.user)
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)


class MiniAppEdgeCaseTests(TestCase):
    """Tests for edge cases and security features."""
    
    def setUp(self):
        self.client = APIClient()
        self.connect_url = '/api/mini-app/auth/connect-email/'
        self.verify_url = '/api/mini-app/auth/OTP/'
    
    def test_idempotent_email_connection(self):
        """Test that requesting OTP multiple times is idempotent."""
        telegram_id = '123456789'
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'telegram_id': telegram_id
        }
        
        # First request
        response1 = self.client.post(self.connect_url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        count_after_first = EmailOTPTelegramLink.objects.filter(
            email='test@example.com',
            verified_at__isnull=True
        ).count()
        
        # Second request
        response2 = self.client.post(self.connect_url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Should still only have one active OTP
        count_after_second = EmailOTPTelegramLink.objects.filter(
            email='test@example.com',
            verified_at__isnull=True
        ).count()
        
        self.assertEqual(count_after_first, count_after_second)
    
    def test_otp_hash_security(self):
        """Test that OTP is stored hashed, not in plaintext."""
        telegram_id = '123456789'
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'telegram_id': telegram_id
        }
        
        response = self.client.post(self.connect_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get OTP record
        otp_record = EmailOTPTelegramLink.objects.filter(
            email='test@example.com'
        ).first()
        
        # code_hash should be a hash (64 chars for SHA256)
        self.assertEqual(len(otp_record.code_hash), 64)
        self.assertTrue(otp_record.code_hash.isalnum())
    
    def test_password_hash_security(self):
        """Test that password is stored hashed in OTP record."""
        telegram_id = '123456789'
        password = 'SecurePass123'
        data = {
            'email': 'test@example.com',
            'password': password,
            'telegram_id': telegram_id
        }
        
        response = self.client.post(self.connect_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get OTP record
        otp_record = EmailOTPTelegramLink.objects.filter(
            email='test@example.com'
        ).first()
        
        # Password should be hashed (Django password hash format)
        self.assertNotEqual(otp_record.password, password)
        self.assertTrue(otp_record.password.startswith('pbkdf2_sha256$'))
