from celery.schedules import crontab
from logit_backend.celery import app
from core.tasks import (
    clean_old_notifications,
    check_expired_cargos,
    check_expiring_documents
)

# Schedule periodic tasks
app.conf.beat_schedule = {
    'clean-old-notifications': {
        'task': 'core.tasks.clean_old_notifications',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'check-expired-cargos': {
        'task': 'core.tasks.check_expired_cargos',
        'schedule': crontab(hour='*/3'),  # Every 3 hours
    },
    'check-expiring-documents': {
        'task': 'core.tasks.check_expiring_documents',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
}