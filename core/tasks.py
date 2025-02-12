import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import telegram
from .models import (
    TelegramGroup, TelegramMessage,
    Notification, SearchFilter
)
from cargo.models import Cargo

logger = logging.getLogger(__name__)

@shared_task
def sync_telegram_groups():
    """
    Synchronize messages from Telegram groups
    """
    try:
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        for group in TelegramGroup.objects.filter(is_active=True):
            try:
                # Get updates from telegram
                updates = bot.get_updates(offset=-1, timeout=30)
                
                for update in updates:
                    if not update.message:
                        continue
                    
                    # Skip if message already exists
                    if TelegramMessage.objects.filter(
                        telegram_id=str(update.message.message_id)
                    ).exists():
                        continue
                    
                    # Create new message
                    TelegramMessage.objects.create(
                        telegram_id=str(update.message.message_id),
                        group=group,
                        message_text=update.message.text
                    )
                
                # Update last sync time
                group.last_sync = timezone.now()
                group.save()
                
            except Exception as e:
                logger.error(
                    f"Error syncing group {group.name}: {str(e)}"
                )
                continue
            
    except Exception as e:
        logger.error(f"Error in sync_telegram_groups: {str(e)}")
        raise

@shared_task
def process_telegram_messages():
    """
    Process unprocessed Telegram messages and create cargo entries
    """
    try:
        messages = TelegramMessage.objects.filter(
            processed=False
        ).select_related('group')
        
        for message in messages:
            try:
                with transaction.atomic():
                    # Extract cargo information from message
                    cargo_data = parse_cargo_message(message.message_text)
                    
                    if cargo_data:
                        # Create cargo entry
                        cargo = Cargo.objects.create(
                            source_type='telegram',
                            source_id=message.telegram_id,
                            **cargo_data
                        )
                        
                        message.cargo = cargo
                        message.processed = True
                        message.processed_at = timezone.now()
                        message.save()
                        
                        # Notify users with matching search filters
                        notify_matching_users.delay(cargo.id)
                    
            except Exception as e:
                logger.error(
                    f"Error processing message {message.telegram_id}: {str(e)}"
                )
                continue
                
    except Exception as e:
        logger.error(f"Error in process_telegram_messages: {str(e)}")
        raise

@shared_task
def notify_matching_users(cargo_id):
    """
    Notify users with matching search filters about new cargo
    """
    try:
        cargo = Cargo.objects.get(id=cargo_id)
        
        # Get all active search filters
        filters = SearchFilter.objects.filter(
            notifications_enabled=True
        ).select_related('user')
        
        for filter_obj in filters:
            try:
                # Check if cargo matches filter criteria
                if cargo_matches_filter(cargo, filter_obj.filter_data):
                    # Create notification
                    Notification.objects.create(
                        user=filter_obj.user,
                        type='cargo',
                        message=f'New cargo matching your filter "{filter_obj.name}": {cargo.title}',
                        content_object=cargo
                    )
            except Exception as e:
                logger.error(
                    f"Error processing filter {filter_obj.id}: {str(e)}"
                )
                continue
                
    except Exception as e:
        logger.error(f"Error in notify_matching_users: {str(e)}")
        raise

@shared_task
def clean_old_notifications():
    """
    Remove notifications older than 30 days
    """
    try:
        threshold = timezone.now() - timedelta(days=30)
        Notification.objects.filter(created_at__lt=threshold).delete()
    except Exception as e:
        logger.error(f"Error in clean_old_notifications: {str(e)}")
        raise

@shared_task
def check_expired_cargos():
    """
    Check for expired cargo listings and notify owners
    """
    try:
        threshold = timezone.now().date()
        expired_cargos = Cargo.objects.filter(
            status='active',
            loading_date__lt=threshold
        )
        
        for cargo in expired_cargos:
            # Create notification for cargo owner
            Notification.objects.create(
                user=cargo.owner,
                type='cargo',
                message=f'Your cargo listing "{cargo.title}" has expired',
                content_object=cargo
            )
            
            # Update cargo status
            cargo.status = 'expired'
            cargo.save()
            
    except Exception as e:
        logger.error(f"Error in check_expired_cargos: {str(e)}")
        raise

def parse_cargo_message(message_text):
    """
    Parse cargo information from Telegram message
    This is a placeholder - implement actual parsing logic
    """
    # TODO: Implement message parsing using NLP or pattern matching
    return None

def cargo_matches_filter(cargo, filter_data):
    """
    Check if cargo matches filter criteria
    This is a placeholder - implement actual matching logic
    """
    # TODO: Implement filter matching logic
    return False