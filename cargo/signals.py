from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Cargo, CarrierRequest
from core.services.telegram import telegram_service
import asyncio

User = get_user_model()

@receiver(post_save, sender=Cargo)
def notify_cargo_status_change(sender, instance, created, **kwargs):
    """Send notifications for cargo status changes"""
    if created:
        return
        
    if instance.tracker.has_changed('status'):
        old_status = instance.tracker.previous('status')
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
            messages = [
                (user.telegram_id, telegram_service.format_cargo_notification(instance, action))
                for user in recipients
            ]
            asyncio.create_task(telegram_service.send_bulk_messages(messages))

@receiver(post_save, sender=CarrierRequest)
def notify_carrier_request_status_change(sender, instance, created, **kwargs):
    """Send notifications for carrier request status changes"""
    if created:
        return
        
    if instance.tracker.has_changed('status'):
        old_status = instance.tracker.previous('status')
        new_status = instance.status
        
        recipients = []
        action = ""
        
        if new_status == 'assigned':
            if instance.carrier and instance.carrier.telegram_id:
                recipients = [instance.carrier]
                action = "Вашей заявке назначен груз"
                
        elif new_status in ['accepted', 'rejected']:
            if instance.assigned_by and instance.assigned_by.telegram_id:
                recipients = [instance.assigned_by]
                action = f"Перевозчик {'принял' if new_status == 'accepted' else 'отклонил'} назначенный груз"

        # Send notifications via Telegram
        if recipients and action:
            messages = [
                (user.telegram_id, telegram_service.format_carrier_notification(instance, action))
                for user in recipients
            ]
            asyncio.create_task(telegram_service.send_bulk_messages(messages))