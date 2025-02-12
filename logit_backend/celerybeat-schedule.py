from celery.schedules import crontab
from logit_backend.celery import app
from core.tasks import (
    sync_telegram_groups,
    process_telegram_messages,
    clean_old_notifications,
    check_expired_cargos
)

# Schedule periodic tasks
app.conf.beat_schedule = {
    'sync-telegram-groups': {
        'task': 'core.tasks.sync_telegram_groups',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'process-telegram-messages': {
        'task': 'core.tasks.process_telegram_messages',
        'schedule': crontab(minute='*/2'),  # Every 2 minutes
    },
    'clean-old-notifications': {
        'task': 'core.tasks.clean_old_notifications',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'check-expired-cargos': {
        'task': 'core.tasks.check_expired_cargos',
        'schedule': crontab(hour='*/1'),  # Every hour
    },
}