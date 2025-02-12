from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Notification,
    Favorite,
    Rating,
    TelegramGroup,
    TelegramMessage,
    SearchFilter
)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'type', 'short_message',
        'is_read', 'created_at'
    )
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    ordering = ('-created_at',)
    raw_id_fields = ('user',)
    
    def short_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    short_message.short_description = _('Message')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'content_type', 'object_id', 'created_at'
    )
    list_filter = ('content_type', 'created_at')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    ordering = ('-created_at',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = (
        'from_user', 'to_user', 'score',
        'short_comment', 'created_at'
    )
    list_filter = ('score', 'created_at')
    search_fields = (
        'from_user__username',
        'to_user__username',
        'comment'
    )
    raw_id_fields = ('from_user', 'to_user')
    ordering = ('-created_at',)
    
    def short_comment(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'
    short_comment.short_description = _('Comment')

@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'telegram_id', 'is_active',
        'last_sync', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'telegram_id')
    ordering = ('name',)
    
    actions = ['sync_selected_groups']
    
    def sync_selected_groups(self, request, queryset):
        for group in queryset:
            from .tasks import sync_telegram_group
            sync_telegram_group.delay(group.id)
        self.message_user(
            request,
            _("Sync started for selected groups.")
        )
    sync_selected_groups.short_description = _("Sync selected groups")

@admin.register(TelegramMessage)
class TelegramMessageAdmin(admin.ModelAdmin):
    list_display = (
        'telegram_id', 'group', 'short_text',
        'processed', 'processed_at', 'created_at'
    )
    list_filter = (
        'processed', 'processed_at', 'created_at',
        'group'
    )
    search_fields = ('telegram_id', 'message_text')
    raw_id_fields = ('group', 'cargo')
    ordering = ('-created_at',)
    
    def short_text(self, obj):
        return obj.message_text[:50] + '...' if len(obj.message_text) > 50 else obj.message_text
    short_text.short_description = _('Message Text')
    
    actions = ['process_selected_messages']
    
    def process_selected_messages(self, request, queryset):
        for message in queryset.filter(processed=False):
            from .tasks import process_telegram_message
            process_telegram_message.delay(message.id)
        self.message_user(
            request,
            _("Processing started for selected messages.")
        )
    process_selected_messages.short_description = _("Process selected messages")

@admin.register(SearchFilter)
class SearchFilterAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'name', 'notifications_enabled',
        'created_at', 'updated_at'
    )
    list_filter = ('notifications_enabled', 'created_at')
    search_fields = ('user__username', 'name')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)