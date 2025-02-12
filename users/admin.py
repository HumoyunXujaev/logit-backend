from datetime import timezone
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserDocument
from django.utils.html import format_html

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'telegram_id', 'get_full_name', 'username', 'role',
        'type', 'rating', 'is_active', 'is_verified'
    )
    list_filter = (
        'is_active', 'is_verified', 'role', 'type',
        'date_joined', 'last_login'
    )
    search_fields = (
        'telegram_id', 'first_name', 'last_name',
        'username', 'phone_number', 'company_name'
    )
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {
            'fields': (
                'telegram_id', 'first_name', 'last_name',
                'username', 'language_code'
            )
        }),
        (_('Profile'), {
            'fields': (
                'type', 'role', 'preferred_language',
                'phone_number', 'whatsapp_number'
            )
        }),
        (_('Company Info'), {
            'fields': (
                'company_name', 'position', 'registration_certificate'
            )
        }),
        (_('Student Info'), {
            'fields': (
                'student_id', 'group_name', 'study_language',
                'curator_name', 'end_date'
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active', 'is_verified', 'verification_date',
                'verification_notes', 'rating'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_staff', 'is_superuser', 'groups', 'user_permissions'
            )
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'rating')
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('Full Name')
    
    def save_model(self, request, obj, form, change):
        """
        Custom save method to handle verification status
        """
        if 'is_verified' in form.changed_data:
            if obj.is_verified and not obj.verification_date:
                obj.verification_date = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'get_user_name', 'type', 'title', 'uploaded_at',
        'verified', 'verified_at', 'get_document_preview'
    )
    list_filter = ('type', 'verified', 'uploaded_at')
    search_fields = (
        'user__first_name', 'user__last_name',
        'user__telegram_id', 'title'
    )
    ordering = ('-uploaded_at',)
    
    readonly_fields = (
        'uploaded_at', 'verified_at', 'verified_by',
        'get_document_preview'
    )
    
    fieldsets = (
        (None, {
            'fields': ('user', 'type', 'title', 'file')
        }),
        (_('Verification'), {
            'fields': (
                'verified', 'verified_at', 'verified_by',
                'notes'
            )
        }),
        (_('Preview'), {
            'fields': ('get_document_preview',)
        }),
    )
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    get_user_name.short_description = _('User')
    get_user_name.admin_order_field = 'user__first_name'
    
    def get_document_preview(self, obj):
        """Generate preview for image documents"""
        if obj.file and hasattr(obj.file, 'url'):
            file_url = obj.file.url
            if file_url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                return format_html(
                    '<img src="{}" style="max-height: 200px;"/>',
                    file_url
                )
            return format_html(
                '<a href="{}" target="_blank">View Document</a>',
                file_url
            )
        return "No file uploaded"
    get_document_preview.short_description = _('Preview')
    
    def save_model(self, request, obj, form, change):
        """
        Custom save method to handle verification status
        """
        if 'verified' in form.changed_data and obj.verified:
            obj.verified_at = timezone.now()
            obj.verified_by = request.user
        super().save_model(request, obj, form, change)