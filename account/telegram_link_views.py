"""
Telegram Link Views

Endpoints for linking web account to Telegram bot.
Flow:
1. User clicks "Link Telegram" button on web
2. Server creates signed deep link
3. User opens Telegram bot with deep link
4. Bot webhook verifies payload and links account
"""
import logging
import uuid
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, TelegramLinkNonce, AuthAuditLog
from .miniapp_views import CustomJWTAuthentication

logger = logging.getLogger(__name__)


class TelegramLinkCreateView(APIView):
    """
    POST /api/mini-app/auth/connect-telegram/link/
    
    Create a deep link for linking web account to Telegram.
    User must be authenticated via web (JWT).
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="""
        Create a deep link to connect your web account to Telegram.
        
        **How it works:**
        1. Call this endpoint from web (with JWT token)
        2. Receive a deep link (t.me/YourBot?start=...)
        3. Open the link in Telegram
        4. Bot will automatically link your accounts
        
        **Link expires in 10 minutes.**
        """,
        responses={
            200: openapi.Response(
                description="Deep link created successfully",
                examples={
                    "application/json": {
                        "deep_link": "https://t.me/mazzaly_bot?start=ABC123XYZ",
                        "expires_in": 600,
                        "expires_at": "2025-11-04T12:00:00Z"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request - user already linked",
                examples={
                    "application/json": {
                        "detail": "Your account is already linked to Telegram"
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        },
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT Access Token",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        tags=['Telegram Link']
    )
    def post(self, request):
        user = request.user
        
        # Check if user already has telegram_id
        if user.telegram_id:
            return Response(
                {
                    'detail': 'Your account is already linked to Telegram',
                    'telegram_id': user.telegram_id
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Invalidate any existing unused nonces for this user
        TelegramLinkNonce.objects.filter(
            user=user,
            used=False
        ).update(used=True, used_at=timezone.now())
        
        # Create new nonce with 10 min expiry
        expires_at = timezone.now() + timedelta(minutes=10)
        nonce = TelegramLinkNonce.objects.create(
            user=user,
            expires_at=expires_at
        )
        
        # Create signed payload (use nonce as token)
        payload = str(nonce.nonce)
        
        # DEBUG: Log nonce creation
        logger.info(f"Created nonce: {nonce.nonce} for user {user.email}, expires at {expires_at}")
        
        # Get bot username from settings
        bot_username = settings.TELEGRAM_BOT_USERNAME
        logger.info(f"Bot username from settings: {bot_username}")
        
        # Create deep link
        deep_link = f"https://t.me/{bot_username}?start={payload}"
        logger.info(f"Generated deep link: {deep_link}")
        
        # Log action
        AuthAuditLog.objects.create(
            user=user,
            action='telegram_link_requested',
            platform='web',
            email=user.email,
            ip_address=self._get_client_ip(request),
            success=True
        )
        
        logger.info(f"Telegram link created for user {user.id} (email: {user.email})")
        
        return Response(
            {
                'deep_link': deep_link,
                'expires_in': 600,  # seconds
                'expires_at': expires_at.isoformat()
            },
            status=status.HTTP_200_OK
        )
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class TelegramWebhookView(APIView):
    """
    POST /api/mini-app/auth/telegram-webhook/
    
    Telegram bot webhook endpoint.
    Handles /start command with link payload.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="""
        Telegram bot webhook endpoint.
        
        **This endpoint is called by Telegram servers, not by users directly.**
        
        Processes /start command and links accounts if payload is valid.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'update_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'message': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'from': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'text': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Webhook processed successfully",
                examples={
                    "application/json": {
                        "ok": True
                    }
                }
            ),
        },
        tags=['Telegram Link']
    )
    def post(self, request):
        """
        Handle Telegram webhook update.
        
        Expected format:
        {
            "update_id": 123,
            "message": {
                "message_id": 456,
                "from": {
                    "id": 123456789,
                    "first_name": "John",
                    "username": "johndoe"
                },
                "text": "/start ABC123XYZ"
            }
        }
        """
        try:
            data = request.data
            
            # DEBUG: Log incoming webhook data
            logger.info(f"Webhook received: {data}")
            
            # Extract message
            message = data.get('message', {})
            if not message:
                # Not a message update, ignore
                logger.info("No message in update, ignoring")
                return Response({'ok': True}, status=status.HTTP_200_OK)
            
            # Get user info from Telegram
            telegram_user = message.get('from', {})
            telegram_user_id = str(telegram_user.get('id', ''))
            telegram_username = telegram_user.get('username', '')
            telegram_first_name = telegram_user.get('first_name', '')
            telegram_last_name = telegram_user.get('last_name', '')
            
            if not telegram_user_id:
                logger.warning("Webhook received without telegram user_id")
                return Response({'ok': True}, status=status.HTTP_200_OK)
            
            # Check if it's a /start command
            text = message.get('text', '')
            logger.info(f"Message text: {text}")
            
            if not text.startswith('/start '):
                # Not a start command with payload, ignore
                logger.info("Not a /start command with payload, ignoring")
                return Response({'ok': True}, status=status.HTTP_200_OK)
            
            # Extract payload (everything after "/start ")
            payload = text[7:].strip()  # Remove "/start "
            logger.info(f"Extracted payload: {payload}")
            
            if not payload:
                # Empty payload, ignore
                logger.info("Empty payload, ignoring")
                return Response({'ok': True}, status=status.HTTP_200_OK)
            
            # Verify and process payload
            result = self._process_link_payload(
                payload=payload,
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
                telegram_first_name=telegram_first_name,
                telegram_last_name=telegram_last_name
            )
            
            if result['success']:
                # Send success message to user via Telegram API
                self._send_telegram_message(
                    chat_id=telegram_user_id,
                    text=result['message']
                )
                
                logger.info(f"Successfully linked user {result['user_id']} to telegram {telegram_user_id}")
            else:
                # Send error message
                self._send_telegram_message(
                    chat_id=telegram_user_id,
                    text=result['message']
                )
                
                logger.warning(f"Failed to link telegram {telegram_user_id}: {result['message']}")
            
            return Response({'ok': True}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing Telegram webhook: {str(e)}", exc_info=True)
            # Still return 200 to Telegram so it doesn't retry
            return Response({'ok': True}, status=status.HTTP_200_OK)
    
    def _process_link_payload(self, payload, telegram_user_id, telegram_username, 
                               telegram_first_name, telegram_last_name):
        """
        Verify payload and link account.
        
        Returns dict with 'success', 'message', and optionally 'user_id'.
        """
        try:
            # Try to parse payload as UUID (nonce)
            logger.info(f"Processing payload: {payload}")
            try:
                nonce_uuid = uuid.UUID(payload)
                logger.info(f"Parsed UUID: {nonce_uuid}")
            except ValueError as e:
                logger.warning(f"Invalid UUID format: {payload}, error: {e}")
                return {
                    'success': False,
                    'message': '❌ Invalid link. Please request a new link from the website.'
                }
            
            # Find nonce in database
            try:
                nonce = TelegramLinkNonce.objects.get(nonce=nonce_uuid)
                logger.info(f"Found nonce in DB: {nonce.nonce}, user: {nonce.user.email}")
            except TelegramLinkNonce.DoesNotExist:
                logger.warning(f"Nonce not found in DB: {nonce_uuid}")
                # Check if any nonces exist for debugging
                nonce_count = TelegramLinkNonce.objects.count()
                logger.info(f"Total nonces in DB: {nonce_count}")
                return {
                    'success': False,
                    'message': '❌ Link not found. Please request a new link from the website.'
                }
            
            # Check if already used
            if nonce.used:
                return {
                    'success': False,
                    'message': '❌ This link has already been used. Please request a new link.'
                }
            
            # Check if expired
            if nonce.is_expired:
                return {
                    'success': False,
                    'message': '❌ Link has expired. Please request a new link from the website.'
                }
            
            # Get user
            user = nonce.user
            
            # Check if user already has telegram_id
            if user.telegram_id:
                # Mark nonce as used anyway
                nonce.used = True
                nonce.used_at = timezone.now()
                nonce.telegram_user_id = telegram_user_id
                nonce.save()
                
                return {
                    'success': False,
                    'message': f'ℹ️ Your account is already linked to Telegram (ID: {user.telegram_id}).'
                }
            
            # Check if this telegram_id is already used by another user
            existing_user = User.objects.filter(telegram_id=telegram_user_id).first()
            if existing_user:
                return {
                    'success': False,
                    'message': '❌ This Telegram account is already linked to another user.'
                }
            
            # All checks passed - link the account
            with transaction.atomic():
                # Update user
                user.telegram_id = telegram_user_id
                user.telegram_username = telegram_username
                user.telegram_first_name = telegram_first_name
                user.telegram_last_name = telegram_last_name
                user.telegram_linked_at = timezone.now()
                
                # Update login_method if it was email-only
                if user.login_method == User.LOGIN_METHOD_EMAIL:
                    user.login_method = User.LOGIN_METHOD_BOTH
                
                user.save()
                
                # Mark nonce as used
                nonce.used = True
                nonce.used_at = timezone.now()
                nonce.telegram_user_id = telegram_user_id
                nonce.save()
                
                # Log action
                AuthAuditLog.objects.create(
                    user=user,
                    action='telegram_linked',
                    platform='telegram',
                    telegram_id=telegram_user_id,
                    email=user.email,
                    success=True
                )
            
            return {
                'success': True,
                'message': f'✅ Success! Your Telegram account has been linked to {user.email}. You can now access Mazzaly from both web and Telegram!',
                'user_id': user.id
            }
            
        except Exception as e:
            logger.error(f"Error processing link payload: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': '❌ An error occurred. Please try again or contact support.'
            }
    
    def _send_telegram_message(self, chat_id, text):
        """
        Send a message to Telegram user via Bot API.
        """
        try:
            import requests
            
            bot_token = settings.TELEGRAM_BOT_TOKEN
            if not bot_token:
                logger.error("TELEGRAM_BOT_TOKEN not configured")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False
