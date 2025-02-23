from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from users.models import User
from .models import Notification
from cargo.models import Cargo, CarrierRequest
from .services.telegram import TelegramNotificationService
import asyncio

import logging
telegram_service = TelegramNotificationService()


logger = logging.getLogger(__name__)

@receiver(post_save, sender=Notification)
def send_telegram_notification(sender, instance, created, **kwargs):
    """Send notification to Telegram when new notification is created"""
    if not created:
        return
        
    try:
        # Get the related content object (Cargo or CarrierRequest)
        content_object = instance.content_object
        
        # Skip if no content object
        if not content_object:
            return
            
        # Format message based on content type
        if isinstance(content_object, Cargo):
            message = telegram_service.format_cargo_notification(
                content_object,
                instance.message
            )
        elif isinstance(content_object, CarrierRequest):
            message = telegram_service.format_carrier_notification(
                content_object,
                instance.message
            )
        else:
            message = instance.message
            
        # Get user's telegram ID
        telegram_id = instance.user.telegram_id
        
        # Send message asynchronously
        asyncio.create_task(
            telegram_service.send_message(telegram_id, message)
        )
        
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {str(e)}")

@receiver(post_save, sender=Cargo)
def notify_cargo_status_change(sender, instance, created, **kwargs):
    """Create notifications for cargo status changes"""
    if created:
        return
        
    if instance.tracker.has_changed('status'):
        old_status = instance.tracker.previous('status')
        new_status = instance.status
        
        # Determine who should be notified
        recipients = []
        
        if new_status == 'pending_approval':
            # Notify managers
            recipients = User.objects.filter(role='manager', is_active=True)
            message = f"Новый груз требует проверки: {instance.title}"
            
        elif new_status == 'manager_approved':
            # Notify students
            recipients = User.objects.filter(role='student', is_active=True)
            message = f"Новый груз доступен: {instance.title}"
            
        elif new_status == 'assigned':
            # Notify carrier
            recipients = [instance.assigned_to]
            message = f"Вам назначен груз: {instance.title}"
            
        # Create notifications
        for recipient in recipients:
            Notification.objects.create(
                user=recipient,
                type='cargo',
                message=message,
                content_object=instance
            )