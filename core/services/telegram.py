from typing import List, Dict, Any, Tuple, Union
import logging
import requests
from django.conf import settings
from celery import shared_task

logger = logging.getLogger(__name__)

class TelegramNotificationService:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id: str, message: str) -> bool:
        """Send message to a telegram chat"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False

    @staticmethod
    @shared_task
    def send_notification(telegram_id: str, message: str) -> bool:
        """Celery task to send notification to a user"""
        service = TelegramNotificationService()
        return service.send_message(telegram_id, message)

    @staticmethod
    @shared_task
    def send_bulk_messages(messages: List[Union[Dict[str, str], Tuple[str, str]]]) -> None:
        """Send multiple messages via Celery"""
        service = TelegramNotificationService()
        for msg in messages:
            # Handle both dict and tuple formats
            if isinstance(msg, dict):
                telegram_id = msg.get("telegram_id")
                message = msg.get("message")
            elif isinstance(msg, tuple) and len(msg) >= 2:
                telegram_id, message = msg[0], msg[1]
            else:
                logger.error(f"Invalid message format: {msg}")
                continue
                
            if telegram_id and message:
                service.send_message(telegram_id, message)

    def format_cargo_notification(self, cargo: Any, action: str) -> str:
        """Format a cargo notification message"""
        return f"""
🚛 <b>{action}</b>

<b>Груз:</b> {cargo.title}
<b>Маршрут:</b> {cargo.loading_point} ➡️ {cargo.unloading_point}
<b>Вес:</b> {cargo.weight} т
<b>Тип транспорта:</b> {cargo.get_vehicle_type_display()}
<b>Статус:</b> {cargo.get_status_display()}

👉 Перейдите в приложение для подробностей
"""

    def format_carrier_notification(self, request: Any, action: str) -> str:
        """Format a carrier request notification message"""
        return f"""
🚚 <b>{action}</b>

<b>Перевозчик:</b> {request.carrier.get_full_name()}
<b>Транспорт:</b> {request.vehicle.registration_number}
<b>Маршрут:</b> {request.loading_point} ➡️ {request.unloading_point}
<b>Статус:</b> {request.get_status_display()}

👉 Перейдите в приложение для подробностей
"""

    def notify_users(self, recipients: List[Any], message: str) -> None:
        """Send notification to multiple users"""
        # Create list of (telegram_id, message) tuples for users with telegram_id
        messages = [
            (user.telegram_id, message)
            for user in recipients
            if user.telegram_id
        ]
        
        # Send messages if we have any recipients
        if messages:
            self.send_bulk_messages.delay(messages)


telegram_service = TelegramNotificationService()