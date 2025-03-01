from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from cargo.models import Cargo
logger = logging.getLogger(__name__)

class Location(models.Model):
    """
    Unified model for countries, states and cities
    Level: 1 = Country, 2 = State/Region, 3 = City
    """
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    country = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                               related_name='all_locations')
    level = models.SmallIntegerField(
        choices=[
            (1, 'Country'),
            (2, 'State/Region'),
            (3, 'City')
        ]
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    code = models.CharField(max_length=10, null=True, blank=True)  # Для кодов стран/штатов (iso2, state_code и т.д.)
    additional_data = models.JSONField(null=True, blank=True)  # Для хранения дополнительных данных
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['parent_id']),
            models.Index(fields=['country_id']),
            # Индекс для географического поиска
            models.Index(fields=['latitude', 'longitude'], name='location_coords_idx')
        ]
        ordering = ['name']

    def __str__(self):
        if self.level == 1:
            return f"{self.name} (Country)"
        elif self.level == 2:
            return f"{self.name}, {self.country.name} (State)" if self.country else f"{self.name} (State)"
        else:
            state = self.parent.name if self.parent and self.parent.level == 2 else None
            country_name = self.country.name if self.country else ""
            return f"{self.name}, {state + ', ' if state else ''}{country_name} (City)"

    def get_hierarchy(self):
        """Returns list of parent locations up to country"""
        hierarchy = []
        current = self
        while current:
            hierarchy.append({
                'id': current.id,
                'name': current.name,
                'level': current.level
            })
            current = current.parent
        return list(reversed(hierarchy))

    @property
    def full_name(self):
        """Returns full location name including parent locations"""
        hierarchy = self.get_hierarchy()
        return ' › '.join(item['name'] for item in hierarchy)
    
    
class Notification(models.Model):
    class NotificationType(models.TextChoices):
        CARGO = 'cargo', _('Cargo')
        ROUTE = 'route', _('Route')
        SYSTEM = 'system', _('System')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['is_read']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['user', 'content_type', 'object_id']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.content_object}"

class Rating(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    score = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text=_("Rating from 1 to 5")
    )
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('from_user', 'to_user')
        indexes = [
            models.Index(fields=['to_user', 'score']),
        ]
        
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}: {self.score}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update user's average rating
        self.to_user.update_rating()

class TelegramGroup(models.Model):
    telegram_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name

class TelegramMessage(models.Model):
    telegram_id = models.CharField(max_length=100, unique=True)
    group = models.ForeignKey(TelegramGroup, on_delete=models.CASCADE, related_name='messages')
    message_text = models.TextField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Link to created cargo if message was processed
    cargo = models.ForeignKey('cargo.Cargo', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['processed']),
            models.Index(fields=['telegram_id']),
        ]
        
    def __str__(self):
        return f"{self.group.name} - {self.telegram_id}"

class SearchFilter(models.Model):
    """Model for storing user search filters"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_filters')
    name = models.CharField(max_length=255)
    filter_data = models.JSONField()
    notifications_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'notifications_enabled']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    

@receiver(post_save, sender=SearchFilter)
def notify_search_filter_subscription(sender, instance, created, **kwargs):
    """Send notification when a user subscribes to a search filter"""
    if created and instance.notifications_enabled:
        # Prepare notification message
        message = f"""
📢 <b>Новая подписка на фильтр</b>

Вы подписались на уведомления по фильтру "{instance.name}".
Вы будете получать уведомления о новых грузах, соответствующих вашим критериям.

👉 Перейдите в приложение для управления подписками
"""
        
        # Notify user
        from core.services.telegram import telegram_service
        if instance.user.telegram_id:
            telegram_service.send_notification.delay(
                instance.user.telegram_id,
                message
            )

def cargo_matches_filter(cargo, filter_data):
    """Check if cargo matches filter criteria"""
    # Basic matching logic - can be expanded for more complex filters
    matches = True
    
    # Match vehicle type
    if filter_data.get('vehicle_type') and cargo.vehicle_type != filter_data['vehicle_type']:
        matches = False
        
    # Match loading point
    if filter_data.get('loading_point'):
        if filter_data['loading_point'].lower() not in cargo.loading_point.lower():
            matches = False
            
    # Match unloading point
    if filter_data.get('unloading_point'):
        if filter_data['unloading_point'].lower() not in cargo.unloading_point.lower():
            matches = False
    
    # Match date range
    if filter_data.get('date_from'):
        from django.utils.dateparse import parse_date
        date_from = parse_date(filter_data['date_from'])
        if date_from and cargo.loading_date < date_from:
            matches = False
            
    if filter_data.get('date_to'):
        from django.utils.dateparse import parse_date
        date_to = parse_date(filter_data['date_to'])
        if date_to and cargo.loading_date > date_to:
            matches = False
    
    return matches

@receiver(post_save, sender=Cargo)
def notify_matching_filter_subscribers(sender, instance, created, **kwargs):
    """Notify users with matching search filters about new cargo"""
    if not created:
        return
        
    from core.services.telegram import telegram_service
    
    # Find all active search filters with notifications enabled
    search_filters = SearchFilter.objects.filter(notifications_enabled=True)
    
    for filter_obj in search_filters:
        try:
            # Check if cargo matches filter criteria
            if cargo_matches_filter(instance, filter_obj.filter_data):
                # Create notification message
                message = f"""
🚛 <b>Новый груз по вашему фильтру</b>

<b>Фильтр:</b> {filter_obj.name}
<b>Груз:</b> {instance.title}
<b>Маршрут:</b> {instance.loading_point} ➡️ {instance.unloading_point}
<b>Дата загрузки:</b> {instance.loading_date.strftime('%d.%m.%Y')}

👉 Перейдите в приложение для подробностей
"""
                
                # Send notification
                if filter_obj.user.telegram_id:
                    telegram_service.send_notification.delay(
                        filter_obj.user.telegram_id,
                        message
                    )
        except Exception as e:
            # Log the error but continue processing other filters
            logger.error(f"Error processing filter {filter_obj.id}: {str(e)}")
            continue