from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Cargo, CarrierRequest
from core.services.telegram import telegram_service
from django.db import transaction

User = get_user_model()

@receiver(post_save, sender=Cargo)
def notify_cargo_changes(sender, instance, created, **kwargs):
    """Send notifications for cargo creation and changes"""
    # Skip if this is not a change or the transaction is being managed elsewhere
    if transaction.get_connection().in_atomic_block and not created:
        return
        
    # Determine action and recipients based on status and event
    if created:
        action = f"Новый груз создан: {instance.title}"
        
        # Notify different users based on cargo status
        if instance.status == Cargo.CargoStatus.PENDING_APPROVAL:
            # Notify managers about new cargo requiring approval
            managers = User.objects.filter(role='manager', is_active=True)
            if managers.exists():
                for manager in managers:
                    if manager.telegram_id:
                        telegram_service.send_notification.delay(
                            manager.telegram_id,
                            telegram_service.format_cargo_notification(instance, action)
                        )
            
        elif instance.status == Cargo.CargoStatus.PENDING:
            # Notify students about new cargo
            students = User.objects.filter(role='student', is_active=True)
            if students.exists():
                for student in students:
                    if student.telegram_id:
                        telegram_service.send_notification.delay(
                            student.telegram_id, 
                            telegram_service.format_cargo_notification(instance, action)
                        )
            
    elif hasattr(instance, '_original_status') and instance._original_status != instance.status:
        old_status = instance._original_status
        new_status = instance.status
        
        action = f"Статус груза изменен с {old_status} на {new_status}: {instance.title}"
        
        # Notify owner
        if instance.owner and instance.owner.telegram_id:
            telegram_service.send_notification.delay(
                instance.owner.telegram_id,
                telegram_service.format_cargo_notification(instance, action)
            )
            
        # Notify assigned carrier if status becomes assigned
        if new_status == Cargo.CargoStatus.ASSIGNED and instance.assigned_to and instance.assigned_to.telegram_id:
            telegram_service.send_notification.delay(
                instance.assigned_to.telegram_id,
                telegram_service.format_cargo_notification(instance, "Вам назначен груз")
            )
            
        # Notify managing student about status changes
        if instance.managed_by and instance.managed_by.telegram_id:
            telegram_service.send_notification.delay(
                instance.managed_by.telegram_id,
                telegram_service.format_cargo_notification(instance, action)
            )
            
        # Notify all students when cargo becomes manager_approved
        if new_status == Cargo.CargoStatus.MANAGER_APPROVED:
            students = User.objects.filter(role='student', is_active=True)
            if students.exists():
                for student in students:
                    if student.telegram_id:
                        telegram_service.send_notification.delay(
                            student.telegram_id,
                            telegram_service.format_cargo_notification(instance, "Новый груз доступен")
                        )

@receiver(pre_save, sender=Cargo)
def store_original_status(sender, instance, **kwargs):
    """Store original status before save for comparison in post_save"""
    if instance.pk:
        try:
            instance._original_status = Cargo.objects.get(pk=instance.pk).status
        except Cargo.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_delete, sender=Cargo)
def notify_cargo_deletion(sender, instance, **kwargs):
    """Send notifications when cargo is deleted"""
    action = f"Груз удален: {instance.title}"
    
    # Notify owner
    if instance.owner and instance.owner.telegram_id:
        telegram_service.send_notification.delay(
            instance.owner.telegram_id, 
            telegram_service.format_cargo_notification(instance, action)
        )
    
    # Notify carrier if assigned
    if instance.assigned_to and instance.assigned_to.telegram_id:
        telegram_service.send_notification.delay(
            instance.assigned_to.telegram_id,
            telegram_service.format_cargo_notification(instance, action)
        )
    
    # Notify managing student
    if instance.managed_by and instance.managed_by.telegram_id:
        telegram_service.send_notification.delay(
            instance.managed_by.telegram_id,
            telegram_service.format_cargo_notification(instance, action)
        )

@receiver(post_save, sender=CarrierRequest)
def notify_carrier_request_changes(sender, instance, created, **kwargs):
    """Send notifications for carrier request creation and changes"""
    if created:
        action = "Новая заявка от перевозчика"
        
        # Notify students about new carrier request
        students = User.objects.filter(role='student', is_active=True)
        if students.exists():
            for student in students:
                if student.telegram_id:
                    telegram_service.send_notification.delay(
                        student.telegram_id,
                        telegram_service.format_carrier_notification(instance, action)
                    )
            
    elif hasattr(instance, '_original_status') and instance._original_status != instance.status:
        old_status = instance._original_status
        new_status = instance.status
        
        action = f"Статус заявки изменен с {old_status} на {new_status}"
        
        # Notify carrier about status changes
        if instance.carrier and instance.carrier.telegram_id:
            telegram_service.send_notification.delay(
                instance.carrier.telegram_id,
                telegram_service.format_carrier_notification(instance, action)
            )
            
        # Notify assigning student if request was assigned
        if instance.assigned_by and instance.assigned_by.telegram_id:
            telegram_service.send_notification.delay(
                instance.assigned_by.telegram_id,
                telegram_service.format_carrier_notification(instance, action)
            )
                
        # Notify cargo owner if request was accepted
        if new_status == CarrierRequest.RequestStatus.ACCEPTED and instance.assigned_cargo and instance.assigned_cargo.owner and instance.assigned_cargo.owner.telegram_id:
            telegram_service.send_notification.delay(
                instance.assigned_cargo.owner.telegram_id,
                telegram_service.format_carrier_notification(instance, "Перевозчик принял вашу заявку")
            )

@receiver(pre_save, sender=CarrierRequest)
def store_carrier_request_original_status(sender, instance, **kwargs):
    """Store original status before save for comparison in post_save"""
    if instance.pk:
        try:
            instance._original_status = CarrierRequest.objects.get(pk=instance.pk).status
        except CarrierRequest.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_delete, sender=CarrierRequest)
def notify_carrier_request_deletion(sender, instance, **kwargs):
    """Send notifications when carrier request is deleted"""
    action = f"Заявка перевозчика удалена"
    
    # Notify carrier
    if instance.carrier and instance.carrier.telegram_id:
        telegram_service.send_notification.delay(
            instance.carrier.telegram_id,
            telegram_service.format_carrier_notification(instance, action)
        )
    
    # Notify assigning student
    if instance.assigned_by and instance.assigned_by.telegram_id:
        telegram_service.send_notification.delay(
            instance.assigned_by.telegram_id,
            telegram_service.format_carrier_notification(instance, action)
        )
    
    # Notify cargo owner if request was assigned to a cargo
    if instance.assigned_cargo and instance.assigned_cargo.owner and instance.assigned_cargo.owner.telegram_id:
        telegram_service.send_notification.delay(
            instance.assigned_cargo.owner.telegram_id,
            telegram_service.format_carrier_notification(instance, action)
        )