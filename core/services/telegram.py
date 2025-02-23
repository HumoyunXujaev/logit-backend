import logging
from typing import List, Optional
from telegram.ext import Application
from telegram import Bot
from django.conf import settings
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor
import telegram.error
from users.models import User
from cargo.models import Cargo, CarrierRequest

logger = logging.getLogger(__name__)

class TelegramNotificationService:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def _send_message_sync(
        self,
        chat_id: str,
        message: str,
        silent: bool = False
    ) -> bool:
        """Send message synchronously using python-telegram-bot"""
        try:
            bot = Bot(token=self.token)
            bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML',
                disable_notification=silent
            )
            return True
        except telegram.error.TelegramError as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to {chat_id}: {str(e)}")
            return False

    def send_message(
        self,
        chat_id: str,
        message: str,
        silent: bool = False
    ) -> bool:
        """Send message using thread pool"""
        try:
            future = self.executor.submit(
                self._send_message_sync,
                chat_id,
                message,
                silent
            )
            return future.result(timeout=10)  # 10 second timeout
        except Exception as e:
            logger.error(f"Error in send_message thread: {str(e)}")
            return False

    def send_bulk_messages(
        self,
        messages: List[tuple[str, str]],
        rate_limit: int = 30
    ) -> None:
        """Send multiple messages with rate limiting"""
        from time import sleep
        
        for chat_id, message in messages:
            # Rate limit: max 30 messages per second
            if not cache.add(f'telegram_ratelimit_{chat_id}', 1, timeout=1):
                sleep(1 / rate_limit)
                
            self.send_message(chat_id, message)

    def format_cargo_notification(self, cargo: 'Cargo', action: str) -> str:
        """Format cargo notification message"""
        return f"""
🚛 <b>Уведомление о грузе</b>

{action}

<b>Груз:</b> {cargo.title}
<b>Маршрут:</b> {cargo.loading_point} ➡️ {cargo.unloading_point}
<b>Вес:</b> {cargo.weight} т
{f'<b>Объем:</b> {cargo.volume} м³' if cargo.volume else ''}
<b>Тип транспорта:</b> {cargo.get_vehicle_type_display()}
<b>Оплата:</b> {cargo.get_payment_method_display()}
{f'<b>Цена:</b> {cargo.price} ₽' if cargo.price else ''}

👉 Перейдите в приложение для подробностей
"""

    def format_carrier_notification(
        self,
        carrier_request: 'CarrierRequest',
        action: str
    ) -> str:
        """Format carrier request notification message"""
        return f"""
🚚 <b>Уведомление о заявке перевозчика</b>

{action}

<b>Перевозчик:</b> {carrier_request.carrier.get_full_name()}
<b>Транспорт:</b> {carrier_request.vehicle.registration_number}
<b>Маршрут:</b> {carrier_request.loading_point} ➡️ {carrier_request.unloading_point}
<b>Дата готовности:</b> {carrier_request.ready_date.strftime('%d.%m.%Y')}

👉 Перейдите в приложение для подробностей
"""

    def format_verification_notification(
        self,
        user: 'User',
        action: str
    ) -> str:
        """Format verification notification message"""
        return f"""
✅ <b>Уведомление о верификации</b>

{action}

<b>Пользователь:</b> {user.get_full_name()}
<b>Статус:</b> {'Верифицирован' if user.is_verified else 'Ожидает проверки'}

👉 Перейдите в приложение для подробностей
"""

telegram_service = TelegramNotificationService()