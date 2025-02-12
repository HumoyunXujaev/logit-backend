from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Cargo, CargoDocument, CargoStatusHistory, CarrierRequest

admin.register(CarrierRequest)
class CarrierRequestAdmin(admin.ModelAdmin):
    list_display = (
        'carrier', 'vehicle', 'loading_point',
        'unloading_point', 'ready_date',
        'price_expectation', 'status', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'carrier__username', 'vehicle__registration_number',
        'loading_point', 'unloading_point'
    )
    raw_id_fields = ['carrier', 'vehicle']
    ordering = ['-created_at']


    
class CargoDocumentInline(admin.TabularInline):
    model = CargoDocument
    extra = 1
    readonly_fields = ['uploaded_at']
    fields = ['type', 'title', 'file', 'notes', 'uploaded_at']

class CargoStatusHistoryInline(admin.TabularInline):
    model = CargoStatusHistory
    extra = 0
    readonly_fields = ['changed_at']
    fields = ['status', 'changed_by', 'changed_at', 'comment']
    ordering = ['-changed_at']

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'get_route', 'status', 'owner',
        'vehicle_type', 'loading_date', 'price',
        'views_count', 'created_at'
    )
    list_filter = (
        'status', 'vehicle_type', 'loading_type',
        'payment_method', 'is_constant', 'is_ready',
        'created_at'
    )
    search_fields = (
        'title', 'description', 'loading_point',
        'unloading_point', 'owner__username'
    )
    raw_id_fields = ['owner']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    inlines = [CargoDocumentInline, CargoStatusHistoryInline]
    
    fieldsets = (
        (None, {
            'fields': (
                'title', 'description', 'status', 'owner'
            )
        }),
        (_('Dimensions and Weight'), {
            'fields': (
                ('weight', 'volume'),
                ('length', 'width', 'height')
            )
        }),
        (_('Route'), {
            'fields': (
                'loading_point', 'unloading_point',
                'additional_points'
            )
        }),
        (_('Schedule'), {
            'fields': (
                'loading_date', 'is_constant', 'is_ready'
            )
        }),
        (_('Vehicle Requirements'), {
            'fields': (
                'vehicle_type', 'loading_type'
            )
        }),
        (_('Payment'), {
            'fields': (
                'payment_method', 'price', 'payment_details'
            )
        }),
        (_('Meta'), {
            'fields': (
                'source_type', 'source_id', 'views_count',
                'created_at', 'updated_at'
            )
        }),
    )
    
    readonly_fields = [
        'created_at', 'updated_at', 'views_count'
    ]
    
    def get_route(self, obj):
        return f"{obj.loading_point} → {obj.unloading_point}"
    get_route.short_description = _('Route')
    
    def save_model(self, request, obj, form, change):
        if change:
            if 'status' in form.changed_data:
                CargoStatusHistory.objects.create(
                    cargo=obj,
                    status=obj.status,
                    changed_by=request.user,
                    comment='Changed from admin'
                )
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_active', 'mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        for cargo in queryset:
            CargoStatusHistory.objects.create(
                cargo=cargo,
                status='active',
                changed_by=request.user,
                comment='Marked as active from admin'
            )
        self.message_user(
            request,
            _(f'{updated} cargos were marked as active.')
        )
    mark_as_active.short_description = _('Mark selected cargos as active')
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        for cargo in queryset:
            CargoStatusHistory.objects.create(
                cargo=cargo,
                status='completed',
                changed_by=request.user,
                comment='Marked as completed from admin'
            )
        self.message_user(
            request,
            _(f'{updated} cargos were marked as completed.')
        )
    mark_as_completed.short_description = _('Mark selected cargos as completed')
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        for cargo in queryset:
            CargoStatusHistory.objects.create(
                cargo=cargo,
                status='cancelled',
                changed_by=request.user,
                comment='Marked as cancelled from admin'
            )
        self.message_user(
            request,
            _(f'{updated} cargos were marked as cancelled.')
        )
    mark_as_cancelled.short_description = _('Mark selected cargos as cancelled')

@admin.register(CargoDocument)
class CargoDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'cargo', 'type', 'title',
        'uploaded_at', 'get_file_preview'
    )
    list_filter = ('type', 'uploaded_at')
    search_fields = (
        'cargo__title', 'title', 'notes',
        'cargo__owner__username'
    )
    raw_id_fields = ['cargo']
    ordering = ['-uploaded_at']
    
    def get_file_preview(self, obj):
        if obj.file:
            if obj.file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return format_html(
                    '<img src="{}" height="50"/>',
                    obj.file.url
                )
            return format_html(
                '<a href="{}" target="_blank">View File</a>',
                obj.file.url
            )
        return "-"
    get_file_preview.short_description = _('File Preview')

@admin.register(CargoStatusHistory)
class CargoStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'cargo', 'status', 'changed_by',
        'changed_at'
    )
    list_filter = ('status', 'changed_at')
    search_fields = (
        'cargo__title', 'changed_by__username',
        'comment'
    )
    raw_id_fields = ['cargo', 'changed_by']
    ordering = ['-changed_at']
    readonly_fields = ['changed_at']