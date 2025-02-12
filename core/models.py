from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User

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