from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Vehicle,
    VehicleDocument,
    VehicleAvailability,
    VehicleInspection
)

class VehicleDocumentInline(admin.TabularInline):
    model = VehicleDocument
    extra = 1
    fields = [
        'type', 'title', 'file', 'expiry_date',
        'verified', 'verification_notes'
    ]
    readonly_fields = ['verified_at', 'verified_by']
    ordering = ['-uploaded_at']

class VehicleAvailabilityInline(admin.TabularInline):
    model = VehicleAvailability
    extra = 1
    fields = ['start_date', 'end_date', 'location', 'note']
    ordering = ['-start_date']

class VehicleInspectionInline(admin.TabularInline):
    model = VehicleInspection
    extra = 1
    fields = [
        'type', 'inspection_date', 'expiry_date',
        'inspector', 'result', 'notes'
    ]
    ordering = ['-inspection_date']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'registration_number', 'owner', 'body_type',
        'get_dimensions', 'is_verified', 'is_active',
        'created_at'
    )
    list_filter = (
        'body_type', 'loading_type', 'is_active',
        'is_verified', 'adr', 'dozvol', 'tir',
        'registration_country', 'created_at'
    )
    search_fields = (
        'registration_number', 'owner__username',
        'owner__first_name', 'owner__last_name'
    )
    raw_id_fields = ['owner', 'verified_by']
    date_hierarchy = 'created_at'
    
    inlines = [
        VehicleDocumentInline,
        VehicleAvailabilityInline,
        VehicleInspectionInline
    ]
    
    fieldsets = (
        (None, {
            'fields': (
                'owner', 'registration_number',
                'registration_country'
            )
        }),
        (_('Vehicle Specifications'), {
            'fields': (
                'body_type', 'loading_type',
                ('capacity', 'volume'),
                ('length', 'width', 'height')
            )
        }),
        (_('Certifications'), {
            'fields': (
                'adr', 'dozvol', 'tir',
                'license_number'
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active', 'is_verified',
                'verification_date', 'verified_by'
            )
        }),
    )
    
    readonly_fields = [
        'created_at', 'updated_at',
        'verification_date', 'verified_by'
    ]
    
    def get_dimensions(self, obj):
        return f"{obj.length}x{obj.width}x{obj.height} м"
    get_dimensions.short_description = _('Dimensions')
    
    actions = ['verify_vehicles', 'mark_as_inactive']
    
    def verify_vehicles(self, request, queryset):
        updated = queryset.update(
            is_verified=True,
            verified_by=request.user,
            verification_date=timezone.now()
        )
        self.message_user(
            request,
            _(f'{updated} vehicles were verified.')
        )
    verify_vehicles.short_description = _("Verify selected vehicles")
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f'{updated} vehicles were marked as inactive.')
        )
    mark_as_inactive.short_description = _("Mark selected vehicles as inactive")

@admin.register(VehicleDocument)
class VehicleDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle', 'type', 'title', 'expiry_date',
        'verified', 'verified_at', 'get_file_preview'
    )
    list_filter = (
        'type', 'verified', 'uploaded_at',
        'expiry_date'
    )
    search_fields = (
        'vehicle__registration_number',
        'title', 'verification_notes'
    )
    raw_id_fields = ['vehicle', 'verified_by']
    ordering = ['-uploaded_at']
    
    fieldsets = (
        (None, {
            'fields': (
                'vehicle', 'type', 'title',
                'file', 'expiry_date'
            )
        }),
        (_('Verification'), {
            'fields': (
                'verified', 'verified_at',
                'verified_by', 'verification_notes'
            )
        }),
    )
    
    readonly_fields = [
        'uploaded_at', 'verified_at',
        'verified_by'
    ]
    
    def get_file_preview(self, obj):
        if obj.file:
            if obj.file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return format_html(
                    '<img src="{}" height="50"/>',
                    obj.file.url
                )
            return format_html(
                '<a href="{}" target="_blank">View Document</a>',
                obj.file.url
            )
        return "-"
    get_file_preview.short_description = _('Document Preview')
    
    actions = ['verify_documents', 'unverify_documents']
    
    def verify_documents(self, request, queryset):
        updated = queryset.update(
            verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(
            request,
            _(f'{updated} documents were verified.')
        )
    verify_documents.short_description = _("Verify selected documents")
    
    def unverify_documents(self, request, queryset):
        updated = queryset.update(
            verified=False,
            verified_by=None,
            verified_at=None
        )
        self.message_user(
            request,
            _(f'{updated} documents were unverified.')
        )
    unverify_documents.short_description = _("Unverify selected documents")

@admin.register(VehicleInspection)
class VehicleInspectionAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle', 'type', 'inspection_date',
        'expiry_date', 'result', 'inspector'
    )
    list_filter = (
        'type', 'result', 'inspection_date',
        'expiry_date'
    )
    search_fields = (
        'vehicle__registration_number',
        'inspector__username', 'notes'
    )
    raw_id_fields = ['vehicle', 'inspector']
    ordering = ['-inspection_date']
    date_hierarchy = 'inspection_date'
    
    readonly_fields = ['created_at']

@admin.register(VehicleAvailability)
class VehicleAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle', 'start_date', 'end_date',
        'location', 'created_at'
    )
    list_filter = ('start_date', 'end_date')
    search_fields = (
        'vehicle__registration_number',
        'location', 'note'
    )
    raw_id_fields = ['vehicle']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    
    readonly_fields = ['created_at']