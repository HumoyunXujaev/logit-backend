from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
import hashlib
import hmac
from django.conf import settings
from typing import Optional
import json
from django.utils import timezone

User = get_user_model()

class TelegramAuthBackend(BaseBackend):
    def authenticate(self, request, telegram_data=None) -> Optional[User]:
        """
        Authenticate user using Telegram WebApp data
        
        Args:
            request: HTTP request
            telegram_data: Dictionary with Telegram WebApp data
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        if not telegram_data:
            return None

        # Verify Telegram data authenticity
        if not self.verify_telegram_data(telegram_data):
            return None

        try:
            # Get user data
            user_data = json.loads(telegram_data.get('user', '{}'))
            telegram_id = str(user_data.get('id'))
            
            if not telegram_id:
                return None

            # Get or create user
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'username': user_data.get('username', ''),
                    'language_code': user_data.get('language_code', 'ru'),
                }
            )
            
            # Update last login
            if not created:
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])

            # Don't authenticate inactive users
            if not user.is_active:
                return None

            return user

        except Exception as e:
            # Log the error in production
            print(f"Authentication error: {e}")
            return None

    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(telegram_id=user_id)
        except User.DoesNotExist:
            return None

    def verify_telegram_data(self, telegram_data: dict) -> bool:
        """
        Verify authenticity of Telegram WebApp data
        
        Args:
            telegram_data: Dictionary with Telegram WebApp data
            
        Returns:
            bool: True if data is authentic, False otherwise
        """
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            if not bot_token:
                return False

            received_hash = telegram_data.get('hash')
            if not received_hash:
                return False

            # Remove hash from data to verify
            telegram_data_without_hash = telegram_data.copy()
            telegram_data_without_hash.pop('hash', None)

            # Sort data
            data_check_string = '\n'.join(
                f"{k}={v}" for k, v in sorted(telegram_data_without_hash.items())
            )

            # Create secret key
            secret_key = hmac.new(
                key=b'WebAppData',
                msg=bot_token.encode(),
                digestmod=hashlib.sha256
            ).digest()

            # Calculate hash
            calculated_hash = hmac.new(
                key=secret_key,
                msg=data_check_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()

            return calculated_hash == received_hash

        except Exception as e:
            print(f"Verification error: {e}")
            return False

    def validate_auth_data(self, auth_data: dict) -> bool:
        """
        Additional validation of authentication data
        
        Args:
            auth_data: Dictionary with authentication data
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            required_fields = ['id', 'first_name']
            user_data = json.loads(auth_data.get('user', '{}'))
            
            return all(user_data.get(field) for field in required_fields)
            
        except Exception:
            return False