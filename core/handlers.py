from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cargo.models import Cargo, CarrierRequest
from users.models import User
from core.services.telegram import telegram_service

@receiver(post_save, sender=Cargo)
def handle_cargo_notification(sender, instance, created, **kwargs):
    """Handle cargo notifications"""
    if created:
        action = "Новый груз создан"
    else:
        if not instance.tracker.has_changed('status'):
            return
        action = f"Статус груза изменен на {instance.get_status_display()}"

    # Determine recipients based on status and role
    recipients = []
    
    if instance.status == 'pending_approval':
        # Notify managers about new cargo
        recipients = User.objects.filter(role='manager', is_active=True)
    elif instance.status == 'manager_approved':
        # Notify students about approved cargo
        recipients = User.objects.filter(role='student', is_active=True)
    elif instance.status == 'assigned':
        # Notify assigned carrier
        if instance.assigned_to:
            recipients = [instance.assigned_to]
    
    # Send notifications
    notifications = [
        {
            'telegram_id': user.telegram_id,
            'message': telegram_service.format_cargo_message(action, instance)
        }
        for user in recipients if user.telegram_id
    ]
    
    if notifications:
        telegram_service.send_bulk_notifications.delay(notifications)

@receiver(post_save, sender=CarrierRequest)
def handle_carrier_request_notification(sender, instance, created, **kwargs):
    """Handle carrier request notifications"""
    if created:
        action = "Новая заявка от перевозчика"
    else:
        if not instance.tracker.has_changed('status'):
            return
        action = f"Статус заявки изменен на {instance.get_status_display()}"

    # Determine recipients
    recipients = []
    
    if instance.status == 'pending':
        # Notify students about new request
        recipients = User.objects.filter(role='student', is_active=True)
    elif instance.status == 'assigned':
        # Notify carrier about assignment
        recipients = [instance.carrier]
    elif instance.status in ['accepted', 'rejected']:
        # Notify assigning student
        if instance.assigned_by:
            recipients = [instance.assigned_by]

    # Send notifications
    notifications = [
        {
            'telegram_id': user.telegram_id,
            'message': telegram_service.format_carrier_request_message(action, instance)
        }
        for user in recipients if user.telegram_id
    ]
    
    if notifications:
        telegram_service.send_bulk_notifications.delay(notifications)

@receiver(post_delete, sender=Cargo)
def handle_cargo_deletion(sender, instance, **kwargs):
    """Handle cargo deletion notifications"""
    # Notify cargo owner
    if instance.owner and instance.owner.telegram_id:
        message = f"""
❌ <b>Груз удален</b>

<b>Груз:</b> {instance.title}
<b>Маршрут:</b> {instance.loading_point} ➡️ {instance.unloading_point}
"""
        telegram_service.send_notification.delay(
            instance.owner.telegram_id,
            message
        )