from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def clean_old_notifications():
    """Remove notifications older than 30 days"""
    from core.models import Notification
    
    threshold = timezone.now() - timedelta(days=30)
    deleted_count = Notification.objects.filter(created_at__lt=threshold).delete()[0]
    
    logger.info(f"Cleaned {deleted_count} old notifications")

@shared_task
def check_expired_cargos():
    """Check for expired cargo listings and notify owners"""
    from cargo.models import Cargo
    from core.services.telegram import telegram_service
    
    threshold = timezone.now().date()
    expired_cargos = Cargo.objects.filter(
        status__in=['pending', 'manager_approved'],
        loading_date__lt=threshold
    )
    
    for cargo in expired_cargos:
        # Update cargo status
        cargo.status = Cargo.CargoStatus.EXPIRED
        cargo.save()
        
        # Notify owner if they exist
        if cargo.owner and cargo.owner.telegram_id:
            message = f"""
⚠️ <b>Груз просрочен</b>

<b>Груз:</b> {cargo.title}
<b>Маршрут:</b> {cargo.loading_point} ➡️ {cargo.unloading_point}
<b>Дата загрузки:</b> {cargo.loading_date.strftime('%d.%m.%Y')}

Статус груза изменен на "Просрочен".
"""
            telegram_service.send_notification.delay(
                cargo.owner.telegram_id,
                message
            )
    
    logger.info(f"Marked {expired_cargos.count()} cargos as expired")

@shared_task
def check_expiring_documents():
    """Check for vehicle documents that are about to expire and notify owners"""
    from vehicles.models import VehicleDocument
    from core.services.telegram import telegram_service
    
    # Check documents expiring in the next 7 days
    soon = timezone.now().date() + timedelta(days=7)
    expiring_docs = VehicleDocument.objects.filter(
        expiry_date__lte=soon,
        expiry_date__gte=timezone.now().date()
    ).select_related('vehicle', 'vehicle__owner')
    
    for doc in expiring_docs:
        owner = doc.vehicle.owner
        if owner and owner.telegram_id:
            days_left = (doc.expiry_date - timezone.now().date()).days
            
            message = f"""
⚠️ <b>Скоро истекает срок действия документа</b>

<b>Транспорт:</b> {doc.vehicle.registration_number}
<b>Документ:</b> {doc.get_type_display()}
<b>Название:</b> {doc.title}
<b>Срок действия:</b> {doc.expiry_date.strftime('%d.%m.%Y')}
<b>Осталось дней:</b> {days_left}

Пожалуйста, обновите документ до истечения срока.
"""
            telegram_service.send_notification.delay(
                owner.telegram_id,
                message
            )
    
    logger.info(f"Sent notifications for {expiring_docs.count()} expiring documents")