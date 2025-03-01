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
    """Send notifications for cargo status changes"""
    if created:
        return
        
    # We can't use tracker since it's not configured
    # Instead, we'll check for status changes based on the "_original_status" 
    # attribute which is set in pre_save in cargo/signals.py
    if hasattr(instance, '_original_status') and instance._original_status != instance.status:
        old_status = instance._original_status
        new_status = instance.status
        
        # Determine who should be notified
        recipients = []
        action = ""
        
        if new_status == 'pending_approval':
            # Notify managers
            recipients = User.objects.filter(
                role='manager',
                is_active=True,
                telegram_id__isnull=False
            )
            action = f"Новый груз требует проверки: {instance.title}"
            
        elif new_status == 'manager_approved':
            # Notify students
            recipients = User.objects.filter(
                role='student',
                is_active=True,
                telegram_id__isnull=False
            )
            action = f"Новый груз доступен: {instance.title}"
            
        elif new_status == 'assigned':
            # Notify carrier
            if instance.assigned_to and instance.assigned_to.telegram_id:
                recipients = [instance.assigned_to]
                action = f"Вам назначен груз: {instance.title}"

        # Send notifications via Telegram
        if recipients and action:
            for recipient in recipients:
                if recipient.telegram_id:
                    telegram_service.send_notification.delay(
                        recipient.telegram_id, 
                        telegram_service.format_cargo_notification(instance, action)
                    )

@receiver(post_save, sender=CarrierRequest)
def notify_carrier_request_status_change(sender, instance, created, **kwargs):
    """Send notifications for carrier request status changes"""
    if created:
        return
        
    if hasattr(instance, '_original_status') and instance._original_status != instance.status:
        old_status = instance._original_status
        new_status = instance.status
        
        recipients = []
        action = ""
        
        if new_status == 'assigned':
            if instance.carrier and instance.carrier.telegram_id:
                recipients = [instance.carrier]
                action = "Вам назначен груз"
                
        elif new_status in ['accepted', 'rejected']:
            if instance.assigned_by and instance.assigned_by.telegram_id:
                recipients = [instance.assigned_by]
                action = f"Перевозчик {'принял' if new_status == 'accepted' else 'отклонил'} назначенный груз"

        # Send notifications via Telegram
        if recipients and action:
            for recipient in recipients:
                if recipient.telegram_id:
                    telegram_service.send_notification.delay(
                        recipient.telegram_id,
                        telegram_service.format_carrier_notification(instance, action)
                    )