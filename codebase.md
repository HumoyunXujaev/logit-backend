# cargo\admin.py

```py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Cargo, CargoDocument, CargoStatusHistory, CarrierRequest

@admin.register(CarrierRequest)
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
    raw_id_fields = ['owner', 'loading_location', 'unloading_location']
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
                'additional_points', 'loading_location', 'unloading_location'
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
        })
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
```

# cargo\apps.py

```py
from django.apps import AppConfig

class CargoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cargo'
    
    def ready(self):
        import cargo.signals  # Import signals when app is ready

```

# cargo\filters.py

```py
import django_filters
from django.db.models import Q
from .models import Cargo
from core.models import Location
from math import radians, cos, sin, asin, sqrt

class CargoFilter(django_filters.FilterSet):
    min_weight = django_filters.NumberFilter(
        field_name='weight',
        lookup_expr='gte'
    )
    max_weight = django_filters.NumberFilter(
        field_name='weight',
        lookup_expr='lte'
    )
    min_volume = django_filters.NumberFilter(
        field_name='volume',
        lookup_expr='gte'
    )
    max_volume = django_filters.NumberFilter(
        field_name='volume',
        lookup_expr='lte'
    )
    loading_date_from = django_filters.DateFilter(
        field_name='loading_date',
        lookup_expr='gte'
    )
    loading_date_to = django_filters.DateFilter(
        field_name='loading_date',
        lookup_expr='lte'
    )
    price_from = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte'
    )
    price_to = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte'
    )
    
    # Фильтры для Location
    loading_location = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=3),
        field_name='loading_location'
    )
    unloading_location = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=3),
        field_name='unloading_location'
    )
    loading_country = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=1),
        method='filter_loading_country'
    )
    unloading_country = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=1),
        method='filter_unloading_country'
    )
    loading_state = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=2),
        method='filter_loading_state'
    )
    unloading_state = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=2),
        method='filter_unloading_state'
    )
    
    # Старые текстовые фильтры (для совместимости)
    location = django_filters.CharFilter(method='filter_location')
    radius = django_filters.NumberFilter(method='filter_radius')
    
    class Meta:
        model = Cargo
        fields = {
            'status': ['exact'],
            'vehicle_type': ['exact', 'in'],
            'loading_type': ['exact', 'in'],
            'payment_method': ['exact'],
            'is_constant': ['exact'],
            'is_ready': ['exact'],
        }
    
    def filter_location(self, queryset, name, value):
        """
        Filter by loading or unloading point, supporting partial matches
        """
        if not value:
            return queryset
            
        return queryset.filter(
            Q(loading_point__icontains=value) |
            Q(unloading_point__icontains=value)
        )
    
    def filter_radius(self, queryset, name, value):
        """
        Filter by radius around loading or unloading point
        Uses Location objects if specified, otherwise falls back to text search
        """
        if not value:
            return queryset
            
        # Получаем параметры из запроса
        request = self.request
        if not request:
            return queryset
            
        # Фильтруем по загрузке
        filtered_queryset = queryset
        
        # Проверяем если есть loading_location_id
        loading_location_id = request.query_params.get('loading_location_id')
        if loading_location_id:
            try:
                # Получаем локацию
                location = Location.objects.get(id=loading_location_id)
                if location.latitude and location.longitude:
                    # Фильтруем грузы в радиусе
                    locations_in_radius = self._get_locations_in_radius(
                        location.latitude, location.longitude, value
                    )
                    filtered_queryset = filtered_queryset.filter(
                        loading_location__in=locations_in_radius
                    )
            except Location.DoesNotExist:
                pass
                
        # Проверяем если есть unloading_location_id
        unloading_location_id = request.query_params.get('unloading_location_id')
        if unloading_location_id:
            try:
                # Получаем локацию
                location = Location.objects.get(id=unloading_location_id)
                if location.latitude and location.longitude:
                    # Фильтруем грузы в радиусе
                    locations_in_radius = self._get_locations_in_radius(
                        location.latitude, location.longitude, value
                    )
                    filtered_queryset = filtered_queryset.filter(
                        unloading_location__in=locations_in_radius
                    )
            except Location.DoesNotExist:
                pass
                
        return filtered_queryset
    
    def filter_loading_country(self, queryset, name, value):
        """Фильтр по стране загрузки"""
        if not value:
            return queryset
        
        # Ищем все Location с указанной страной
        return queryset.filter(
            Q(loading_location__country=value) |
            Q(loading_location=value)  # Если сама страна выбрана как локация
        )
    
    def filter_unloading_country(self, queryset, name, value):
        """Фильтр по стране выгрузки"""
        if not value:
            return queryset
        
        # Ищем все Location с указанной страной
        return queryset.filter(
            Q(unloading_location__country=value) |
            Q(unloading_location=value)  # Если сама страна выбрана как локация
        )
    
    def filter_loading_state(self, queryset, name, value):
        """Фильтр по региону/штату загрузки"""
        if not value:
            return queryset
        
        # Ищем все Location с указанным регионом или который является регионом
        return queryset.filter(
            Q(loading_location__parent=value) |
            Q(loading_location=value)  # Если сам штат выбран как локация
        )
    
    def filter_unloading_state(self, queryset, name, value):
        """Фильтр по региону/штату выгрузки"""
        if not value:
            return queryset
        
        # Ищем все Location с указанным регионом или который является регионом
        return queryset.filter(
            Q(unloading_location__parent=value) |
            Q(unloading_location=value)  # Если сам штат выбран как локация
        )
    
    def _get_locations_in_radius(self, lat, lon, radius_km):
        """
        Получить все локации в указанном радиусе
        Используем формулу Гаверсинуса для расчета расстояния
        """
        locations = []
        
        # Получаем все локации уровня 3 (города)
        cities = Location.objects.filter(level=3)
        
        for city in cities:
            if city.latitude and city.longitude:
                distance = self._haversine(
                    float(lat), float(lon),
                    float(city.latitude), float(city.longitude)
                )
                if distance <= radius_km:
                    locations.append(city.id)
        
        return locations
    
    def _haversine(self, lat1, lon1, lat2, lon2):
        """
        Расчет расстояния между двумя точками по формуле Гаверсинуса
        Результат в километрах
        """
        # Конвертируем градусы в радианы
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Формула Гаверсинуса
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Радиус Земли в километрах
        
        return c * r
```

# cargo\models.py

```py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from django.utils import timezone
from vehicles.models import Vehicle

class CarrierRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ASSIGNED = 'assigned', _('Assigned to Cargo')
        ACCEPTED = 'accepted', _('Accepted by Carrier')
        REJECTED = 'rejected', _('Rejected by Carrier')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')

    # Basic Information
    carrier = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='carrier_requests',
        limit_choices_to={'role': 'carrier'}
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        related_name='carrier_requests'
    )
    
    # Route Information
    loading_point = models.CharField(max_length=255)
    unloading_point = models.CharField(max_length=255)

     # Новые поля для связи с Location
    loading_location = models.ForeignKey(
        'core.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carrier_loading_requests'
    )
    unloading_location = models.ForeignKey(
        'core.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carrier_unloading_requests'
    )

    ready_date = models.DateField()
    vehicle_count = models.PositiveIntegerField(default=1)
    
    # Payment and Additional Info
    price_expectation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    payment_terms = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Logistics Assignment
    assigned_cargo = models.ForeignKey(
        'Cargo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carrier_requests'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_carrier_requests',
        limit_choices_to={'role': 'student'}
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['carrier']),
            models.Index(fields=['status']),
            models.Index(fields=['ready_date']),
            models.Index(fields=['loading_point']),
            models.Index(fields=['unloading_point']),
        ]
        
    def __str__(self):
        return f"Request from {self.carrier.get_full_name()} ({self.loading_point} - {self.unloading_point})"

    # def notify_users(self, recipients, message):
    #     """Send notification to multiple users"""
    #     from core.services.telegram import telegram_service
        
    #     # Create list of (chat_id, message) tuples for users with telegram_id
    #     messages = [
    #         (user.telegram_id, message)
    #         for user in recipients
    #         if user.telegram_id
    #     ]
        
    #     # Send messages if we have any recipients
    #     if messages:
    #         telegram_service.send_bulk_messages(messages)
    def notify_users(self, recipients, message):
        """Send notification to multiple users"""
        from core.services.telegram import telegram_service
        
        messages = [
            {"telegram_id": user.telegram_id, "message": message}
            for user in recipients
            if user is not None and user.telegram_id  # Check if user is None before accessing telegram_id
        ]
        
        # Send messages if we have any recipients
        if messages:
            telegram_service.send_bulk_messages.delay(messages)


    def save(self, *args, **kwargs):
        """Override save to handle notifications"""
        is_new = not self.pk
        if not is_new:
            old_status = CarrierRequest.objects.get(pk=self.pk).status
            status_changed = old_status != self.status
        else:
            status_changed = False
            
        super().save(*args, **kwargs)
        
        # Get notification service
        from core.services.telegram import telegram_service
        
        if is_new:
            # Notify students about new carrier request
            students = User.objects.filter(role='student', is_active=True)
            message = telegram_service.format_carrier_notification(
                self,
                "Новая заявка от перевозчика"
            )
            self.notify_users(students, message)
                        
        elif status_changed:
            # Send notifications based on new status
            message = telegram_service.format_carrier_notification(
                self,
                f"Статус заявки изменен на {self.get_status_display()}"
            )
            recipients = []
            
            if self.status == self.RequestStatus.ASSIGNED:
                # Notify carrier about assignment
                recipients = [self.carrier]
                
            elif self.status in [self.RequestStatus.ACCEPTED, self.RequestStatus.REJECTED]:
                # Notify assigning student
                if self.assigned_by:
                    recipients = [self.assigned_by]
                    
                # Also notify cargo owner if request was accepted
                if self.status == self.RequestStatus.ACCEPTED and self.assigned_cargo:
                    recipients.append(self.assigned_cargo.owner)
            
            elif self.status == self.RequestStatus.COMPLETED:
                # Notify carrier and cargo owner
                recipients = [self.carrier]
                if self.assigned_cargo:
                    recipients.append(self.assigned_cargo.owner)
            
            if recipients:
                self.notify_users(recipients, message)


class Cargo(models.Model):
    class CargoStatus(models.TextChoices):
            DRAFT = 'draft', _('Draft')
            PENDING_APPROVAL = 'pending_approval', _('Pending Manager Approval')
            MANAGER_APPROVED = 'manager_approved', _('Approved by Manager')
            PENDING = 'pending', _('Pending Assignment')
            ASSIGNED = 'assigned', _('Assigned to Carrier')
            IN_PROGRESS = 'in_progress', _('In Progress')
            COMPLETED = 'completed', _('Completed')
            CANCELLED = 'cancelled', _('Cancelled')
            REJECTED = 'rejected', _('Rejected by Manager')
            EXPIRED = 'expired', _('Expired')

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Cash')
        CARD = 'card', _('Card')
        TRANSFER = 'transfer', _('Bank Transfer')
        ADVANCE = 'advance', _('Advance')

    class VehicleType(models.TextChoices):
        TENT = 'tent', _('Tent')
        REFRIGERATOR = 'refrigerator', _('Refrigerator')
        ISOTHERMAL = 'isothermal', _('Isothermal')
        CONTAINER = 'container', _('Container')
        CAR_CARRIER = 'car_carrier', _('Car Carrier')
        BOARD = 'board', _('Board')
    
    class LoadingType(models.TextChoices):
        RAMPS = 'ramps', _('Ramps')
        NO_DOORS = 'no_doors', _('No Doors')
        SIDE = 'side', _('Side Loading')
        TOP = 'top', _('Top Loading')
        HYDRO_BOARD = 'hydro_board', _('Hydro Board')

    class SourceType(models.TextChoices):
        TELEGRAM = 'telegram', _('Telegram')
        API = 'api', _('External API')
        MANUAL = 'manual', _('Manual Entry')
        WEBSITE = 'website', _('Website')
        
    # Basic cargo information
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=CargoStatus.choices,
        default=CargoStatus.DRAFT
    )
    
    # Dimensions and weight
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    
    loading_location = models.ForeignKey(
        'core.Location',
        on_delete=models.PROTECT,
        related_name='loading_cargos',
        null=True,
        blank=True
    )
    unloading_location = models.ForeignKey(
        'core.Location',
        on_delete=models.PROTECT,
        related_name='unloading_cargos',
        null=True,
        blank=True
    )
    
    # Optional intermediate points
    additional_locations = models.ManyToManyField(
        'core.Location',
        related_name='intermediate_cargos',
        null=True,
        blank=True
    )

    # Route information
    loading_point = models.CharField(max_length=255)
    unloading_point = models.CharField(max_length=255)
    additional_points = models.JSONField(null=True, blank=True)
    
    # Timing
    loading_date = models.DateField()
    is_constant = models.BooleanField(default=False)
    is_ready = models.BooleanField(default=False)
    
    # Vehicle requirements
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices
    )
    loading_type = models.CharField(
        max_length=20,
        choices=LoadingType.choices
    )
    
    # Payment information
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    payment_details = models.JSONField(null=True, blank=True)
    
    # Owner and management
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_cargos',
        null=True,
        blank=True,
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cargos',
        limit_choices_to={'role': 'carrier'}
    )
    managed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_cargos',
        limit_choices_to={'role': 'student'}
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    
    # Source information 
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.MANUAL
    )
    source_id = models.CharField(max_length=255, null=True, blank=True)
    approved_by = models.ForeignKey(
            User,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='approved_cargos',
            limit_choices_to={'role': 'manager'}
        )
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(null=True, blank=True)
    
    def get_distance(self):
        """Calculate total route distance in km"""
        from math import radians, sin, cos, sqrt, atan2
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth's radius in km
            
            lat1, lon1 = map(radians, [float(lat1), float(lon1)])
            lat2, lon2 = map(radians, [float(lat2), float(lon2)])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c

        total_distance = 0
        prev_location = self.loading_location
        
        # Add intermediate points if they exist
        locations = list(self.additional_locations.all())
        locations.append(self.unloading_location)
        
        for location in locations:
            if prev_location.latitude and prev_location.longitude and \
               location.latitude and location.longitude:
                distance = haversine(
                    prev_location.latitude, prev_location.longitude,
                    location.latitude, location.longitude
                )
                total_distance += distance
            prev_location = location
            
        return round(total_distance)
    
    def notify_users(self, recipients, message):
        """Send notification to multiple users"""
        from core.services.telegram import telegram_service
        
        messages = [
            {"telegram_id": user.telegram_id, "message": message}
            for user in recipients
            if user is not None and user.telegram_id  # Check if user is None before accessing telegram_id
        ]
        
        # Send messages if we have any recipients
        if messages:
            telegram_service.send_bulk_messages.delay(messages)

    def save(self, *args, **kwargs):
        """Override save to handle volume calculation and notifications"""
        if all([self.length, self.width, self.height]):
            self.volume = self.length * self.width * self.height
            
        # Check if this is a new cargo or status has changed
        is_new = not self.pk
        if not is_new:
            old_status = Cargo.objects.get(pk=self.pk).status
            status_changed = old_status != self.status
        else:
            status_changed = False

        if self.approved_by and not self.approval_date:
            self.approval_date = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Get notification service
        from core.services.telegram import telegram_service
        
        if is_new:
            # Notify managers about new cargo requiring approval
            if self.status == self.CargoStatus.PENDING_APPROVAL:
                managers = User.objects.filter(role='manager', is_active=True)
                message = telegram_service.format_cargo_notification(
                    self,
                    f"Новый груз требует проверки: {self.title}"
                )
                self.notify_users(managers, message)
                        
        elif status_changed:
            # Send notifications based on new status
            message = telegram_service.format_cargo_notification(
                self,
                f"Статус груза изменен на {self.get_status_display()}: {self.title}"
            )
            recipients = []
            
            if self.status == self.CargoStatus.MANAGER_APPROVED:
                # Notify students about approved cargo
                recipients = User.objects.filter(role='student', is_active=True)
                
            elif self.status == self.CargoStatus.ASSIGNED:
                # Notify assigned carrier
                if self.assigned_to:
                    recipients = [self.assigned_to]
            
            elif self.status in [self.CargoStatus.COMPLETED, self.CargoStatus.CANCELLED]:
                # Notify owner and manager
                recipients = [self.owner]
                if self.approved_by:
                    recipients.append(self.approved_by)
            
            if recipients:
                self.notify_users(recipients, message)

    def approve(self, manager: User, notes: str = None):
        """Approve cargo by manager"""
        if manager.role != 'manager':
            raise ValueError("Only managers can approve cargos")
            
        self.status = self.CargoStatus.MANAGER_APPROVED
        self.approved_by = manager
        self.approval_notes = notes
        self.approval_date = timezone.now()
        self.save()
        
        # Notify owner about approval
        from core.services.telegram import telegram_service
        message = telegram_service.format_cargo_notification(
            self,
            "Ваш груз был одобрен"
        )
        self.notify_users([self.owner], message)

    def reject(self, manager: User, notes: str = None):
        """Reject cargo by manager"""
        if manager.role != 'manager':
            raise ValueError("Only managers can reject cargos")
            
        self.status = self.CargoStatus.REJECTED
        self.approved_by = manager
        self.approval_notes = notes
        self.approval_date = timezone.now()
        self.save()
        
        # Notify owner about rejection
        from core.services.telegram import telegram_service
        message = telegram_service.format_cargo_notification(
            self,
            f"Ваш груз был отклонен\nПричина: {notes if notes else 'Не указана'}"
        )
        self.notify_users([self.owner], message)


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['loading_date']),
            models.Index(fields=['owner']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['managed_by']),
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['vehicle_type']),
            models.Index(fields=['loading_point']),
            models.Index(fields=['unloading_point']),
        ]
        
    def __str__(self):
        return f"{self.title} ({self.loading_point} - {self.unloading_point})"
    
    def increment_views(self):
        """Increment the view counter"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    

class CargoDocument(models.Model):
    """Model for storing cargo-related documents"""
    
    class DocumentType(models.TextChoices):
        INVOICE = 'invoice', _('Invoice')
        CMR = 'cmr', _('CMR')
        PACKING_LIST = 'packing_list', _('Packing List')
        OTHER = 'other', _('Other')

    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    type = models.CharField(max_length=20, choices=DocumentType.choices)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='cargo_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.cargo.title} - {self.type} - {self.title}"

class CargoStatusHistory(models.Model):
    """Model for tracking cargo status changes"""
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(
        max_length=20,
        choices=Cargo.CargoStatus.choices
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = 'Cargo status histories'
        
    def __str__(self):
        return f"{self.cargo.title} - {self.status} at {self.changed_at}"
    
    def save(self, *args, **kwargs):
        """Override save to send notifications"""
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new:
            # Send notification about status change
            from core.services.telegram import telegram_service
            message = (
                f"Cargo status updated to {self.get_status_display()}\n"
                f"Cargo: {self.cargo.title}\n"
                f"Changed by: {self.changed_by.get_full_name() if self.changed_by else 'System'}\n"
                f"Comment: {self.comment if self.comment else 'No comment'}"
            )
            
            # Notify cargo owner
            if self.cargo.owner.telegram_id:
                telegram_service.send_message(
                    self.cargo.owner.telegram_id,
                    message
                )
```

# cargo\serializers.py

```py
from rest_framework import serializers
from django.utils import timezone
from .models import CargoStatusHistory
from users.serializers import UserProfileSerializer
from .models import Cargo, CarrierRequest, CargoDocument
from vehicles.serializers import VehicleSerializer
from django.conf import settings
from core.serializers import LocationListSerializer, LocationDetailSerializer
from core.models import Location

class CargoApprovalSerializer(serializers.ModelSerializer):
    """Serializer for manager approval/rejection of cargo"""
    approval_notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Cargo
        fields = ['approval_notes']

    def validate(self, data):
        user = self.context['request'].user
        if user.role != 'manager':
            raise serializers.ValidationError(
                "Only managers can perform this action"
            )
        return data

class ManagerCargoUpdateSerializer(serializers.ModelSerializer):
    """Serializer for managers to update cargo details"""
    loading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    unloading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Cargo
        fields = [
            'title', 'description', 'weight',
            'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'loading_location', 'unloading_location',
            'additional_points', 'loading_date',
            'is_constant', 'is_ready', 'vehicle_type',
            'loading_type', 'payment_method', 'price',
            'payment_details', 'status'
        ]

    def validate_status(self, value):
        if value not in [
            Cargo.CargoStatus.MANAGER_APPROVED,
            Cargo.CargoStatus.REJECTED,
            Cargo.CargoStatus.PENDING
        ]:
            raise serializers.ValidationError(
                "Invalid status for manager update"
            )
        return value

    def validate(self, data):
        user = self.context['request'].user
        if user.role != 'manager':
            raise serializers.ValidationError(
                "Only managers can update cargo details"
            )
        return data
    
class ExternalCargoCreateSerializer(serializers.ModelSerializer):
    """Serializer for external cargo creation with API key validation"""
    api_key = serializers.CharField(write_only=True)
    source_type = serializers.ChoiceField(choices=Cargo.SourceType.choices)
    source_id = serializers.CharField(required=True)
    loading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    unloading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Cargo
        fields = [
            'title', 'description', 'weight',
            'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'loading_location', 'unloading_location',
            'additional_points', 'loading_date',
            'is_constant', 'is_ready', 'vehicle_type',
            'loading_type', 'payment_method', 'price',
            'payment_details', 'source_type', 'source_id',
            'api_key'
        ]

    def validate_api_key(self, value):
        """Validate the API key against the configured value"""
        valid_key = getattr(settings, 'EXTERNAL_API_KEY', None)
        if not valid_key:
            raise serializers.ValidationError(
                "API key validation is not configured"
            )
        
        if value != valid_key:
            raise serializers.ValidationError("Invalid API key")
        
        return value

    def validate(self, data):
        """Additional validation for the complete cargo data"""
        # Remove api_key from data before saving
        data.pop('api_key', None)
        
        # Set status to pending for external cargos
        data['status'] = 'pending'
        
        return data
    
class CargoDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoDocument
        fields = [
            'id', 'type', 'title', 'file',
            'uploaded_at', 'notes'
        ]
        read_only_fields = ['uploaded_at']

class CargoStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = CargoStatusHistory
        fields = [
            'id', 'status', 'changed_by',
            'changed_at', 'comment'
        ]
        read_only_fields = ['changed_at']

class CarrierRequestSerializer(serializers.ModelSerializer):
    """Full carrier request serializer with all details"""
    carrier = UserProfileSerializer(read_only=True)
    assigned_by = UserProfileSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    assigned_cargo = serializers.PrimaryKeyRelatedField(read_only=True)
    loading_location = LocationDetailSerializer(read_only=True)
    unloading_location = LocationDetailSerializer(read_only=True)
    
    class Meta:
        model = CarrierRequest
        fields = [
            'id', 'carrier', 'vehicle', 'loading_point',
            'unloading_point', 'loading_location', 'unloading_location',
            'ready_date', 'vehicle_count',
            'price_expectation', 'payment_terms', 'notes',
            'status', 'created_at', 'updated_at',
            'assigned_cargo', 'assigned_by', 'assigned_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'assigned_at']

class CarrierRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating carrier requests"""
    loading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    unloading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CarrierRequest
        fields = [
            'vehicle', 'loading_point', 'unloading_point',
            'loading_location', 'unloading_location',
            'ready_date', 'vehicle_count', 'price_expectation',
            'payment_terms', 'notes'
        ]
    
    def validate_vehicle(self, value):
        """Validate that vehicle belongs to the carrier"""
        user = self.context['request'].user
        if value.owner != user:
            raise serializers.ValidationError(
                "You can only use your own vehicles"
            )
        return value

    def validate_ready_date(self, value):
        """Validate ready date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Ready date cannot be in the past"
            )
        return value
    
    def validate(self, data):
        """Validate location data"""
        # Если указан loading_location, но не указан loading_point
        if data.get('loading_location') and not data.get('loading_point'):
            data['loading_point'] = data['loading_location'].name
            
        # Если указан unloading_location, но не указан unloading_point
        if data.get('unloading_location') and not data.get('unloading_point'):
            data['unloading_point'] = data['unloading_location'].name
            
        return data

class CarrierRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating carrier requests"""
    loading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    unloading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CarrierRequest
        fields = [
            'vehicle', 'loading_point', 'unloading_point',
            'loading_location', 'unloading_location',
            'ready_date', 'vehicle_count', 'price_expectation',
            'payment_terms', 'notes', 'status'
        ]

    def validate_status(self, value):
        """Validate status transitions"""
        instance = getattr(self, 'instance', None)
        if instance:
            valid_transitions = {
                'pending': ['cancelled'],
                'assigned': ['accepted', 'rejected'],
                'accepted': ['completed', 'cancelled'],
                'rejected': ['pending'],  # Allow retry
                'completed': [],  # No transitions from completed
                'cancelled': ['pending'],  # Allow reactivation
            }
            
            current_status = instance.status
            if value != current_status and value not in valid_transitions[current_status]:
                raise serializers.ValidationError(
                    f"Cannot transition from {current_status} to {value}"
                )
                
        return value
    
    def validate(self, data):
        """Validate location data"""
        # Если указан loading_location, но не указан loading_point
        if data.get('loading_location') and not data.get('loading_point'):
            data['loading_point'] = data['loading_location'].name
            
        # Если указан unloading_location, но не указан unloading_point
        if data.get('unloading_location') and not data.get('unloading_point'):
            data['unloading_point'] = data['unloading_location'].name
            
        return data

class CarrierRequestListSerializer(serializers.ModelSerializer):
    """Simplified carrier request serializer for list views"""
    carrier = UserProfileSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    loading_location = LocationListSerializer(read_only=True)
    unloading_location = LocationListSerializer(read_only=True)
    
    class Meta:
        model = CarrierRequest
        fields = [
            'id', 'carrier', 'vehicle', 'loading_point',
            'unloading_point', 'loading_location', 'unloading_location',
            'ready_date', 'vehicle_count',
            'price_expectation', 'payment_terms', 'notes',
            'status', 'created_at', 'updated_at',
            'assigned_cargo', 'assigned_by', 'assigned_at'
        ]

class CargoSerializer(serializers.ModelSerializer):
    """Full cargo serializer with all details"""
    owner = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    managed_by = UserProfileSerializer(read_only=True)
    carrier_requests = CarrierRequestListSerializer(many=True, read_only=True)
    loading_location = LocationDetailSerializer(read_only=True)
    unloading_location = LocationDetailSerializer(read_only=True)
    additional_locations = LocationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Cargo
        fields = [
            'id', 'title', 'description', 'status',
            'weight', 'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point', 
            'loading_location', 'unloading_location', 
            'additional_locations', 'additional_points',
            'loading_date', 'is_constant', 'is_ready',
            'vehicle_type', 'loading_type',
            'payment_method', 'price', 'payment_details',
            'owner', 'assigned_to', 'managed_by',
            'created_at', 'updated_at', 'views_count',
            'source_type', 'source_id', 'carrier_requests'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'views_count',
            'carrier_requests'
        ]

class CargoCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating cargos"""
    loading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    unloading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Cargo
        fields = [
            'title', 'description', 'weight',
            'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'loading_location', 'unloading_location',
            'additional_points', 'loading_date',
            'is_constant', 'is_ready', 'vehicle_type',
            'loading_type', 'payment_method', 'price',
            'payment_details'
        ]

    def validate_loading_date(self, value):
        """Validate that loading date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Loading date cannot be in the past"
            )
        return value
    
    def validate(self, data):
        """Validate location data"""
        # Если указан loading_location, но не указан loading_point
        if data.get('loading_location') and not data.get('loading_point'):
            data['loading_point'] = data['loading_location'].name
            
        # Если указан unloading_location, но не указан unloading_point
        if data.get('unloading_location') and not data.get('unloading_point'):
            data['unloading_point'] = data['unloading_location'].name
            
        return data
    
    def create(self, validated_data):
        """Create cargo with appropriate initial status based on user role"""
        request = self.context.get('request')
        user = request.user if request else None

        if not user:
            raise serializers.ValidationError("User is required")

        # Set initial status based on user role
        if user.role == 'cargo-owner':
            # Cargo owners' submissions need manager approval
            validated_data['status'] = Cargo.CargoStatus.PENDING_APPROVAL
        elif user.role == 'logistics-company':
            # Logistics companies' submissions go directly to pending
            validated_data['status'] = Cargo.CargoStatus.PENDING
        elif user.role == 'manager':
            # Managers' submissions are automatically approved
            validated_data['status'] = Cargo.CargoStatus.MANAGER_APPROVED
            validated_data['approved_by'] = user
        else:
            validated_data['status'] = Cargo.CargoStatus.DRAFT

        # Create the cargo
        print("creating cargo with data: ", validated_data)
        cargo = Cargo.objects.create(
            # owner=user, 
            **validated_data)
        
        return cargo
    
class CargoUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating cargo"""
    loading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    unloading_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(level=3),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Cargo
        fields = [
            'title', 'description', 'weight',
            'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'loading_location', 'unloading_location',
            'additional_points', 'loading_date',
            'is_constant', 'is_ready', 'vehicle_type',
            'loading_type', 'payment_method', 'price',
            'payment_details', 'status'
        ]

    def validate_status(self, value):
        """Validate status transitions based on user role"""
        user = self.context['request'].user
        instance = self.instance
        current_status = instance.status

        valid_transitions = {
            'draft': ['pending', 'cancelled'],
            'pending': ['assigned', 'cancelled'],
            'assigned': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],  # No transitions from completed
            'cancelled': ['draft'],  # Allow reactivation
            'expired': ['draft']  # Allow reactivation
        }

        # Additional role-based validation
        if user.role == 'student':
            if current_status == 'pending' and value == 'assigned':
                # Check if carrier is assigned
                if not self.instance.assigned_to:
                    raise serializers.ValidationError(
                        "Cannot mark as assigned without carrier"
                    )
        elif user.role == 'carrier':
            # Carriers can only update status of assigned cargos
            if instance.assigned_to != user:
                raise serializers.ValidationError(
                    "You can only update status of cargos assigned to you"
                )
            # Carriers can only mark as in_progress or completed
            if value not in ['in_progress', 'completed']:
                raise serializers.ValidationError(
                    "Invalid status transition for carrier"
                )

        if value != current_status and value not in valid_transitions[current_status]:
            raise serializers.ValidationError(
                f"Cannot transition from {current_status} to {value}"
            )

        return value
    
    def validate(self, data):
        """Validate location data"""
        # Если указан loading_location, но не указан loading_point
        if data.get('loading_location') and not data.get('loading_point'):
            data['loading_point'] = data['loading_location'].name
            
        # Если указан unloading_location, но не указан unloading_point
        if data.get('unloading_location') and not data.get('unloading_point'):
            data['unloading_point'] = data['unloading_location'].name
            
        return data

class CargoListSerializer(serializers.ModelSerializer):
    """Simplified cargo serializer for list views"""
    owner = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    managed_by = UserProfileSerializer(read_only=True)
    loading_location = LocationListSerializer(read_only=True)
    unloading_location = LocationListSerializer(read_only=True)

    class Meta:
        model = Cargo
        fields = [
            'id', 'title', 'description', 'status',
            'weight', 'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'loading_location', 'unloading_location',
            'additional_points', 'loading_date', 'is_constant', 'is_ready',
            'vehicle_type', 'loading_type',
            'payment_method', 'price', 'payment_details',
            'owner', 'assigned_to', 'managed_by',
            'created_at', 'updated_at', 'views_count',
            'source_type', 'source_id'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'views_count'
        ]

class CargoAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for assigning cargo to carrier"""
    carrier_request = serializers.PrimaryKeyRelatedField(
        queryset=CarrierRequest.objects.filter(status='pending')
    )

    class Meta:
        model = Cargo
        fields = ['carrier_request']

    def validate_carrier_request(self, value):
        """Validate carrier request can be assigned"""
        if value.status != 'pending':
            raise serializers.ValidationError(
                "Can only assign pending carrier requests"
            )
        if value.assigned_cargo:
            raise serializers.ValidationError(
                "Carrier request already assigned to another cargo"
            )
        return value

    def update(self, instance, validated_data):
        """Assign cargo to carrier"""
        carrier_request = validated_data['carrier_request']
        user = self.context['request'].user

        # Update cargo
        instance.status = 'assigned'
        instance.assigned_to = carrier_request.carrier
        instance.managed_by = user
        instance.save()

        # Update carrier request
        carrier_request.status = 'assigned'
        carrier_request.assigned_cargo = instance
        carrier_request.assigned_by = user
        carrier_request.assigned_at = timezone.now()
        carrier_request.save()

        return instance

class CargoAcceptanceSerializer(serializers.ModelSerializer):
    """Serializer for accepting/rejecting cargo assignment"""
    decision = serializers.ChoiceField(choices=['accept', 'reject'])

    class Meta:
        model = Cargo
        fields = ['decision']

    def validate(self, data):
        """Validate user can accept/reject cargo"""
        user = self.context['request'].user
        instance = self.instance

        if instance.assigned_to != user:
            raise serializers.ValidationError(
                "You can only accept/reject cargos assigned to you"
            )
        if instance.status != 'assigned':
            raise serializers.ValidationError(
                "Can only accept/reject assigned cargos"
            )

        return data

    def update(self, instance, validated_data):
        """Process cargo acceptance/rejection"""
        decision = validated_data['decision']
        carrier_request = instance.carrier_requests.filter(status='assigned').first()

        if decision == 'accept':
            instance.status = 'in_progress'
            if carrier_request:
                carrier_request.status = 'accepted'
        else:
            instance.status = 'pending'
            instance.assigned_to = None
            if carrier_request:
                carrier_request.status = 'rejected'
                carrier_request.assigned_cargo = None

        instance.save()
        if carrier_request:
            carrier_request.save()

        return instance

class CargoSearchSerializer(serializers.Serializer):
    """Serializer for cargo search parameters"""
    q = serializers.CharField(required=False, allow_blank=True)
    from_location_id = serializers.IntegerField(required=False)
    to_location_id = serializers.IntegerField(required=False)
    from_location = serializers.CharField(required=False, allow_blank=True)
    to_location = serializers.CharField(required=False, allow_blank=True)
    min_weight = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2
    )
    max_weight = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    vehicle_types = serializers.MultipleChoiceField(
        required=False,
        choices=Cargo.VehicleType.choices
    )
    loading_types = serializers.MultipleChoiceField(
        required=False,
        choices=Cargo.LoadingType.choices
    )
    payment_methods = serializers.MultipleChoiceField(
        required=False,
        choices=Cargo.PaymentMethod.choices
    )
    radius = serializers.IntegerField(required=False, min_value=0, max_value=500)
    
    def validate(self, data):
        """Validate search parameters"""
        if data.get('min_weight') and data.get('max_weight'):
            if data['min_weight'] > data['max_weight']:
                raise serializers.ValidationError(
                    "min_weight cannot be greater than max_weight"
                )
        
        if data.get('date_from') and data.get('date_to'):
            if data['date_from'] > data['date_to']:
                raise serializers.ValidationError(
                    "date_from cannot be later than date_to"
                )
        
        return data
```

# cargo\signals.py

```py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Cargo, CarrierRequest
from core.services.telegram import telegram_service
from django.db import transaction

User = get_user_model()

@receiver(post_save, sender=Cargo)
def notify_cargo_changes(sender, instance, created, **kwargs):
    """Send notifications for cargo creation and changes"""
    # Skip if this is not a change or the transaction is being managed elsewhere
    if transaction.get_connection().in_atomic_block and not created:
        return
        
    # Determine action and recipients based on status and event
    if created:
        action = f"Новый груз создан: {instance.title}"
        
        # Notify different users based on cargo status
        if instance.status == Cargo.CargoStatus.PENDING_APPROVAL:
            # Notify managers about new cargo requiring approval
            managers = User.objects.filter(role='manager', is_active=True)
            if managers.exists():
                for manager in managers:
                    if manager.telegram_id:
                        telegram_service.send_notification.delay(
                            manager.telegram_id,
                            telegram_service.format_cargo_notification(instance, action)
                        )
            
        elif instance.status == Cargo.CargoStatus.PENDING:
            # Notify students about new cargo
            students = User.objects.filter(role='student', is_active=True)
            if students.exists():
                for student in students:
                    if student.telegram_id:
                        telegram_service.send_notification.delay(
                            student.telegram_id, 
                            telegram_service.format_cargo_notification(instance, action)
                        )
            
    elif hasattr(instance, '_original_status') and instance._original_status != instance.status:
        old_status = instance._original_status
        new_status = instance.status
        
        action = f"Статус груза изменен с {old_status} на {new_status}: {instance.title}"
        
        # Notify owner
        if instance.owner and instance.owner.telegram_id:
            telegram_service.send_notification.delay(
                instance.owner.telegram_id,
                telegram_service.format_cargo_notification(instance, action)
            )
            
        # Notify assigned carrier if status becomes assigned
        if new_status == Cargo.CargoStatus.ASSIGNED and instance.assigned_to and instance.assigned_to.telegram_id:
            telegram_service.send_notification.delay(
                instance.assigned_to.telegram_id,
                telegram_service.format_cargo_notification(instance, "Вам назначен груз")
            )
            
        # Notify managing student about status changes
        if instance.managed_by and instance.managed_by.telegram_id:
            telegram_service.send_notification.delay(
                instance.managed_by.telegram_id,
                telegram_service.format_cargo_notification(instance, action)
            )
            
        # Notify all students when cargo becomes manager_approved
        if new_status == Cargo.CargoStatus.MANAGER_APPROVED:
            students = User.objects.filter(role='student', is_active=True)
            if students.exists():
                for student in students:
                    if student.telegram_id:
                        telegram_service.send_notification.delay(
                            student.telegram_id,
                            telegram_service.format_cargo_notification(instance, "Новый груз доступен")
                        )

@receiver(pre_save, sender=Cargo)
def store_original_status(sender, instance, **kwargs):
    """Store original status before save for comparison in post_save"""
    if instance.pk:
        try:
            instance._original_status = Cargo.objects.get(pk=instance.pk).status
        except Cargo.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_delete, sender=Cargo)
def notify_cargo_deletion(sender, instance, **kwargs):
    """Send notifications when cargo is deleted"""
    action = f"Груз удален: {instance.title}"
    
    # Notify owner
    if instance.owner and instance.owner.telegram_id:
        telegram_service.send_notification.delay(
            instance.owner.telegram_id, 
            telegram_service.format_cargo_notification(instance, action)
        )
    
    # Notify carrier if assigned
    if instance.assigned_to and instance.assigned_to.telegram_id:
        telegram_service.send_notification.delay(
            instance.assigned_to.telegram_id,
            telegram_service.format_cargo_notification(instance, action)
        )
    
    # Notify managing student
    if instance.managed_by and instance.managed_by.telegram_id:
        telegram_service.send_notification.delay(
            instance.managed_by.telegram_id,
            telegram_service.format_cargo_notification(instance, action)
        )

@receiver(post_save, sender=CarrierRequest)
def notify_carrier_request_changes(sender, instance, created, **kwargs):
    """Send notifications for carrier request creation and changes"""
    if created:
        action = "Новая заявка от перевозчика"
        
        # Notify students about new carrier request
        students = User.objects.filter(role='student', is_active=True)
        if students.exists():
            for student in students:
                if student.telegram_id:
                    telegram_service.send_notification.delay(
                        student.telegram_id,
                        telegram_service.format_carrier_notification(instance, action)
                    )
            
    elif hasattr(instance, '_original_status') and instance._original_status != instance.status:
        old_status = instance._original_status
        new_status = instance.status
        
        action = f"Статус заявки изменен с {old_status} на {new_status}"
        
        # Notify carrier about status changes
        if instance.carrier and instance.carrier.telegram_id:
            telegram_service.send_notification.delay(
                instance.carrier.telegram_id,
                telegram_service.format_carrier_notification(instance, action)
            )
            
        # Notify assigning student if request was assigned
        if instance.assigned_by and instance.assigned_by.telegram_id:
            telegram_service.send_notification.delay(
                instance.assigned_by.telegram_id,
                telegram_service.format_carrier_notification(instance, action)
            )
                
        # Notify cargo owner if request was accepted
        if new_status == CarrierRequest.RequestStatus.ACCEPTED and instance.assigned_cargo and instance.assigned_cargo.owner and instance.assigned_cargo.owner.telegram_id:
            telegram_service.send_notification.delay(
                instance.assigned_cargo.owner.telegram_id,
                telegram_service.format_carrier_notification(instance, "Перевозчик принял вашу заявку")
            )

@receiver(pre_save, sender=CarrierRequest)
def store_carrier_request_original_status(sender, instance, **kwargs):
    """Store original status before save for comparison in post_save"""
    if instance.pk:
        try:
            instance._original_status = CarrierRequest.objects.get(pk=instance.pk).status
        except CarrierRequest.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_delete, sender=CarrierRequest)
def notify_carrier_request_deletion(sender, instance, **kwargs):
    """Send notifications when carrier request is deleted"""
    action = f"Заявка перевозчика удалена"
    
    # Notify carrier
    if instance.carrier and instance.carrier.telegram_id:
        telegram_service.send_notification.delay(
            instance.carrier.telegram_id,
            telegram_service.format_carrier_notification(instance, action)
        )
    
    # Notify assigning student
    if instance.assigned_by and instance.assigned_by.telegram_id:
        telegram_service.send_notification.delay(
            instance.assigned_by.telegram_id,
            telegram_service.format_carrier_notification(instance, action)
        )
    
    # Notify cargo owner if request was assigned to a cargo
    if instance.assigned_cargo and instance.assigned_cargo.owner and instance.assigned_cargo.owner.telegram_id:
        telegram_service.send_notification.delay(
            instance.assigned_cargo.owner.telegram_id,
            telegram_service.format_carrier_notification(instance, action)
        )
```

# cargo\urls.py

```py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    CargoViewSet,
    CarrierRequestViewSet,ExternalCargoViewSet
)

router = DefaultRouter()
router.register(r'cargos', CargoViewSet, basename='cargo')
router.register(r'external', ExternalCargoViewSet, basename='external-cargo')
router.register(r'carrier-requests', CarrierRequestViewSet, basename='carrier-request')

urlpatterns = [
    path('', include(router.urls)),
]
```

# cargo\views.py

```py
from decimal import Decimal
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, OpenApiParameter

from users.models import User
from .models import Cargo, CarrierRequest, CargoDocument
from .serializers import (
    CargoSerializer,
    CargoListSerializer,
    CargoCreateSerializer,
    CargoUpdateSerializer,
    CargoAssignmentSerializer,
    CargoAcceptanceSerializer,
    CarrierRequestSerializer,
    CarrierRequestListSerializer,
    CarrierRequestCreateSerializer,
    CarrierRequestUpdateSerializer,
    ManagerCargoUpdateSerializer,
    ExternalCargoCreateSerializer
)
from .filters import CargoFilter
from core.permissions import (
    IsVerifiedUser,
    IsManager,
    IsObjectOwner,
    isStudent,
    IsCarrier,
    IsLogisticsCompany,
    IsCargoOwner
)
import hashlib
from drf_spectacular.types import OpenApiTypes
from django.conf import settings
from rest_framework.permissions import AllowAny

class ManagerCargoViewSet(viewsets.ModelViewSet):
    """ViewSet for manager operations on cargo"""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    serializer_class = ManagerCargoUpdateSerializer

    def get_queryset(self):
        """Filter queryset to show relevant cargos for managers"""
        return Cargo.objects.filter(
            Q(status=Cargo.CargoStatus.PENDING_APPROVAL) |
            Q(approved_by=self.request.user) |
            Q(status=Cargo.CargoStatus.MANAGER_APPROVED)
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a cargo"""
        cargo = self.get_object()
        serializer = CargoApprovalSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                cargo.approve(
                    manager=request.user,
                    notes=serializer.validated_data.get('approval_notes')
                )
                return Response(
                    {'status': 'Cargo approved successfully'},
                    status=status.HTTP_200_OK
                )
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a cargo"""
        cargo = self.get_object()
        serializer = CargoApprovalSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                cargo.reject(
                    manager=request.user,
                    notes=serializer.validated_data.get('approval_notes')
                )
                return Response(
                    {'status': 'Cargo rejected successfully'},
                    status=status.HTTP_200_OK
                )
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Get cargos pending manager approval"""
        queryset = self.get_queryset().filter(
            status=Cargo.CargoStatus.PENDING_APPROVAL
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def approved(self, request):
        """Get cargos approved by the current manager"""
        queryset = self.get_queryset().filter(
            status=Cargo.CargoStatus.MANAGER_APPROVED,
            approved_by=request.user
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class ExternalCargoViewSet(viewsets.GenericViewSet):
    """ViewSet for external cargo creation via API"""
    permission_classes = [AllowAny]
    # serializer_class = CargoSerializer

    @action(detail=False, methods=['post'])
    def create_external(self, request):
        """
        Create cargo entries from external API
        Requires authentication with API key and hash verification
        """
        try:
            # Extract data from request
            api_key = request.data.get('api_key')
            created_at = request.data.get('created_at')
            received_hash = request.data.get('hash')
            orders = request.data.get('orders', [])

            # Check for required fields
            if not all([api_key, created_at, received_hash, orders]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verify hash
            private_key = settings.PRIVATE_API_KEY
            calculated_hash = hashlib.md5(
                (private_key + api_key + str(created_at)).encode()
            ).hexdigest()
            
            if calculated_hash != received_hash:
                return Response(
                    {'error': 'Invalid authentication'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            created_cargos = []
            errors = []
            
            # Process each order
            for order_data in orders:
                try:
                    # Convert string numeric values to proper types
                    cleaned_data = self._convert_data_types(order_data)
                    
                    # Set source type to external API if not provided
                    if 'source_type' not in cleaned_data:
                        cleaned_data['source_type'] = 'api'
                    
                    cargo = Cargo.objects.create(
                        status='pending',  # Use string to match choices
                        **cleaned_data
                    )
                    
                    created_cargos.append({
                        'id': cargo.id,
                        'title': cargo.title,
                        'source_id': cargo.source_id
                    })
                    
                except Exception as e:
                    errors.append({
                        'order': order_data.get('source_id', 'Unknown'),
                        'error': str(e)
                    })
            
            return Response(
                {
                    'status': 'success',
                    'created': len(created_cargos),
                    'errors': len(errors),
                    'cargos': created_cargos,
                    'error_details': errors
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def _convert_data_types(self, data):
        """Convert string values to appropriate data types"""
        result = {}
        for key, value in data.items():
            if key in ['weight', 'volume', 'length', 'width', 'height', 'price'] and value:
                try:
                    result[key] = Decimal(str(value))
                except (ValueError, TypeError):
                    result[key] = None
            elif key == 'loading_date' and value:
                try:
                    result[key] = parse_date(str(value))
                except (ValueError, TypeError):
                    result[key] = None
            elif key in ['is_constant', 'is_ready']:
                result[key] = bool(value)
            else:
                result[key] = value
        return result
        
class CarrierRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier requests"""
    queryset = CarrierRequest.objects.all()
    serializer_class = CarrierRequestSerializer
    # permission_classes = [IsVerifiedUser, IsCarrier]
    permission_classes = [IsVerifiedUser]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    search_fields = [
        'loading_point', 'unloading_point',
        'carrier__username', 'notes'
    ]
    ordering_fields = ['created_at', 'ready_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'carrier':
            return queryset.filter(carrier=user)
        elif user.role == 'student':
            return queryset.filter(status='pending')
        elif user.is_staff:
            return queryset
            
        return queryset.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'create':
            return CarrierRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CarrierRequestUpdateSerializer
        elif self.action == 'list':
            return CarrierRequestListSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Create a new carrier request"""
        serializer.save(carrier=self.request.user)

    @extend_schema(
        description='Get matching cargos for carrier request',
        responses={200: CargoListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def matching_cargos(self, request, pk=None):
        """Get list of cargos matching this carrier request"""
        carrier_request = self.get_object()
        
        # Filter cargos based on matching criteria
        matching_cargos = Cargo.objects.filter(
            status='pending',
            loading_date__gte=carrier_request.ready_date,
            loading_point__icontains=carrier_request.loading_point,
            unloading_point__icontains=carrier_request.unloading_point
        )
        
        serializer = CargoListSerializer(matching_cargos, many=True)
        return Response(serializer.data)

class CargoViewSet(viewsets.ModelViewSet):
    """ViewSet for cargo management"""
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsVerifiedUser]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = CargoFilter
    search_fields = [
        'title', 'description',
        'loading_point', 'unloading_point'
    ]
    ordering_fields = [
        'created_at', 'loading_date',
        'price', 'views_count'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'carrier':
            # Carriers see pending and assigned cargos
            return queryset.filter(
                Q(status=Cargo.CargoStatus.PENDING) |
                Q(assigned_to=user)
            )
        elif user.role == 'student':
            # Students see manager-approved cargos
            # VIP students see all approved cargos, standard students see limited ones
            base_query = Q(status=Cargo.CargoStatus.MANAGER_APPROVED)
            if user.tariff == 'standard':
                 return queryset.filter(
                Q(status='pending') |
                Q(managed_by=user) | 
                Q(owner=user)
            )
            if user.tariff == 'vip':
                return queryset.filter(
                Q(status='pending') |
                Q(managed_by=user) | 
                Q(owner=user) | 
                Q(status=Cargo.CargoStatus.MANAGER_APPROVED)
            )
                # return queryset.filter(base_query)
            
            else:
                return queryset.none()

        elif user.role == 'cargo-owner':
            # Owners see their own cargos
            return queryset.filter(owner=user)
        elif user.role == 'logistics-company':
            # Companies see their own cargos
            return queryset.filter(owner=user)
        elif user.role == 'manager':
            # Managers see all cargos
            return queryset
        elif user.is_staff:
            return queryset
            
        return queryset.none()
            
        return queryset.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'create':
            return CargoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CargoUpdateSerializer
        elif self.action == 'list':
            return CargoListSerializer
        elif self.action == 'assign_carrier':
            return CargoAssignmentSerializer
        elif self.action == 'accept_assignment':
            return CargoAcceptanceSerializer
        return self.serializer_class
    
    def get_permissions(self):
        """Get custom permissions for different actions"""
        if self.action == 'create':
            permission_classes = [
                IsVerifiedUser,
                (IsCargoOwner | IsLogisticsCompany | isStudent)
            ]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsVerifiedUser, IsObjectOwner]
        else:
            permission_classes = [IsVerifiedUser]
        return [permission() for permission in permission_classes]

    @extend_schema(
        description='Get matching carrier requests for cargo',
        responses={200: CarrierRequestListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def matching_carriers(self, request, pk=None):
        """Get list of carrier requests matching this cargo"""
        cargo = self.get_object()
        
        # Filter carrier requests based on matching criteria
        matching_requests = CarrierRequest.objects.filter(
            status='pending',
            ready_date__lte=cargo.loading_date,
            loading_point__icontains=cargo.loading_point,
            unloading_point__icontains=cargo.unloading_point
        )
        
        serializer = CarrierRequestListSerializer(matching_requests, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Assign cargo to carrier',
        request=CargoAssignmentSerializer,
        responses={200: CargoSerializer}
    )
    @action(detail=True, methods=['post'])
    def assign_carrier(self, request, pk=None):
        """Assign cargo to a carrier through carrier request"""
        cargo = self.get_object()
        serializer = self.get_serializer(cargo, data=request.data)
        
        if serializer.is_valid():
            cargo = serializer.save()
            return Response(CargoSerializer(cargo).data)
            
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        description='Accept or reject cargo assignment',
        request=CargoAcceptanceSerializer,
        responses={200: CargoSerializer}
    )
    @action(detail=True, methods=['post'])
    def accept_assignment(self, request, pk=None):
        """Accept or reject cargo assignment"""
        cargo = self.get_object()
        serializer = self.get_serializer(cargo, data=request.data)
        
        if serializer.is_valid():
            cargo = serializer.save()
            return Response(CargoSerializer(cargo).data)
            
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def perform_create(self, serializer):
        """Create cargo and handle notifications"""
        cargo = serializer.save(owner=self.request.user)

        # Create notifications based on cargo status
        if cargo.status == Cargo.CargoStatus.PENDING_APPROVAL:
            self.notify_managers(cargo)
        elif cargo.status == Cargo.CargoStatus.MANAGER_APPROVED:
            self.notify_students(cargo)

    def notify_managers(self, cargo):
        """Notify managers about new cargo requiring approval"""
        from core.models import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        managers = User.objects.filter(role='manager', is_active=True)
        for manager in managers:
            Notification.objects.create(
                user=manager,
                type='cargo',
                message=f'New cargo requires approval: {cargo.title}',
                content_object=cargo
            )

    def notify_students(self, cargo):
        """Notify students about new approved cargo"""
        from core.models import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        students = User.objects.filter(role='student', is_active=True)
        for student in students:
            Notification.objects.create(
                user=student,
                type='cargo',
                message=f'New cargo available: {cargo.title}',
                content_object=cargo
            )

    def perform_update(self, serializer):
        """Update cargo and handle notifications"""
        old_status = serializer.instance.status
        cargo = serializer.save()
        new_status = cargo.status
        
        from core.models import Notification
        
        # Handle status change notifications
        if old_status != new_status:
            # Notify owner about status changes
            Notification.objects.create(
                user=cargo.owner,
                type='cargo',
                message=f'Cargo status changed to {new_status}: {cargo.title}',
                content_object=cargo
            )
            
            # Notify assigned carrier about status changes
            if cargo.assigned_to:
                Notification.objects.create(
                    user=cargo.assigned_to,
                    type='cargo',
                    message=f'Cargo status changed to {new_status}: {cargo.title}',
                    content_object=cargo
                )
            
            # Notify managing student about status changes
            if cargo.managed_by:
                Notification.objects.create(
                    user=cargo.managed_by,
                    type='cargo',
                    message=f'Cargo status changed to {new_status}: {cargo.title}',
                    content_object=cargo
                )

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increment cargo view counter"""
        cargo = self.get_object()
        cargo.views_count += 1
        cargo.save(update_fields=['views_count'])
        return Response({'status': 'view count updated'})

    @extend_schema(
        description='Search for cargos with advanced filters',
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                description='Search query'
            ),
            OpenApiParameter(
                name='from_location',
                type=str,
                description='Loading point'
            ),
            OpenApiParameter(
                name='to_location',
                type=str,
                description='Unloading point'
            ),
            OpenApiParameter(
                name='date_from',
                type=str,
                description='Loading date from'
            ),
            OpenApiParameter(
                name='date_to',
                type=str,
                description='Loading date to'
            ),
            OpenApiParameter(
                name='vehicle_type',
                type=str,
                description='Vehicle type'
            ),
        ],
        responses={200: CargoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced cargo search"""
        queryset = self.get_queryset()
        
        # Apply text search
        q = request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q)
            )
        
        # Filter by location
        from_location = request.query_params.get('from_location', '')
        if from_location:
            queryset = queryset.filter(
                loading_point__icontains=from_location
            )
            
        to_location = request.query_params.get('to_location', '')
        if to_location:
            queryset = queryset.filter(
                unloading_point__icontains=to_location
            )
        
        # Filter by date range
        date_from = request.query_params.get('date_from', '')
        if date_from:
            queryset = queryset.filter(loading_date__gte=date_from)
            
        date_to = request.query_params.get('date_to', '')
        if date_to:
            queryset = queryset.filter(loading_date__lte=date_to)
        
        # Filter by vehicle type
        vehicle_type = request.query_params.get('vehicle_type', '')
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        
        # Order results
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Get cargo statistics',
        responses={200: {'type': 'object'}}
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get cargo statistics"""
        user = request.user
        queryset = self.get_queryset()
        
        stats = {
            'total_active': queryset.filter(status='pending').count(),
            'total_in_progress': queryset.filter(status='in_progress').count(),
            'total_completed': queryset.filter(status='completed').count(),
        }
        
        if user.role == 'carrier':
            stats.update({
                'assigned_to_me': queryset.filter(assigned_to=user).count(),
                'completed_by_me': queryset.filter(
                    assigned_to=user,
                    status='completed'
                ).count(),
            })
        elif user.role == 'student':
            stats.update({
                'managed_by_me': queryset.filter(managed_by=user).count(),
                'pending_assignment': queryset.filter(
                    status='pending',
                    managed_by=None
                ).count(),
            })
        elif user.role in ['cargo-owner', 'logistics-company']:
            stats.update({
                'my_active': queryset.filter(
                    owner=user,
                    status__in=['pending', 'in_progress']
                ).count(),
                'my_completed': queryset.filter(
                    owner=user,
                    status='completed'
                ).count(),
            })
            
        return Response(stats)
```

# core\admin.py

```py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Notification,
    Favorite,
    Rating,
    TelegramGroup,
    TelegramMessage,
    SearchFilter,
    Location
)



@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'level', 'latitude',
        'longitude', 'code', 'created_at'
    )
    list_filter = ('level', 'created_at')
    search_fields = ('name', 'code')
    ordering = ('name',)
    raw_id_fields = ('parent', 'country')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': (
                'name', 'level', 'latitude',
                'longitude', 'code', 'additional_data'
            )
        }),
        (_('Hierarchy'), {
            'fields': ('parent', 'country'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
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
```

# core\apps.py

```py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals  # Import signals when app is ready
```

# core\cache.py

```py
from django.core.cache import cache
from django.conf import settings
from .models import Location

CACHE_TTL = getattr(settings, 'LOCATION_CACHE_TTL', 60 * 60 * 24)  # 24 hours

def get_cached_countries():
    """Get list of countries from cache or database"""
    key = 'location_countries'
    countries = cache.get(key)
    
    if countries is None:
        countries = list(Location.objects.filter(level=1).values(
            'id', 'name', 'code', 'additional_data'
        ))
        cache.set(key, countries, CACHE_TTL)
    
    return countries

def get_cached_states(country_id):
    """Get states for a country from cache or database"""
    key = f'location_states_{country_id}'
    states = cache.get(key)
    
    if states is None:
        states = list(Location.objects.filter(
            level=2,
            country_id=country_id
        ).values('id', 'name', 'code', 'additional_data'))
        cache.set(key, states, CACHE_TTL)
    
    return states

def get_cached_cities(parent_id, is_state=True):
    """Get cities for a state or country from cache or database"""
    key = f'location_cities_{parent_id}'
    cities = cache.get(key)
    
    if cities is None:
        filter_kwargs = {
            'level': 3,
            'parent_id' if is_state else 'country_id': parent_id
        }
        cities = list(Location.objects.filter(**filter_kwargs).values(
            'id', 'name', 'latitude', 'longitude'
        ))
        cache.set(key, cities, CACHE_TTL)
    
    return cities

def invalidate_location_cache(location_id=None):
    """Invalidate location caches"""
    if location_id:
        location = Location.objects.get(id=location_id)
        if location.level == 1:  # Country
            cache.delete('location_countries')
            cache.delete(f'location_states_{location_id}')
            cache.delete(f'location_cities_{location_id}')
        elif location.level == 2:  # State
            cache.delete(f'location_states_{location.country_id}')
            cache.delete(f'location_cities_{location_id}')
        else:  # City
            cache.delete(f'location_cities_{location.parent_id}')
    else:
        # Invalidate all location caches
        cache.delete_pattern('location_*')
```

# core\handlers.py

```py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cargo.models import Cargo, CarrierRequest
from users.models import User
from core.services.telegram import telegram_service

@receiver(post_save, sender=Cargo)
def handle_cargo_notification(sender, instance, created, **kwargs):
    """Handle cargo notifications"""
    if created:
        action = "Новый груз создан"
    else:
        if not instance.tracker.has_changed('status'):
            return
        action = f"Статус груза изменен на {instance.get_status_display()}"

    # Determine recipients based on status and role
    recipients = []
    
    if instance.status == 'pending_approval':
        # Notify managers about new cargo
        recipients = User.objects.filter(role='manager', is_active=True)
    elif instance.status == 'manager_approved':
        # Notify students about approved cargo
        recipients = User.objects.filter(role='student', is_active=True)
    elif instance.status == 'assigned':
        # Notify assigned carrier
        if instance.assigned_to:
            recipients = [instance.assigned_to]
    
    # Send notifications
    notifications = [
        {
            'telegram_id': user.telegram_id,
            'message': telegram_service.format_cargo_message(action, instance)
        }
        for user in recipients if user.telegram_id
    ]
    
    if notifications:
        telegram_service.send_bulk_notifications.delay(notifications)

@receiver(post_save, sender=CarrierRequest)
def handle_carrier_request_notification(sender, instance, created, **kwargs):
    """Handle carrier request notifications"""
    if created:
        action = "Новая заявка от перевозчика"
    else:
        if not instance.tracker.has_changed('status'):
            return
        action = f"Статус заявки изменен на {instance.get_status_display()}"

    # Determine recipients
    recipients = []
    
    if instance.status == 'pending':
        # Notify students about new request
        recipients = User.objects.filter(role='student', is_active=True)
    elif instance.status == 'assigned':
        # Notify carrier about assignment
        recipients = [instance.carrier]
    elif instance.status in ['accepted', 'rejected']:
        # Notify assigning student
        if instance.assigned_by:
            recipients = [instance.assigned_by]

    # Send notifications
    notifications = [
        {
            'telegram_id': user.telegram_id,
            'message': telegram_service.format_carrier_request_message(action, instance)
        }
        for user in recipients if user.telegram_id
    ]
    
    if notifications:
        telegram_service.send_bulk_notifications.delay(notifications)

@receiver(post_delete, sender=Cargo)
def handle_cargo_deletion(sender, instance, **kwargs):
    """Handle cargo deletion notifications"""
    # Notify cargo owner
    if instance.owner and instance.owner.telegram_id:
        message = f"""
❌ <b>Груз удален</b>

<b>Груз:</b> {instance.title}
<b>Маршрут:</b> {instance.loading_point} ➡️ {instance.unloading_point}
"""
        telegram_service.send_notification.delay(
            instance.owner.telegram_id,
            message
        )
```

# core\management\commands\import_locations.py

```py
import os
import re
import psycopg2
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction, connection
from core.models import Location

# Настройка логгера
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import locations from world.sql into Location model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to world.sql file',
            default='world.sql'
        )
        parser.add_argument(
            '--batch-size',
            type=int, 
            help='Batch size for inserting data', 
            default=1000
        )
        parser.add_argument(
            '--countries-only',
            action='store_true',
            help='Import only countries'
        )
        parser.add_argument(
            '--states-only',
            action='store_true',
            help='Import only states'
        )
        parser.add_argument(
            '--cities-only',
            action='store_true',
            help='Import only cities'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip import if data already exists'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        batch_size = options['batch_size']
        countries_only = options['countries_only']
        states_only = options['states_only']
        cities_only = options['cities_only']
        skip_existing = options['skip_existing']
        
        if not os.path.exists(file_path):
            raise CommandError(f'File {file_path} does not exist')

        # Проверка наличия данных
        if skip_existing and Location.objects.exists():
            self.stdout.write('Locations already exist, skipping import.')
            return

        self.stdout.write('Starting import...')
        
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT'],
            )
            
            conn.autocommit = False  # Отключаем автоматические транзакции
            cursor = conn.cursor()
            
            # Импорт стран
            if not states_only and not cities_only:
                self._import_countries(cursor, file_path, batch_size)
                conn.commit()
                
            # Импорт штатов/регионов
            if not countries_only and not cities_only:
                self._import_states(cursor, file_path, batch_size)
                conn.commit()
                
            # Импорт городов
            if not countries_only and not states_only:
                self._import_cities(cursor, file_path, batch_size)
                conn.commit()
                
            self.stdout.write(self.style.SUCCESS('Successfully imported locations'))

        except Exception as e:
            if conn:
                conn.rollback()
            self.stdout.write(self.style.ERROR(f'Import failed: {str(e)}'))
            logger.exception("Import failed")
            raise CommandError(f'Import failed: {str(e)}')
        
        finally:
            if conn:
                conn.close()

    def _import_countries(self, cursor, file_path, batch_size):
        """Import countries from SQL file"""
        self.stdout.write('Importing countries...')
        
        try:
            # Создаем временную таблицу с ПРАВИЛЬНЫМ типом для iso2 - varchar вместо char
            cursor.execute("""
                DROP TABLE IF EXISTS temp_countries;
                CREATE TEMP TABLE temp_countries (
                    id bigint PRIMARY KEY,
                    name varchar(100) NOT NULL,
                    iso2 varchar(10),  -- Изменено с char(2) на varchar(10)
                    latitude numeric(10,8),
                    longitude numeric(11,8),
                    capital varchar(255),
                    currency_name varchar(255),
                    region varchar(255),
                    created_at timestamp,
                    updated_at timestamp
                )
            """)
            
            # Читаем и извлекаем данные о странах
            country_data = self._extract_data_from_sql(file_path, 'countries')
            
            # Вставляем данные пакетами
            for i in range(0, len(country_data), batch_size):
                batch = country_data[i:i+batch_size]
                self._insert_countries(cursor, batch)
                self.stdout.write(f"Inserted countries batch {i//batch_size + 1}, {len(batch)} rows")
            
            # Копируем данные из временной таблицы в Location
            cursor.execute("""
                INSERT INTO core_location (id, name, level, code, latitude, longitude, additional_data, created_at, updated_at)
                SELECT 
                    id, 
                    name, 
                    1 as level, 
                    SUBSTRING(iso2, 1, 10) as code,  -- Убедимся, что код не превышает 10 символов
                    latitude, 
                    longitude, 
                    json_build_object('capital', capital, 'currency', currency_name, 'region', region),
                    COALESCE(created_at, NOW()),
                    COALESCE(updated_at, NOW())
                FROM temp_countries
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """)
            
            inserted = cursor.rowcount
            self.stdout.write(f"Imported {inserted} countries")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing countries: {str(e)}"))
            logger.exception("Error importing countries")
            raise

    def _import_states(self, cursor, file_path, batch_size):
        """Import states/regions from SQL file"""
        self.stdout.write('Importing states/regions...')
        
        try:
            # Создаем временную таблицу
            cursor.execute("""
                DROP TABLE IF EXISTS temp_states;
                CREATE TEMP TABLE temp_states (
                    id bigint PRIMARY KEY,
                    name varchar(255) NOT NULL,
                    country_id bigint NOT NULL,
                    state_code varchar(255),
                    latitude numeric(10,8),
                    longitude numeric(11,8),
                    type varchar(191),
                    created_at timestamp,
                    updated_at timestamp
                )
            """)
            
            # Читаем и извлекаем данные о штатах
            state_data = self._extract_data_from_sql(file_path, 'states')
            
            # Вставляем данные пакетами
            total_inserted = 0
            for i in range(0, len(state_data), batch_size):
                try:
                    batch = state_data[i:i+batch_size]
                    inserted = self._insert_states(cursor, batch)
                    total_inserted += inserted
                    self.stdout.write(f"Inserted states batch {i//batch_size + 1}, {inserted} rows")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error in states batch {i//batch_size + 1}: {str(e)}"))
                    # Продолжаем со следующего пакета
                    cursor.execute("ROLLBACK")
            
            # Копируем данные из временной таблицы в Location
            cursor.execute("""
                INSERT INTO core_location (id, name, parent_id, country_id, level, code, latitude, longitude, additional_data, created_at, updated_at)
                SELECT 
                    s.id, 
                    s.name, 
                    s.country_id as parent_id, 
                    s.country_id as country_id, 
                    2 as level, 
                    s.state_code as code, 
                    s.latitude, 
                    s.longitude, 
                    json_build_object('type', s.type),
                    COALESCE(s.created_at, NOW()),
                    COALESCE(s.updated_at, NOW())
                FROM temp_states s
                JOIN core_location c ON s.country_id = c.id
                WHERE c.level = 1
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """)
            
            inserted = cursor.rowcount
            self.stdout.write(f"Imported {inserted} states/regions")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing states: {str(e)}"))
            logger.exception("Error importing states")
            raise

    def _import_cities(self, cursor, file_path, batch_size):
        """Import cities from SQL file"""
        self.stdout.write('Importing cities...')
        
        try:
            # Создаем временную таблицу
            cursor.execute("""
                DROP TABLE IF EXISTS temp_cities;
                CREATE TEMP TABLE temp_cities (
                    id bigint PRIMARY KEY,
                    name varchar(255) NOT NULL,
                    state_id bigint,
                    country_id bigint NOT NULL,
                    latitude numeric(10,8),
                    longitude numeric(11,8),
                    created_at timestamp,
                    updated_at timestamp
                )
            """)
            
            # Читаем и извлекаем данные о городах
            city_data = self._extract_data_from_sql(file_path, 'cities')
            
            # Вставляем данные пакетами
            total_inserted = 0
            for i in range(0, len(city_data), batch_size):
                try:
                    batch = city_data[i:i+batch_size]
                    inserted = self._insert_cities(cursor, batch)
                    total_inserted += inserted
                    self.stdout.write(f"Inserted cities batch {i//batch_size + 1}, {inserted} rows")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error in cities batch {i//batch_size + 1}: {str(e)}"))
                    # Продолжаем со следующего пакета
                    cursor.execute("ROLLBACK")
            
            # Импорт городов с привязкой к штатам
            cursor.execute("""
                INSERT INTO core_location (name, parent_id, country_id, level, latitude, longitude, created_at, updated_at)
                SELECT 
                    c.name, 
                    c.state_id as parent_id, 
                    c.country_id, 
                    3 as level,
                    c.latitude, 
                    c.longitude, 
                    COALESCE(c.created_at, NOW()),
                    COALESCE(c.updated_at, NOW())
                FROM temp_cities c
                JOIN core_location s ON c.state_id = s.id
                WHERE s.level = 2
                ON CONFLICT DO NOTHING
                RETURNING id
            """)
            
            inserted_with_state = cursor.rowcount
            self.stdout.write(f"Imported {inserted_with_state} cities with state reference")
            
            # Импорт городов без штатов, напрямую к странам
            cursor.execute("""
                INSERT INTO core_location (name, parent_id, country_id, level, latitude, longitude, created_at, updated_at)
                SELECT 
                    c.name, 
                    c.country_id as parent_id, 
                    c.country_id, 
                    3 as level,
                    c.latitude, 
                    c.longitude, 
                    COALESCE(c.created_at, NOW()),
                    COALESCE(c.updated_at, NOW())
                FROM temp_cities c
                LEFT JOIN core_location s ON c.state_id = s.id
                WHERE s.id IS NULL AND c.state_id IS NULL
                ON CONFLICT DO NOTHING
                RETURNING id
            """)
            
            inserted_without_state = cursor.rowcount
            self.stdout.write(f"Imported {inserted_without_state} cities without state reference")
            
            total_cities = inserted_with_state + inserted_without_state
            self.stdout.write(f"Total imported cities: {total_cities}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing cities: {str(e)}"))
            logger.exception("Error importing cities")
            raise

    def _extract_data_from_sql(self, file_path, table_name):
        """Extract data from SQL file for the specified table"""
        result = []
        pattern = r"INSERT INTO public\.{}\s+VALUES\s*\((.*?)\);".format(table_name)
        
        # Чтение файла построчно с объединением строк
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Находим все вставки для указанной таблицы
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            
            for match in matches:
                # Разделяем несколько значений INSERT
                values = match.split('), (')
                for value in values:
                    # Очищаем значение
                    value = value.strip()
                    if not value.startswith('('):
                        value = '(' + value
                    if not value.endswith(')'):
                        value = value + ')'
                    result.append(value)
        
        self.stdout.write(f"Extracted {len(result)} {table_name} from SQL file")
        return result

    def _insert_countries(self, cursor, countries_batch):
        """Insert batch of countries into temp table"""
        if not countries_batch:
            return 0
            
        values = []
        for country in countries_batch:
            # Преобразуем строку значений в кортеж
            try:
                # Примерная позиция нужных нам полей:
                # 0=id, 1=name, 4=iso2, 19=latitude, 20=longitude, 6=capital, 8=currency_name, 12=region, 23=created_at, 24=updated_at
                # Извлекаем из строки "VALUES (1, 'name', ...)"
                fields = self._split_sql_values(country)
                
                # Проверяем минимальное количество полей
                if len(fields) < 21:
                    continue
                
                country_values = [
                    fields[0],  # id
                    fields[1],  # name
                    fields[4] if fields[4] != 'NULL' else None,  # iso2
                    fields[19] if fields[19] != 'NULL' else None,  # latitude
                    fields[20] if fields[20] != 'NULL' else None,  # longitude
                    fields[6] if fields[6] != 'NULL' else None,  # capital
                    fields[8] if fields[8] != 'NULL' else None,  # currency_name
                    fields[12] if fields[12] != 'NULL' else None,  # region
                    fields[23] if len(fields) > 23 and fields[23] != 'NULL' else None,  # created_at
                    fields[24] if len(fields) > 24 and fields[24] != 'NULL' else None  # updated_at
                ]
                
                values.append(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", country_values).decode('utf-8'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing country: {str(e)}"))
        
        if not values:
            return 0
            
        # Вставляем все значения одним запросом
        query = """
            INSERT INTO temp_countries 
            (id, name, iso2, latitude, longitude, capital, currency_name, region, created_at, updated_at)
            VALUES {} 
            ON CONFLICT (id) DO NOTHING
        """.format(','.join(values))
        
        cursor.execute(query)
        return cursor.rowcount

    def _insert_states(self, cursor, states_batch):
        """Insert batch of states into temp table"""
        if not states_batch:
            return 0
            
        values = []
        for state in states_batch:
            try:
                # Примерная позиция нужных нам полей:
                # 0=id, 1=name, 2=country_id, 4=state_code, 7=latitude, 8=longitude, 6=type, 9=created_at, 10=updated_at
                fields = self._split_sql_values(state)
                
                # Проверяем минимальное количество полей
                if len(fields) < 9:
                    continue
                
                state_values = [
                    fields[0],  # id
                    fields[1],  # name
                    fields[2],  # country_id
                    fields[4] if fields[4] != 'NULL' else None,  # state_code
                    fields[7] if fields[7] != 'NULL' else None,  # latitude
                    fields[8] if fields[8] != 'NULL' else None,  # longitude
                    fields[6] if fields[6] != 'NULL' else None,  # type
                    fields[9] if len(fields) > 9 and fields[9] != 'NULL' else None,  # created_at
                    fields[10] if len(fields) > 10 and fields[10] != 'NULL' else None  # updated_at
                ]
                
                values.append(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s)", state_values).decode('utf-8'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing state: {str(e)}"))
        
        if not values:
            return 0
            
        # Вставляем все значения одним запросом
        query = """
            INSERT INTO temp_states 
            (id, name, country_id, state_code, latitude, longitude, type, created_at, updated_at)
            VALUES {} 
            ON CONFLICT (id) DO NOTHING
        """.format(','.join(values))
        
        cursor.execute(query)
        return cursor.rowcount

    def _insert_cities(self, cursor, cities_batch):
        """Insert batch of cities into temp table"""
        if not cities_batch:
            return 0
            
        values = []
        for city in cities_batch:
            try:
                # Примерная позиция нужных нам полей:
                # 0=id, 1=name, 2=state_id, 4=country_id, 6=latitude, 7=longitude, 8=created_at, 9=updated_at
                fields = self._split_sql_values(city)
                
                # Проверяем минимальное количество полей
                if len(fields) < 8:
                    continue
                
                city_values = [
                    fields[0],  # id
                    fields[1],  # name
                    fields[2] if fields[2] != 'NULL' else None,  # state_id
                    fields[4],  # country_id
                    fields[6] if fields[6] != 'NULL' else None,  # latitude
                    fields[7] if fields[7] != 'NULL' else None,  # longitude
                    fields[8] if len(fields) > 8 and fields[8] != 'NULL' else None,  # created_at
                    fields[9] if len(fields) > 9 and fields[9] != 'NULL' else None,  # updated_at
                ]
                
                values.append(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", city_values).decode('utf-8'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing city: {str(e)}"))
        
        if not values:
            return 0
            
        # Вставляем все значения одним запросом
        query = """
            INSERT INTO temp_cities 
            (id, name, state_id, country_id, latitude, longitude, created_at, updated_at)
            VALUES {} 
            ON CONFLICT (id) DO NOTHING
        """.format(','.join(values))
        
        cursor.execute(query)
        return cursor.rowcount

    def _split_sql_values(self, values_line):
        """
        Split SQL values line respecting quotes and nested parentheses
        Example: "1, 'text with, comma', NULL, (1,2,3)"
        """
        result = []
        current_value = ""
        in_quotes = False
        paren_level = 0
        
        # Удаляем внешние скобки
        values_line = values_line.strip('()')
        
        for char in values_line:
            if char == "'" and (len(current_value) == 0 or current_value[-1] != '\\'):
                in_quotes = not in_quotes
                current_value += char
            elif char == '(' and not in_quotes:
                paren_level += 1
                current_value += char
            elif char == ')' and not in_quotes:
                paren_level -= 1
                current_value += char
            elif char == ',' and not in_quotes and paren_level == 0:
                result.append(current_value.strip())
                current_value = ""
            else:
                current_value += char
                
        # Добавляем последнее значение
        if current_value:
            result.append(current_value.strip())
            
        return result
```

# core\models.py

```py
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
```

# core\permissions.py

```py
from rest_framework import permissions


class IsManager(permissions.BasePermission):
    """
    Allow access only to manager users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'manager'
        )
    
    def has_object_permission(self, request, view, obj):
        # Managers can modify any cargo objects
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'manager'
        )
    
class IsVerifiedUser(permissions.BasePermission):
    """
    Allow access only to verified users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_verified
        )
    
class isStudent(permissions.BasePermission):
    """
    Allow access only to students.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'student'
        )

class IsCarrier(permissions.BasePermission):
    """
    Allow access only to carriers.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'carrier'
        )

class IsCargoOwner(permissions.BasePermission):
    """
    Allow access only to cargo owners.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'cargo-owner'
        )

class IsLogisticsCompany(permissions.BasePermission):
    """
    Allow access only to logistics companies.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'logistics-company'
        )

class IsObjectOwner(permissions.BasePermission):
    """
    Allow access only to object owner.
    """
    def has_object_permission(self, request, view, obj):
        return bool(obj.owner == request.user)

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Allow full access to staff users, but only read access to others.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class IsVerifiedOrReadOnly(permissions.BasePermission):
    """
    Allow full access to verified users, but only read access to others.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_verified
        )
```

# core\serializers.py

```py
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import (
    Notification, Favorite, Rating, TelegramGroup,
    TelegramMessage, SearchFilter, Location
)
from users.serializers import UserProfileSerializer

class LocationListSerializer(serializers.ModelSerializer):
    """Simple serializer for location lists"""
    class Meta:
        model = Location
        fields = ['id', 'name', 'level', 'code']

class LocationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with hierarchy information"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    hierarchy = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'level', 'code',
            'parent_name', 'country_name',
            'latitude', 'longitude',
            'hierarchy', 'additional_data'
        ]
    
    def get_hierarchy(self, obj):
        return obj.get_hierarchy()

class LocationSearchSerializer(serializers.ModelSerializer):
    """Serializer for location search results"""
    distance = serializers.FloatField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'level',
            'latitude', 'longitude',
            'distance', 'full_name'
        ]

# Остальные существующие сериализаторы
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'message', 'is_read',
            'created_at', 'content_type', 'object_id'
        ]
        read_only_fields = ['created_at']

class FavoriteSerializer(serializers.ModelSerializer):
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(),
        slug_field='model'
    )
    
    class Meta:
        model = Favorite
        fields = [
            'id', 'content_type', 'object_id',
            'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate(self, data):
        """
        Validate that the object exists
        """
        try:
            content_type = data['content_type']
            model_class = content_type.model_class()
            model_class.objects.get(id=data['object_id'])
        except Exception:
            raise serializers.ValidationError(
                "Invalid object_id for the given content_type"
            )
        return data

class RatingSerializer(serializers.ModelSerializer):
    from_user = UserProfileSerializer(read_only=True)
    to_user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = [
            'id', 'from_user', 'to_user', 'score',
            'comment', 'created_at'
        ]
        read_only_fields = ['created_at']

class RatingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['to_user', 'score', 'comment']
    
    def validate_to_user(self, value):
        """
        Validate that users can't rate themselves
        """
        if value == self.context['request'].user:
            raise serializers.ValidationError(
                "You cannot rate yourself"
            )
        return value
    
    def create(self, validated_data):
        from_user = self.context['request'].user
        return Rating.objects.create(from_user=from_user, **validated_data)

class TelegramGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramGroup
        fields = [
            'id', 'telegram_id', 'name', 'description',
            'is_active', 'last_sync', 'created_at'
        ]
        read_only_fields = ['last_sync', 'created_at']

class TelegramMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramMessage
        fields = [
            'id', 'telegram_id', 'group', 'message_text',
            'processed', 'processed_at', 'created_at', 'cargo'
        ]
        read_only_fields = [
            'processed', 'processed_at', 'created_at', 'cargo'
        ]

class SearchFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilter
        fields = [
            'id', 'name', 'filter_data',
            'notifications_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        return SearchFilter.objects.create(user=user, **validated_data)

class SearchFilterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilter
        fields = ['name', 'filter_data', 'notifications_enabled']
```

# core\services\location.py

```py
from math import radians, sin, cos, sqrt, atan2
from typing import List, Optional, Dict, Any
from django.db.models import Q
from core.models import Location
from core.cache import (
    get_cached_countries,
    get_cached_states,
    get_cached_cities
)

class LocationService:
    @staticmethod
    def get_location_hierarchy(location_id: int) -> List[Dict[str, Any]]:
        """Get full location hierarchy from city up to country"""
        location = Location.objects.get(id=location_id)
        return location.get_hierarchy()
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1, lon1 = map(radians, [lat1, lon1])
        lat2, lon2 = map(radians, [lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def find_locations_in_radius(
        latitude: float,
        longitude: float,
        radius: float,
        level: int = 3
    ) -> List[Dict[str, Any]]:
        """Find all locations within specified radius"""
        locations = Location.objects.filter(level=level)
        
        results = []
        for location in locations:
            if location.latitude and location.longitude:
                distance = LocationService.calculate_distance(
                    latitude, longitude,
                    float(location.latitude),
                    float(location.longitude)
                )
                if distance <= radius:
                    results.append({
                        'id': location.id,
                        'name': location.name,
                        'distance': round(distance, 2),
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'full_name': location.full_name
                    })
        
        return sorted(results, key=lambda x: x['distance'])

    @staticmethod
    def search_locations(
        query: str,
        level: Optional[int] = None,
        country_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search locations by name with optional filters"""
        locations = Location.objects.all()
        
        if level is not None:
            locations = locations.filter(level=level)
        
        if country_id:
            locations = locations.filter(
                Q(id=country_id) |  # Country itself
                Q(country_id=country_id)  # States and cities
            )
        
        # Split query into words and create Q objects for each
        words = query.split()
        name_query = Q()
        for word in words:
            name_query |= Q(name__icontains=word)
        
        locations = locations.filter(name_query)[:limit]
        
        return [
            {
                'id': loc.id,
                'name': loc.name,
                'level': loc.level,
                'full_name': loc.full_name,
                'latitude': loc.latitude,
                'longitude': loc.longitude
            }
            for loc in locations
        ]

    @staticmethod
    def get_location_choices(
        level: int,
        parent_id: Optional[int] = None,
        country_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get location choices for dropdowns"""
        if level == 1:
            return get_cached_countries()
        elif level == 2 and country_id:
            return get_cached_states(country_id)
        elif level == 3:
            if parent_id:  # Cities of state
                return get_cached_cities(parent_id, is_state=True)
            elif country_id:  # Cities of country
                return get_cached_cities(country_id, is_state=False)
        return []

    @staticmethod
    def validate_location_path(
        city_id: Optional[int] = None,
        state_id: Optional[int] = None,
        country_id: Optional[int] = None
    ) -> bool:
        """Validate that locations form a valid path in hierarchy"""
        try:
            if city_id:
                city = Location.objects.get(id=city_id, level=3)
                if state_id and city.parent_id != state_id:
                    return False
                if country_id and city.country_id != country_id:
                    return False
                
            if state_id:
                state = Location.objects.get(id=state_id, level=2)
                if country_id and state.country_id != country_id:
                    return False
                
            return True
            
        except Location.DoesNotExist:
            return False
```

# core\services\telegram.py

```py
from typing import List, Dict, Any, Tuple, Union
import logging
import requests
from django.conf import settings
from celery import shared_task

logger = logging.getLogger(__name__)

class TelegramNotificationService:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id: str, message: str) -> bool:
        """Send message to a telegram chat"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False

    @staticmethod
    @shared_task
    def send_notification(telegram_id: str, message: str) -> bool:
        """Celery task to send notification to a user"""
        service = TelegramNotificationService()
        return service.send_message(telegram_id, message)

    @staticmethod
    @shared_task
    def send_bulk_messages(messages: List[Union[Dict[str, str], Tuple[str, str]]]) -> None:
        """Send multiple messages via Celery"""
        service = TelegramNotificationService()
        for msg in messages:
            # Handle both dict and tuple formats
            if isinstance(msg, dict):
                telegram_id = msg.get("telegram_id")
                message = msg.get("message")
            elif isinstance(msg, tuple) and len(msg) >= 2:
                telegram_id, message = msg[0], msg[1]
            else:
                logger.error(f"Invalid message format: {msg}")
                continue
                
            if telegram_id and message:
                service.send_message(telegram_id, message)

    def format_cargo_notification(self, cargo: Any, action: str) -> str:
        """Format a cargo notification message"""
        return f"""
🚛 <b>{action}</b>

<b>Груз:</b> {cargo.title}
<b>Маршрут:</b> {cargo.loading_point} ➡️ {cargo.unloading_point}
<b>Вес:</b> {cargo.weight} т
<b>Тип транспорта:</b> {cargo.get_vehicle_type_display()}
<b>Статус:</b> {cargo.get_status_display()}

👉 Перейдите в приложение для подробностей
"""

    def format_carrier_notification(self, request: Any, action: str) -> str:
        """Format a carrier request notification message"""
        return f"""
🚚 <b>{action}</b>

<b>Перевозчик:</b> {request.carrier.get_full_name()}
<b>Транспорт:</b> {request.vehicle.registration_number}
<b>Маршрут:</b> {request.loading_point} ➡️ {request.unloading_point}
<b>Статус:</b> {request.get_status_display()}

👉 Перейдите в приложение для подробностей
"""

    def notify_users(self, recipients: List[Any], message: str) -> None:
        """Send notification to multiple users"""
        # Create list of (telegram_id, message) tuples for users with telegram_id
        messages = [
            (user.telegram_id, message)
            for user in recipients
            if user.telegram_id
        ]
        
        # Send messages if we have any recipients
        if messages:
            self.send_bulk_messages.delay(messages)


telegram_service = TelegramNotificationService()
```

# core\signals.py

```py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from users.models import User
from .models import Notification
from cargo.models import Cargo, CarrierRequest
from .services.telegram import TelegramNotificationService
import asyncio

import logging
telegram_service = TelegramNotificationService()


logger = logging.getLogger(__name__)

@receiver(post_save, sender=Notification)
def send_telegram_notification(sender, instance, created, **kwargs):
    """Send notification to Telegram when new notification is created"""
    if not created:
        return
        
    try:
        # Get the related content object (Cargo or CarrierRequest)
        content_object = instance.content_object
        
        # Skip if no content object
        if not content_object:
            return
            
        # Format message based on content type
        if isinstance(content_object, Cargo):
            message = telegram_service.format_cargo_notification(
                content_object,
                instance.message
            )
        elif isinstance(content_object, CarrierRequest):
            message = telegram_service.format_carrier_notification(
                content_object,
                instance.message
            )
        else:
            message = instance.message
            
        # Get user's telegram ID
        telegram_id = instance.user.telegram_id
        
        # Send message asynchronously
        asyncio.create_task(
            telegram_service.send_message(telegram_id, message)
        )
        
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {str(e)}")


@receiver(post_save, sender=Cargo)
def notify_cargo_status_change(sender, instance, created, **kwargs):
    """Send notifications for cargo status changes"""
    if created:
        return
        
    # We can't use tracker since it's not configured
    # Instead, we'll check for status changes based on the "_original_status" 
    # attribute which is set in pre_save in cargo/signals.py
    if hasattr(instance, '_original_status') and instance._original_status != instance.status:
        old_status = instance._original_status
        new_status = instance.status
        
        # Determine who should be notified
        recipients = []
        action = ""
        
        if new_status == 'pending_approval':
            # Notify managers
            recipients = User.objects.filter(
                role='manager',
                is_active=True,
                telegram_id__isnull=False
            )
            action = f"Новый груз требует проверки: {instance.title}"
            
        elif new_status == 'manager_approved':
            # Notify students
            recipients = User.objects.filter(
                role='student',
                is_active=True,
                telegram_id__isnull=False
            )
            action = f"Новый груз доступен: {instance.title}"
            
        elif new_status == 'assigned':
            # Notify carrier
            if instance.assigned_to and instance.assigned_to.telegram_id:
                recipients = [instance.assigned_to]
                action = f"Вам назначен груз: {instance.title}"

        # Send notifications via Telegram
        if recipients and action:
            for recipient in recipients:
                if recipient.telegram_id:
                    telegram_service.send_notification.delay(
                        recipient.telegram_id, 
                        telegram_service.format_cargo_notification(instance, action)
                    )

@receiver(post_save, sender=CarrierRequest)
def notify_carrier_request_status_change(sender, instance, created, **kwargs):
    """Send notifications for carrier request status changes"""
    if created:
        return
        
    if hasattr(instance, '_original_status') and instance._original_status != instance.status:
        old_status = instance._original_status
        new_status = instance.status
        
        recipients = []
        action = ""
        
        if new_status == 'assigned':
            if instance.carrier and instance.carrier.telegram_id:
                recipients = [instance.carrier]
                action = "Вам назначен груз"
                
        elif new_status in ['accepted', 'rejected']:
            if instance.assigned_by and instance.assigned_by.telegram_id:
                recipients = [instance.assigned_by]
                action = f"Перевозчик {'принял' if new_status == 'accepted' else 'отклонил'} назначенный груз"

        # Send notifications via Telegram
        if recipients and action:
            for recipient in recipients:
                if recipient.telegram_id:
                    telegram_service.send_notification.delay(
                        recipient.telegram_id,
                        telegram_service.format_carrier_notification(instance, action)
                    )
```

# core\tasks.py

```py
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
```

# core\urls.py

```py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    FavoriteViewSet,
    RatingViewSet,
    TelegramGroupViewSet,
    TelegramMessageViewSet,
    SearchFilterViewSet,
    LocationViewSet
)

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'telegram-groups', TelegramGroupViewSet)
router.register(r'telegram-messages', TelegramMessageViewSet)
router.register(r'search-filters', SearchFilterViewSet, basename='search-filter')
router.register(r'locations', LocationViewSet, basename='location')

urlpatterns = [
    path('', include(router.urls)),
]
```

# core\views.py

```py
from rest_framework import viewsets, status, permissions,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import (
    Notification, Favorite, Rating, TelegramGroup,
    TelegramMessage, SearchFilter
)
from .serializers import (
    NotificationSerializer, FavoriteSerializer, RatingSerializer,
    RatingCreateSerializer, TelegramGroupSerializer,
    TelegramMessageSerializer, SearchFilterSerializer,
    SearchFilterUpdateSerializer
)
from .permissions import IsVerifiedUser, IsStaffOrReadOnly
from django.db.models import F, FloatField
from django.db.models.functions import Power, Sqrt
from django.contrib.postgres.search import SearchVector, SearchQuery
from .models import Location
from .serializers import (
    LocationListSerializer,
    LocationDetailSerializer,
    LocationSearchSerializer
)

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LocationListSerializer
        if self.action in ['nearest', 'search']:
            return LocationSearchSerializer
        return LocationDetailSerializer

    @action(detail=False)
    def countries(self, request):
        """Get list of countries"""
        countries = Location.objects.filter(level=1)
        serializer = self.get_serializer(countries, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def states(self, request):
        """Get states/regions for a country"""
        country_id = request.query_params.get('country_id')
        if not country_id:
            return Response({'error': 'country_id parameter is required'}, status=400)
            
        states = Location.objects.filter(
            level=2,
            country_id=country_id
        )
        serializer = self.get_serializer(states, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def cities(self, request):
        """Get cities for a state or country"""
        state_id = request.query_params.get('state_id')
        country_id = request.query_params.get('country_id')
        
        if not (state_id or country_id):
            return Response(
                {'error': 'Either state_id or country_id parameter is required'},
                status=400
            )
            
        cities = Location.objects.filter(level=3)
        if state_id:
            cities = cities.filter(parent_id=state_id)
        elif country_id:
            cities = cities.filter(country_id=country_id)
            
        serializer = self.get_serializer(cities, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def nearest(self, request):
        """Find locations within specified radius"""
        try:
            lat = float(request.query_params.get('lat', 0))
            lon = float(request.query_params.get('lon', 0))
            radius = float(request.query_params.get('radius', 100))  # km
            level = int(request.query_params.get('level', 3))  # Default to cities
        except (TypeError, ValueError):
            return Response({'error': 'Invalid parameters'}, status=400)

        # Calculate distances using the Haversine formula approximation
        # This formula works well for PostgreSQL
        locations = Location.objects.filter(level=level).annotate(
            distance=Sqrt(
                Power(69.1 * (F('latitude') - lat), 2) +
                Power(69.1 * (F('longitude') - lon) * 0.73, 2)
            ).annotate(distance=FloatField())
        ).filter(distance__lte=radius).order_by('distance')

        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def search(self, request):
        """Search locations by name with full text search"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Search query is required'}, status=400)

        locations = Location.objects.annotate(
            search=SearchVector('name')
        ).filter(search=SearchQuery(query))

        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def children(self, request, pk=None):
        """Get direct child locations"""
        location = self.get_object()
        children = Location.objects.filter(parent=location)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)
    
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @extend_schema(
        description='Mark notification as read',
        responses={200: {'description': 'Notification marked as read'}}
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})
    
    @extend_schema(
        description='Mark all notifications as read',
        responses={200: {'description': 'All notifications marked as read'}}
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all notifications marked as read'})
    
    @extend_schema(
        description='Delete all notifications',
        responses={200: {'description': 'All notifications deleted'}}
    )
    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        self.get_queryset().delete()
        return Response({'status': 'all notifications deleted'})

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @extend_schema(
        description='Clear all favorites',
        responses={200: {'description': 'All favorites cleared'}}
    )
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        self.get_queryset().delete()
        return Response({'status': 'all favorites cleared'})

class RatingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsVerifiedUser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RatingCreateSerializer
        return RatingSerializer
    
    def get_queryset(self):
        if self.action == 'list':
            # Show ratings given to or by the current user
            return Rating.objects.filter(
                Q(from_user=self.request.user) |
                Q(to_user=self.request.user)
            )
        return Rating.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

class TelegramGroupViewSet(viewsets.ModelViewSet):
    queryset = TelegramGroup.objects.all()
    serializer_class = TelegramGroupSerializer
    permission_classes = [IsStaffOrReadOnly]
    
    @extend_schema(
        description='Sync messages from group',
        responses={200: {'description': 'Group sync initiated'}}
    )
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        group = self.get_object()
        # Start celery task for syncing
        from .tasks import sync_telegram_group
        sync_telegram_group.delay(group.id)
        return Response({'status': 'sync initiated'})

class TelegramMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TelegramMessage.objects.all()
    serializer_class = TelegramMessageSerializer
    permission_classes = [IsStaffOrReadOnly]
    
    @extend_schema(
        description='Process message',
        responses={200: {'description': 'Message processed'}}
    )
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        message = self.get_object()
        if message.processed:
            return Response(
                {'detail': 'Message already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start celery task for processing
        from .tasks import process_telegram_message
        process_telegram_message.delay(message.id)
        return Response({'status': 'processing initiated'})

class SearchFilterViewSet(viewsets.ModelViewSet):
    serializer_class = SearchFilterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SearchFilter.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SearchFilterUpdateSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @extend_schema(
        description='Toggle notifications for filter',
        responses={200: {'description': 'Notifications toggled'}}
    )
    @action(detail=True, methods=['post'])
    def toggle_notifications(self, request, pk=None):
        filter_obj = self.get_object()
        filter_obj.notifications_enabled = not filter_obj.notifications_enabled
        filter_obj.save()
        return Response({
            'status': 'notifications ' +
            ('enabled' if filter_obj.notifications_enabled else 'disabled')
        })
```

# logit_backend\asgi.py

```py
"""
ASGI config for logit_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logit_backend.settings')

application = get_asgi_application()

```

# logit_backend\celery.py

```py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logit_backend.settings')

app = Celery('logit_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

# logit_backend\celerybeat-schedule.py

```py
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
```

# logit_backend\schema.py

```py
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from drf_spectacular.utils import extend_schema, OpenApiExample

class TelegramAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'users.auth.TelegramAuthBackend'
    name = 'TelegramAuth'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Telegram WebApp authentication using JWT tokens'
        }

# Common response examples
SERVER_ERROR_RESPONSE = {
    'type': 'object',
    'properties': {
        'detail': {'type': 'string'}
    },
    'example': {'detail': 'Internal server error occurred'}
}

VALIDATION_ERROR_RESPONSE = {
    'type': 'object',
    'properties': {
        'field_name': {
            'type': 'array',
            'items': {'type': 'string'}
        }
    },
    'example': {
        'field_name': ['This field is required.']
    }
}

# Authentication examples
AUTH_SUCCESS_RESPONSE = {
    'type': 'object',
    'properties': {
        'access': {'type': 'string'},
        'refresh': {'type': 'string'},
        'user': {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'username': {'type': 'string'},
                'role': {'type': 'string'}
            }
        }
    },
    'example': {
        'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
        'user': {
            'id': '123456789',
            'username': 'john_doe',
            'role': 'carrier'
        }
    }
}

# User response examples
USER_PROFILE_RESPONSE = {
    'type': 'object',
    'properties': {
        'telegram_id': {'type': 'string'},
        'username': {'type': 'string'},
        'full_name': {'type': 'string'},
        'role': {'type': 'string'},
        'type': {'type': 'string'},
        'is_verified': {'type': 'boolean'},
        'rating': {'type': 'number'}
    },
    'example': {
        'telegram_id': '123456789',
        'username': 'john_doe',
        'full_name': 'John Doe',
        'role': 'carrier',
        'type': 'individual',
        'is_verified': True,
        'rating': 4.8
    }
}

# Cargo response examples
CARGO_RESPONSE = {
    'type': 'object',
    'properties': {
        'id': {'type': 'integer'},
        'title': {'type': 'string'},
        'description': {'type': 'string'},
        'weight': {'type': 'number'},
        'volume': {'type': 'number'},
        'loading_point': {'type': 'string'},
        'unloading_point': {'type': 'string'},
        'loading_date': {'type': 'string', 'format': 'date'},
        'status': {'type': 'string'},
        'owner': {'$ref': '#/components/schemas/UserProfile'},
        'created_at': {'type': 'string', 'format': 'date-time'}
    },
    'example': {
        'id': 1,
        'title': 'Steel Products',
        'description': 'Steel pipes for construction',
        'weight': 20.5,
        'volume': 40.0,
        'loading_point': 'Tashkent',
        'unloading_point': 'Moscow',
        'loading_date': '2024-02-01',
        'status': 'active',
        'owner': USER_PROFILE_RESPONSE['example'],
        'created_at': '2024-01-20T10:30:00Z'
    }
}

# Vehicle response examples
VEHICLE_RESPONSE = {
    'type': 'object',
    'properties': {
        'id': {'type': 'integer'},
        'registration_number': {'type': 'string'},
        'body_type': {'type': 'string'},
        'capacity': {'type': 'number'},
        'volume': {'type': 'number'},
        'owner': {'$ref': '#/components/schemas/UserProfile'},
        'is_verified': {'type': 'boolean'},
        'documents': {
            'type': 'array',
            'items': {'$ref': '#/components/schemas/VehicleDocument'}
        }
    },
    'example': {
        'id': 1,
        'registration_number': 'AA123BB',
        'body_type': 'tent',
        'capacity': 20.0,
        'volume': 86.0,
        'owner': USER_PROFILE_RESPONSE['example'],
        'is_verified': True,
        'documents': []
    }
}

# Common OpenAPI operation descriptions
OPERATIONS = {
    'list': {
        'summary': 'List objects',
        'description': 'Get a paginated list of objects'
    },
    'create': {
        'summary': 'Create object',
        'description': 'Create a new object'
    },
    'retrieve': {
        'summary': 'Get object',
        'description': 'Get object details by ID'
    },
    'update': {
        'summary': 'Update object',
        'description': 'Update object details'
    },
    'delete': {
        'summary': 'Delete object',
        'description': 'Delete an object'
    }
}

# Common OpenAPI parameters
COMMON_PARAMS = {
    'id': OpenApiExample(
        'ID',
        description='Object ID',
        value=1,
        parameter_only=True
    ),
    'page': OpenApiExample(
        'Page',
        description='Page number',
        value=1,
        parameter_only=True
    ),
    'limit': OpenApiExample(
        'Limit',
        description='Number of results per page',
        value=20,
        parameter_only=True
    )
}

# Common OpenAPI tags
TAGS = {
    'auth': 'Authentication',
    'users': 'Users',
    'cargo': 'Cargo',
    'vehicles': 'Vehicles',
    'core': 'Core'
}
```

# logit_backend\settings.py

```py
from datetime import timedelta
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-secret-key-for-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
PRIVATE_API_KEY = os.getenv('PRIVATE_API_KEY', 'testp')
EXTERNAL_API_KEY = os.getenv('EXTERNAL_API_KEY', 'testpb')

ALLOWED_HOSTS = ['*']
# os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,https://f623-84-54-80-95.ngrok-free.app,http://localhost:3000,').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'djoser',
    'drf_spectacular',
    'simple_history',
    
    # Local apps
    'users',
    'cargo',
    'vehicles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'logit_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'logit_backend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'logit_db'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'password'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'users.auth.TelegramAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    # 'EXCEPTION_HANDLER': 'logit_backend.core.exceptions.custom_exception_handler',
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'telegram_id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}

# CORS settings
CORS_ALLOWED_ORIGINS = [

    # '*',  # Allow all origins
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://e79e-213-230-76-173.ngrok-free.app',
    'https://d0af-94-230-229-138.ngrok-free.app',
    'https://f623-84-54-80-95.ngrok-free.app',      

]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'ngrok-skip-browser-warning',
]
# API Documentation settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Logit API',
    'DESCRIPTION': 'API for Logit logistics platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/',
}

# Celery settings
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Telegram Bot settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Security settings
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Content security policy
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Session settings
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False
    SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days
```

# logit_backend\urls.py

```py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

api_urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('users/', include('users.urls')),
    path('cargo/', include('cargo.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('core/', include('core.urls')),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

# logit_backend\wsgi.py

```py
"""
WSGI config for logit_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logit_backend.settings')

application = get_wsgi_application()

```

# manage.py

```py
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logit_backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

```

# media\user_documents\wavy-black-white-background.jpg

This is a binary file of the type: Image

# media\vehicle_documents\wavy-black-white-background_uKSy2Xa.jpg

This is a binary file of the type: Image

# media\vehicle_documents\wavy-black-white-background.jpg

This is a binary file of the type: Image

# README.md

```md
# Logit Platform - Logistics Management System ![Logit Platform](logit\app\blue.png) for local development u can do ts in order to not install postgres \`\`\` DATABASES = { 'default': { 'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3', } } \`\`\` ## Overview Logit Platform is a comprehensive logistics management system designed to streamline cargo transportation and logistics operations. The platform connects cargo owners, carriers, logistics companies, and logistics students in a unified ecosystem. ## 🌟 Key Features ### Authentication & User Management - Telegram WebApp authentication integration - Multi-role user system (Carriers, Cargo Owners, Logistics Companies, Students) - Profile management with document verification - Role-based access control - Language selection (Russian/Uzbek) ### Cargo Management - Create and manage cargo listings - Advanced cargo search with filtering - Real-time cargo status tracking - Multi-point route support - Automatic cargo matching with carriers - Price negotiation system - Document management for cargo ### Vehicle Management - Detailed vehicle registration and management - Vehicle document verification - Technical specifications tracking - Vehicle availability management - ADR/TIR/DOZVOL certification support - Vehicle inspection history ### Carrier Features - Vehicle fleet management - Cargo acceptance/rejection system - Real-time cargo notifications - Document upload and verification - Route planning and tracking - Availability management ### Student Features - Access to logistics training - Supervised cargo management - Learning progression tracking - Practice with real cargo listings - Mentor assignment system ### Platform Features - Real-time notifications - Favorites system - Rating and review system - Distance calculation - Advanced search filters - Document verification system - Multi-language support - Telegram group integration ## 🔧 Technology Stack ### Frontend - Next.js 14 (App Router) - TypeScript - TailwindCSS - Shadcn/ui Components - Telegram WebApp SDK - React Query - Axios - Framer Motion ### Backend - Django - Django REST Framework - PostgreSQL - Redis - Celery - JWT Authentication - Swagger/OpenAPI ## 📦 Installation ### Prerequisites - Node.js 18+ - Python 3.10+ - PostgreSQL - Redis - Telegram Bot Token ### Frontend Setup 1. Clone the repository: \`\`\`bash git clone https://github.com/HumoyunXujaev/logit-fronttt cd logit \`\`\` 2. Install dependencies: \`\`\`bash npm install \`\`\` 3. Create .env.local: \`\`\`env NEXT_PUBLIC_API_URL=http://localhost:8000/api NEXT_PUBLIC_TELEGRAM_BOT_TOKEN=your_telegram_bot_token \`\`\` 4. Run development server: \`\`\`bash npm run dev \`\`\` 5. setup ngrok (telegram web app doesn't work with localhost): \`\`\`bash ngrok http 3000 \`\`\` ### Backend Setup 1. Clone the repository: \`\`\`bash git clone https://github.com/HumoyunXujaev/logit-backend/ cd logit_backend \`\`\` 2. Create virtual environment: \`\`\`bash python -m venv venv source venv/bin/activate # Linux/Mac venv\Scripts\activate # Windows \`\`\` 3. Install dependencies: \`\`\`bash pip install -r requirements.txt \`\`\` 4. Create .env: \`\`\`env DJANGO_SECRET_KEY=your_secret_key DJANGO_DEBUG=True TELEGRAM_BOT_TOKEN=your_telegram_bot_token POSTGRES_DB=logit_db POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres POSTGRES_HOST=localhost POSTGRES_PORT=5432 \`\`\` 5. Run migrations: \`\`\`bash python manage.py makemigrations \`\`\` \`\`\`bash python manage.py migrate \`\`\` 6. Start development server: \`\`\`bash python manage.py runserver \`\`\` ## 🏗 Project Structure ### Backend Structure \`\`\` ├── cargo/ # Cargo management ├── vehicles/ # Vehicle management ├── users/ # User management ├── core/ # Core functionality └── logit_backend/ # Project settings \`\`\` ## 🚀 Features In Detail ### User Registration Flow 1. User opens Telegram bot 2. Selects language preference 3. Chooses user type (Individual/Legal Entity) 4. Selects role (Carrier/Cargo Owner/etc.) 5. Fills profile information 6. Uploads required documents 7. Awaits verification (if required) ### Cargo Management Flow 1. Cargo owner creates cargo listing 2. System processes and validates cargo information 3. Students can view and manage cargo listings 4. Students can match cargo with carriers 5. Carriers receive notification and can accept/reject 6. System tracks cargo status throughout delivery ### Vehicle Management Flow 1. Carrier registers vehicles 2. Uploads required documentation 3. System verifies vehicle information 4. Carrier can update vehicle availability 5. System matches vehicles with compatible cargo 6. Tracks vehicle status and documents expiry ### Student Learning Flow 1. Student registers with group information 2. Gets assigned to mentor 3. Can view and practice with real cargo listings 4. Manages cargo-carrier matching 5. Receives feedback from mentors 6. Tracks learning progress ## 🔐 Security - JWT-based authentication - Role-based access control - Document verification system - Secure file uploads - HTTPS encryption - Input validation - Rate limiting - Session management ## 📱 Mobile Responsiveness The platform is fully responsive and optimized for: - Desktop browsers - Mobile devices - Telegram WebApp - Tablets ## 🌐 API Documentation API documentation is available at: - Swagger UI: `/api/docs/` - ReDoc: `/api/redoc/` ## 🤝 Contributing Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests. ## 📄 License This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details ## 👥 Team - Product Owner: [Name] - Lead Developer: [Name] - Backend Developer: [Name] - Frontend Developer: [Name] - UI/UX Designer: [Name] ## 📞 Support For support, please contact: - Email: support@logit.com - Telegram: @logit_support - Website: https://logit.com/support ## 🌟 Acknowledgments - Telegram for WebApp SDK - Shadcn for UI components - All contributors and testers ## 🗺 Roadmap ### Phase 1 (Current) - Core platform functionality - Basic cargo management - Vehicle registration - User authentication ### Phase 2 (Planned) - Advanced analytics - Mobile applications - Real-time tracking - Payment integration - AI-powered matching ### Phase 3 (Future) - International expansion - Blockchain integration - IoT device support - Advanced automation ## ⚙ Configuration ### Environment Variables #### Frontend \`\`\`env NEXT_PUBLIC_API_URL= NEXT_PUBLIC_TELEGRAM_BOT_TOKEN= \`\`\` #### Backend \`\`\`env DJANGO_SECRET_KEY= DJANGO_DEBUG= TELEGRAM_BOT_TOKEN= POSTGRES_DB= POSTGRES_USER= POSTGRES_PASSWORD= POSTGRES_HOST= POSTGRES_PORT= \`\`\` --- **Note**: This project is actively maintained and regularly updated. For the latest features and changes, please check the CHANGELOG.md file.
```

# users\admin.py

```py
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
        'type', 'rating', 'is_active', 'is_verified', 'tariff'
    )
    list_filter = (
        'is_active', 'is_verified', 'role', 'type',
        'date_joined', 'last_login', 'tariff'
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
                'username', 'language_code', 
            )
        }),
        (_('Profile'), {
            'fields': (
                'type', 'role', 'preferred_language',
                'phone_number', 'whatsapp_number',
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
                'curator_name', 'end_date',  'tariff'
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
```

# users\apps.py

```py
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

```

# users\auth.py

```py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
import hashlib
import hmac
from django.conf import settings
from typing import Optional
import json
from django.utils import timezone

User = get_user_model()

class TelegramAuthBackend(BaseBackend):
    def authenticate(self, request, telegram_data=None) -> Optional[User]:
        """
        Authenticate user using Telegram WebApp data
        
        Args:
            request: HTTP request
            telegram_data: Dictionary with Telegram WebApp data
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        if not telegram_data:
            return None

        # Verify Telegram data authenticity
        if not self.verify_telegram_data(telegram_data):
            return None

        try:
            # Get user data
            user_data = json.loads(telegram_data.get('user', '{}'))
            telegram_id = str(user_data.get('id'))
            
            if not telegram_id:
                return None

            # Get or create user
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'username': user_data.get('username', ''),
                    'language_code': user_data.get('language_code', 'ru'),
                }
            )
            
            # Update last login
            if not created:
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])

            # Don't authenticate inactive users
            if not user.is_active:
                return None

            return user

        except Exception as e:
            # Log the error in production
            print(f"Authentication error: {e}")
            return None

    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(telegram_id=user_id)
        except User.DoesNotExist:
            return None

    def verify_telegram_data(self, telegram_data: dict) -> bool:
        """
        Verify authenticity of Telegram WebApp data
        
        Args:
            telegram_data: Dictionary with Telegram WebApp data
            
        Returns:
            bool: True if data is authentic, False otherwise
        """
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            if not bot_token:
                return False

            received_hash = telegram_data.get('hash')
            if not received_hash:
                return False

            # Remove hash from data to verify
            telegram_data_without_hash = telegram_data.copy()
            telegram_data_without_hash.pop('hash', None)

            # Sort data
            data_check_string = '\n'.join(
                f"{k}={v}" for k, v in sorted(telegram_data_without_hash.items())
            )

            # Create secret key
            secret_key = hmac.new(
                key=b'WebAppData',
                msg=bot_token.encode(),
                digestmod=hashlib.sha256
            ).digest()

            # Calculate hash
            calculated_hash = hmac.new(
                key=secret_key,
                msg=data_check_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()

            return calculated_hash == received_hash

        except Exception as e:
            print(f"Verification error: {e}")
            return False

    def validate_auth_data(self, auth_data: dict) -> bool:
        """
        Additional validation of authentication data
        
        Args:
            auth_data: Dictionary with authentication data
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            required_fields = ['id', 'first_name']
            user_data = json.loads(auth_data.get('user', '{}'))
            
            return all(user_data.get(field) for field in required_fields)
            
        except Exception:
            return False
```

# users\models.py

```py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from django.core.validators import MaxValueValidator, MinValueValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, telegram_id, **extra_fields):
        if not telegram_id:
            raise ValueError(_('The Telegram ID must be set'))
        
        user = self.model(telegram_id=telegram_id, **extra_fields)
        user.set_unusable_password()  # User doesn't need a password
        user.save(using=self._db)
        return user

    def create_superuser(self, telegram_id, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        return self.create_user(telegram_id, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    class UserType(models.TextChoices):
        INDIVIDUAL = 'individual', _('Individual')
        LEGAL = 'legal', _('Legal Entity')

    class UserRole(models.TextChoices):
        STUDENT = 'student', _('Student')
        CARRIER = 'carrier', _('Carrier')
        CARGO_OWNER = 'cargo-owner', _('Cargo Owner')
        LOGISTICS_COMPANY = 'logistics-company', _('Logistics Company')
        TRANSPORT_COMPANY = 'transport-company', _('Transport Company')
        LOGIT_TRANS = 'logit-trans', _('Logit Trans')
        MANAGER = 'manager', _('Manager')

    class Language(models.TextChoices):
        RUSSIAN = 'ru', _('Russian')
        UZBEK = 'uz', _('Uzbek')

    class StudentTariff(models.TextChoices):
        STANDARD = 'standard', _('Standard Pro')
        VIP = 'vip', _('VIP Pro')

    # Basic User Fields
    telegram_id = models.CharField(_('Telegram ID'), max_length=100, unique=True, primary_key=True)
    first_name = models.CharField(_('First Name'), max_length=255)
    last_name = models.CharField(_('Last Name'), max_length=255, blank=True)
    username = models.CharField(_('Username'), max_length=255, blank=True)
    language_code = models.CharField(_('Language Code'), max_length=10, blank=True)
    
    # System Fields
    is_active = models.BooleanField(_('Active'), default=True)
    is_staff = models.BooleanField(_('Staff status'), default=False)
    is_verified = models.BooleanField(_('Verified'), default=False)
    date_joined = models.DateTimeField(_('Date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('Last login'), null=True, blank=True)
    
    # Profile Fields
    type = models.CharField(max_length=20, choices=UserType.choices, null=True, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, null=True, blank=True)
    preferred_language = models.CharField(max_length=2, choices=Language.choices, default=Language.RUSSIAN)
    
    # Contact Information
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    
    # Company Information
    company_name = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    registration_certificate = models.FileField(upload_to='certificates/', null=True, blank=True)
    
    # Student Information
    student_id = models.CharField(max_length=50, null=True, blank=True)
    group_name = models.CharField(max_length=100, null=True, blank=True)
    study_language = models.CharField(max_length=50, null=True, blank=True)
    curator_name = models.CharField(max_length=100, null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    tariff = models.CharField(max_length=20, choices=StudentTariff.choices, null=True, blank=True)

    # Verification Fields
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_status = models.CharField(max_length=50, null=True, blank=True)
    verification_notes = models.TextField(null=True, blank=True)
    verified_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_users'
    )
    
    # Rating
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ]
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'telegram_id'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.telegram_id})"

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def update_rating(self):
        """Update user's rating based on received ratings"""
        from core.models import Rating
        ratings = Rating.objects.filter(to_user=self)
        if ratings.exists():
            avg_rating = ratings.aggregate(models.Avg('score'))['score__avg']
            self.rating = round(avg_rating, 2)
            self.save(update_fields=['rating'])

class UserDocument(models.Model):
    """Model for storing user documents like licenses, certificates etc."""
    
    class DocumentType(models.TextChoices):
        DRIVER_LICENSE = 'driver_license', _('Driver License')
        PASSPORT = 'passport', _('Passport')
        COMPANY_CERTIFICATE = 'company_certificate', _('Company Certificate')
        OTHER = 'other', _('Other')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    type = models.CharField(max_length=50, choices=DocumentType.choices)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='user_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verified_documents'
    )
    notes = models.TextField(null=True, blank=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['verified']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.type} - {self.title}"
```

# users\serializers.py

```py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserDocument
from drf_spectacular.utils import extend_schema_field
from django.utils import timezone
from datetime import datetime
import pytz

User = get_user_model()

# Create a minimal UserProfile serializer for UserDocument
class BasicUserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['telegram_id', 'username', 'full_name']

class UserDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    verified_by = BasicUserProfileSerializer(read_only=True)

    class Meta:
        model = UserDocument
        fields = [
            'id', 'type', 'title', 'file', 'file_url',
            'uploaded_at', 'verified', 'verified_at',
            'verified_by', 'notes'
        ]
        read_only_fields = ['uploaded_at', 'verified', 'verified_at', 'verified_by']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
        return None
    
# class UserDocumentSerializer(serializers.ModelSerializer):

#     file_url = serializers.SerializerMethodField()
#     verified_by = UserProfileSerializer(read_only=True)

#     class Meta:
#         model = UserDocument
#         fields = [
#             'id', 'type', 'title', 'file', 'file_url',
#             'uploaded_at', 'verified', 'verified_at',
#             'verified_by', 'notes'
#         ]
#         read_only_fields = ['uploaded_at', 'verified', 'verified_at', 'verified_by']
    
#     def get_file_url(self, obj):
#         if obj.file:
#             request = self.context.get('request')
#             if request is not None:
#                 return request.build_absolute_uri(obj.file.url)
#         return None
    
class TelegramAuthSerializer(serializers.Serializer):
    hash = serializers.CharField(required=True)
    user = serializers.JSONField(required=True)
    auth_date = serializers.IntegerField(required=True)

    def validate_auth_date(self, value):
        """Validate that auth_date is not too old"""
        # Convert timestamp to timezone-aware datetime
        auth_timestamp = datetime.fromtimestamp(value, tz=pytz.UTC)
        now = timezone.now()
        
        # Calculate time difference
        time_difference = now - auth_timestamp
        
        # Check if auth_date is not older than 1 day
        if time_difference.days > 1:
            raise serializers.ValidationError(
                "Authentication data has expired"
            )
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    documents = UserDocumentSerializer(many=True, read_only=True)
    rating_count = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'telegram_id', 'username', 'full_name', 'type', 'role',
            'preferred_language', 'phone_number', 'whatsapp_number',
            'company_name', 'position', 'student_id', 'group_name',
            'study_language', 'curator_name', 'end_date', 'rating',
            'rating_count', 'is_verified', 'verification_date',
            'documents', 'date_joined', 'last_login', 'tariff'
        ]
        read_only_fields = [
            'telegram_id', 'rating', 'is_verified',
            'verification_date', 'date_joined', 'last_login'
        ]
    
    @extend_schema_field({'type': 'integer'})
    def get_rating_count(self, obj) -> int:
        return obj.ratings_received.count()
    
    # def get_rating_count(self, obj):
    #     return obj.ratings_received.count()


    
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'phone_number', 'whatsapp_number', 'preferred_language',
            'company_name', 'position', 'type', 'role',
            'student_id', 'group_name', 'study_language',
            'curator_name', 'end_date', 'tariff'
        ]
    
    def validate(self, data):
        """
        Validate based on user type and role
        """
        user_type = data.get('type')
        user_role = data.get('role')
        
        if user_type == 'legal':
            if not data.get('company_name'):
                raise serializers.ValidationError({
                    "company_name": "Company name is required for legal entities"
                })
                
        if user_role == 'student':
            required_fields = ['student_id', 'group_name', 'study_language']
            missing_fields = [
                field for field in required_fields 
                if not data.get(field)
            ]
            if missing_fields:
                raise serializers.ValidationError({
                    field: "This field is required for students"
                    for field in missing_fields
                })
                
        if user_role in ['carrier', 'transport-company']:
            if not data.get('phone_number'):
                raise serializers.ValidationError({
                    "phone_number": "Phone number is required for carriers"
                })
                
        return data

class UserDocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDocument
        fields = ['type', 'title', 'file']
    
    def validate(self, data):
        """
        Validate document type based on user role
        """
        user = self.context['request'].user
        doc_type = data.get('type')
        
        if user.role == 'carrier' and doc_type != 'driver_license':
            raise serializers.ValidationError(
                "Carriers can only upload driver licenses"
            )
            
        if user.role == 'student' and doc_type != 'passport':
            raise serializers.ValidationError(
                "Students can only upload passports"
            )
            
        return data

class UserVerificationSerializer(serializers.Serializer):
    is_verified = serializers.BooleanField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        instance.is_verified = validated_data['is_verified']
        if validated_data.get('notes'):
            instance.verification_notes = validated_data['notes']
        if validated_data['is_verified']:
            instance.verification_date = timezone.now()
        instance.save()
        return instance
```

# users\urls.py

```py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet

router = DefaultRouter()
router.register('', UserViewSet, basename='users')

urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
```

# users\views.py

```py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import (
    UserProfileSerializer,
    TelegramAuthSerializer,
    UserUpdateSerializer,
    UserDocumentSerializer,
    UserDocumentCreateSerializer,
    UserVerificationSerializer
)
from .models import UserDocument
from .auth import TelegramAuthBackend
from core.permissions import IsStaffOrReadOnly

User = get_user_model()

class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    telegram_backend = TelegramAuthBackend()
    
    def get_permissions(self):
        if self.action == 'telegram_auth':
            permission_classes = [permissions.AllowAny]
        elif self.action == 'register':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['verify_user', 'verify_document']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Register new user with both Telegram and profile data
        """
        try:
            with transaction.atomic():
                # Валидируем telegram данные
                telegram_serializer = TelegramAuthSerializer(data=request.data)
                telegram_serializer.is_valid(raise_exception=True)
                
                telegram_data = telegram_serializer.validated_data
                telegram_user = telegram_data['user']
                telegram_id = str(telegram_user['id'])
                
                # Проверяем существование пользователя
                if User.objects.filter(telegram_id=telegram_id).exists():
                    return Response(
                        {'detail': 'User already exists'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Получаем дополнительные данные пользователя
                user_data = request.data.get('userData', {})
                print(user_data)
                print(telegram_user)
                print(telegram_data)
                # Создаем пользователя с базовыми и дополнительными данными
                user = User.objects.create(
                    telegram_id=telegram_id,
                    username=telegram_user.get('username', ''),
                    first_name=telegram_user.get('first_name', ''),
                    last_name=telegram_user.get('last_name', ''),
                    language_code=telegram_user.get('language_code', 'ru'),
                    is_active=True,
                    type=user_data.get('type'),
                    role=user_data.get('role'),
                    tariff=user_data.get('tariff'),
                    preferred_language=user_data.get('preferred_language'),
                    phone_number=user_data.get('phoneNumber'),
                    whatsapp_number=user_data.get('whatsappNumber'),
                    company_name=user_data.get('companyName'),
                    position=user_data.get('position'),
                    registration_certificate=user_data.get('registrationCertificate'),
                    student_id=user_data.get('studentId'),
                    group_name=user_data.get('groupName'),
                    study_language=user_data.get('studyLanguage'),
                    curator_name=user_data.get('curatorName'),
                    end_date=user_data.get('endDate'),
                    is_verified=False,
                    date_joined=timezone.now(),
                    last_login=timezone.now()
                    # Добавьте другие поля из user_data
                )

                # Генерируем токены
                refresh = RefreshToken.for_user(user)
                refresh.set_exp(lifetime=timezone.timedelta(days=365))
                
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserProfileSerializer(user).data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            print(e)
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


    @extend_schema(
        description='Authenticate using Telegram WebApp data',
        request=TelegramAuthSerializer,
        responses={200: {'description': 'Returns JWT tokens if authentication successful'}}
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def telegram_auth(self, request):
        """
        Authenticate user through Telegram
        """
        try:
            serializer = TelegramAuthSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            telegram_data = serializer.validated_data
            telegram_id = str(telegram_data['user']['id'])
            
            # Try to find existing user
            try:
                user = User.objects.get(telegram_id=telegram_id)
            except User.DoesNotExist:
                # Return 404 to trigger registration flow
                return Response(
                    {'detail': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update last login for existing user
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            refresh.set_exp(lifetime=timezone.timedelta(days=365))
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data
            })
            
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        description='Get current user profile',
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        description='Update current user profile',
        request=UserUpdateSerializer,
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['put','patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """
        Update user profile
        """
        try:
            user = request.user
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            return Response(UserProfileSerializer(user).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        description='Upload user document',
        request=UserDocumentCreateSerializer,
        responses={201: UserDocumentSerializer}
    )
    @action(detail=False, methods=['post'])
    def upload_document(self, request):
        """Upload a user document"""
        serializer = UserDocumentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        document = serializer.save(user=request.user)
        
        return Response(
            UserDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        description='Get user documents',
        responses={200: UserDocumentSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def documents(self, request):
        """Get current user's documents"""
        documents = UserDocument.objects.filter(user=request.user)
        serializer = UserDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Verify user',
        request=UserVerificationSerializer,
        responses={200: UserProfileSerializer}
    )
    @action(detail=True, methods=['post'])
    def verify_user(self, request, pk=None):
        """Verify a user (admin only)"""
        user = self.get_object()
        serializer = UserVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.update(user, serializer.validated_data)
        
        return Response(UserProfileSerializer(updated_user).data)

    @extend_schema(
        description='Verify document',
        responses={200: UserDocumentSerializer}
    )
    @action(detail=False, methods=['post'], url_path='documents/(?P<document_id>[^/.]+)/verify')
    def verify_document(self, request, document_id=None):
        """Verify a user document (admin only)"""
        document = UserDocument.objects.get(id=document_id)
        document.verified = True
        document.verified_at = timezone.now()
        document.verified_by = request.user
        document.save()
        
        return Response(UserDocumentSerializer(document).data)

    @extend_schema(
        description='Logout current user',
        responses={200: {'description': 'User logged out successfully'}}
    )
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Logout current user"""
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out'})
        except Exception:
            return Response(
                {'detail': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
```

# vehicles\admin.py

```py
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
```

# vehicles\apps.py

```py
from django.apps import AppConfig


class VehiclesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vehicles'

```

# vehicles\filters.py

```py
import django_filters
from .models import Vehicle

class VehicleFilter(django_filters.FilterSet):
    min_capacity = django_filters.NumberFilter(
        field_name='capacity',
        lookup_expr='gte'
    )
    max_capacity = django_filters.NumberFilter(
        field_name='capacity',
        lookup_expr='lte'
    )
    min_volume = django_filters.NumberFilter(
        field_name='volume',
        lookup_expr='gte'
    )
    max_volume = django_filters.NumberFilter(
        field_name='volume',
        lookup_expr='lte'
    )
    
    location = django_filters.CharFilter(method='filter_location')
    has_valid_documents = django_filters.BooleanFilter(
        method='filter_valid_documents'
    )
    
    class Meta:
        model = Vehicle
        fields = {
            'body_type': ['exact', 'in'],
            'loading_type': ['exact', 'in'],
            'is_active': ['exact'],
            'is_verified': ['exact'],
            'adr': ['exact'],
            'dozvol': ['exact'],
            'tir': ['exact'],
            'registration_country': ['exact'],
        }
    
    def filter_valid_documents(self, queryset, name, value):
        """
        Filter vehicles by presence of verified documents
        """
        if value is True:
            return queryset.filter(
                documents__verified=True
            ).distinct()
        return queryset.exclude(
            documents__verified=True
        ).distinct()
    
    def filter_location(self, queryset, name, value):
        """
        Filter vehicles by current location
        based on latest availability record
        """
        if value:
            return queryset.filter(
                availability__location__icontains=value
            ).distinct()
        return queryset
```

# vehicles\models.py

```py
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Vehicle(models.Model):
    class BodyType(models.TextChoices):
        TENT = 'tent', _('Tent')
        REFRIGERATOR = 'refrigerator', _('Refrigerator')
        ISOTHERMAL = 'isothermal', _('Isothermal')
        CONTAINER = 'container', _('Container')
        CAR_CARRIER = 'car_carrier', _('Car Carrier')
        BOARD = 'board', _('Board')

    class LoadingType(models.TextChoices):
        RAMPS = 'ramps', _('Ramps')
        NO_DOORS = 'no_doors', _('No Doors')
        SIDE = 'side', _('Side Loading')
        TOP = 'top', _('Top Loading')
        HYDRO_BOARD = 'hydro_board', _('Hydro Board')
    
    # Basic information
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )
    body_type = models.CharField(
        max_length=20,
        choices=BodyType.choices
    )
    loading_type = models.CharField(
        max_length=20,
        choices=LoadingType.choices
    )
    
    # Capacity information
    capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Capacity in tons')
    )
    
    volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Volume in cubic meters')
    )
    
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Registration information
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        help_text=_('Vehicle registration number')
    )
    registration_country = models.CharField(
        max_length=2,
        help_text=_('ISO country code')
    )
    
    # Certifications and permissions
    adr = models.BooleanField(
        default=False,
        help_text=_('Has ADR certificate')
    )
    dozvol = models.BooleanField(
        default=False,
        help_text=_('Has DOZVOL')
    )
    tir = models.BooleanField(
        default=False,
        help_text=_('Has TIR')
    )
    license_number = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    
    # Status and dates
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_vehicles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verification_notes = models.TextField(
        null=True, 
        blank=True,
        help_text=_('Notes about vehicle verification')
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['owner']),
            models.Index(fields=['is_active', 'is_verified']),
            models.Index(fields=['body_type']),
        ]
        
    def __str__(self):
        return f"{self.registration_number} - {self.get_body_type_display()}"

class VehicleDocument(models.Model):
    class DocumentType(models.TextChoices):
        TECH_PASSPORT = 'tech_passport', _('Technical Passport')
        LICENSE = 'license', _('License')
        INSURANCE = 'insurance', _('Insurance')
        ADR_CERT = 'adr_cert', _('ADR Certificate')
        DOZVOL = 'dozvol', _('DOZVOL')
        TIR = 'tir', _('TIR')
        OTHER = 'other', _('Other')

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    type = models.CharField(
        max_length=20,
        choices=DocumentType.choices
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='vehicle_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Verification
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_vehicle_documents'
    )
    verification_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['vehicle', 'type']),
            models.Index(fields=['verified']),
            models.Index(fields=['expiry_date']),
        ]
        
    def __str__(self):
        return f"{self.vehicle} - {self.get_type_display()}"

class VehicleAvailability(models.Model):
    """Model for tracking vehicle availability"""
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='availability'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Vehicle availabilities'
        indexes = [
            models.Index(fields=['vehicle', 'start_date']),
            models.Index(fields=['location']),
        ]
        
    def __str__(self):
        return f"{self.vehicle} - {self.start_date}"

class VehicleInspection(models.Model):
    """Model for tracking vehicle inspections"""
    
    class InspectionType(models.TextChoices):
        TECHNICAL = 'technical', _('Technical')
        SAFETY = 'safety', _('Safety')
        INSURANCE = 'insurance', _('Insurance')
        OTHER = 'other', _('Other')

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='inspections'
    )
    type = models.CharField(
        max_length=20,
        choices=InspectionType.choices
    )
    inspection_date = models.DateField()
    expiry_date = models.DateField()
    inspector = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vehicle_inspections'
    )
    result = models.BooleanField()
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-inspection_date']
        indexes = [
            models.Index(fields=['vehicle', 'type']),
            models.Index(fields=['expiry_date']),
        ]
        
    def __str__(self):
        return f"{self.vehicle} - {self.get_type_display()} - {self.inspection_date}"
```

# vehicles\serializers.py

```py
from rest_framework import serializers
from django.utils import timezone
from .models import (
    Vehicle,
    VehicleDocument,
    VehicleAvailability,
    VehicleInspection
)
from users.serializers import UserProfileSerializer

class VehicleDocumentSerializer(serializers.ModelSerializer):
    verified_by = UserProfileSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleDocument
        fields = [
            'id', 'type', 'title', 'file', 'file_url',
            'uploaded_at', 'expiry_date',
            'verified', 'verified_at', 'verified_by',
            'verification_notes'
        ]
        read_only_fields = [
            'uploaded_at', 'verified',
            'verified_at', 'verified_by'
        ]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate_expiry_date(self, value):
        """Check that expiry date is not in the past"""
        if value and value < timezone.now().date():
            raise serializers.ValidationError(
                "Expiry date cannot be in the past"
            )
        return value

class VehicleInspectionSerializer(serializers.ModelSerializer):
    inspector = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = VehicleInspection
        fields = [
            'id', 'type', 'inspection_date',
            'expiry_date', 'inspector', 'result',
            'notes', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate(self, data):
        """
        Check that inspection_date is not in future and
        expiry_date is after inspection_date
        """
        if data['inspection_date'] > timezone.now().date():
            raise serializers.ValidationError(
                "Inspection date cannot be in the future"
            )
        if data['expiry_date'] <= data['inspection_date']:
            raise serializers.ValidationError(
                "Expiry date must be after inspection date"
            )
        return data

class VehicleAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleAvailability
        fields = [
            'id', 'start_date', 'end_date',
            'location', 'note', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate(self, data):
        """
        Check that start_date is not in past and
        end_date is after start_date if provided
        """
        if data['start_date'] < timezone.now().date():
            raise serializers.ValidationError(
                "Start date cannot be in the past"
            )
        if data.get('end_date') and data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                "End date must be after start date"
            )
        return data

class VehicleSerializer(serializers.ModelSerializer):
    """Full vehicle serializer with all details"""
    owner = UserProfileSerializer(read_only=True)
    documents = VehicleDocumentSerializer(many=True, read_only=True)
    inspections = VehicleInspectionSerializer(many=True, read_only=True)
    availability = VehicleAvailabilitySerializer(many=True, read_only=True)
    verified_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner', 'body_type', 'loading_type',
            'capacity', 'volume', 'length', 'width',
            'height', 'registration_number',
            'registration_country', 'adr', 'dozvol',
            'tir', 'license_number', 'is_active',
            'is_verified', 'verification_date',
            'verified_by', 'created_at', 'updated_at',
            'documents', 'inspections', 'availability'
        ]
        read_only_fields = [
            'created_at', 'updated_at',
            'is_verified', 'verification_date',
            'verified_by'
        ]

class VehicleListSerializer(serializers.ModelSerializer):
    """Simplified vehicle serializer for list views"""
    owner = UserProfileSerializer(read_only=True)
    documents_count = serializers.IntegerField(
        source='documents.count',
        read_only=True
    )
    documents = VehicleDocumentSerializer(many=True, read_only=True)
    inspections = VehicleInspectionSerializer(many=True, read_only=True)
    availability = VehicleAvailabilitySerializer(many=True, read_only=True)
    verified_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner', 'body_type', 'loading_type',
            'capacity', 'volume', 'length', 'width',
            'height', 'registration_number',
            'registration_country', 'adr', 'dozvol',
            'tir', 'license_number', 'is_active',
            'is_verified', 'verification_date',
            'verified_by', 'created_at', 'updated_at',
            'documents', 'inspections', 'availability',
            'documents_count', 

            # 'id', 'owner', 'body_type','loading_type',
            # 'capacity', 'registration_number',
            # 'volume', 'length', 'width', 'height',
            # 'is_active', 'is_verified','adr', 'dozvol', 'tir', 'license_number',
            # 'documents_count'
        ]

class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for vehicle creation"""
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'body_type', 'loading_type', 'capacity',
            'volume', 'length', 'width', 'height',
            'registration_number', 'registration_country',
            'adr', 'dozvol', 'tir', 'license_number'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Vehicle.objects.create(owner=user, **validated_data)

class VehicleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vehicle"""
    class Meta:
        model = Vehicle
        fields = [
            'body_type', 'loading_type', 'capacity',
            'volume', 'length', 'width', 'height',
            'registration_number', 'registration_country',
            'adr', 'dozvol', 'tir', 'license_number',
            'is_active'
        ]

class VehicleVerificationSerializer(serializers.ModelSerializer):
    """Serializer for vehicle verification"""
    class Meta:
        model = Vehicle
        fields = ['is_verified', 'verification_notes']
    
    def update(self, instance, validated_data):
        if validated_data.get('is_verified'):
            validated_data['verification_date'] = timezone.now()
            validated_data['verified_by'] = self.context['request'].user
        return super().update(instance, validated_data)
```

# vehicles\urls.py

```py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    VehicleViewSet,
    VehicleDocumentViewSet
)

router = DefaultRouter()
router.register(r'', VehicleViewSet, basename='vehicle')

vehicle_router = routers.NestedDefaultRouter(
    router,
    r'',
    lookup='vehicle'
)
vehicle_router.register(
    r'documents',
    VehicleDocumentViewSet,
    basename='vehicle-documents'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(vehicle_router.urls)),
]
```

# vehicles\views.py

```py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import (
    Vehicle,
    VehicleDocument,
    VehicleAvailability,
    VehicleInspection
)
from .serializers import (
    VehicleSerializer,
    VehicleListSerializer,
    VehicleCreateSerializer,
    VehicleUpdateSerializer,
    VehicleVerificationSerializer,
    VehicleDocumentSerializer,
    VehicleAvailabilitySerializer,
    VehicleInspectionSerializer
)
from .filters import VehicleFilter
from core.permissions import (
    IsVerifiedUser,
    IsObjectOwner,
    IsCarrier
)

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsVerifiedUser, IsCarrier]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = VehicleFilter
    search_fields = [
        'registration_number',
        'owner__username'
    ]
    ordering_fields = [
        'created_at',
        'capacity',
        'volume'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # Regular users can only see their own vehicles
            return queryset.filter(owner=self.request.user)
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VehicleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VehicleUpdateSerializer
        elif self.action == 'list':
            return VehicleListSerializer
        elif self.action == 'verify':
            return VehicleVerificationSerializer
        return self.serializer_class
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsVerifiedUser, IsCarrier, IsObjectOwner]
        else:
            permission_classes = [IsVerifiedUser, IsCarrier]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        description='Verify vehicle',
        request=VehicleVerificationSerializer,
        responses={200: VehicleSerializer}
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAdminUser]
    )
    def verify(self, request, pk=None):
        """Verify vehicle (admin only)"""
        vehicle = self.get_object()
        serializer = self.get_serializer(
            vehicle,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save()
        
        return Response(
            VehicleSerializer(vehicle).data
        )
    
    @extend_schema(
        description='Add document to vehicle',
        request=VehicleDocumentSerializer,
        responses={201: VehicleDocumentSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """Add document to vehicle"""
        vehicle = self.get_object()
        serializer = VehicleDocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(vehicle=vehicle)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        description='Get vehicle documents',
        responses={200: VehicleDocumentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents for a vehicle"""
        vehicle = self.get_object()
        documents = VehicleDocument.objects.filter(vehicle=vehicle)
        serializer = VehicleDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Set vehicle availability',
        request=VehicleAvailabilitySerializer,
        responses={201: VehicleAvailabilitySerializer}
    )
    @action(detail=True, methods=['post'])
    def set_availability(self, request, pk=None):
        """Set vehicle availability"""
        vehicle = self.get_object()
        serializer = VehicleAvailabilitySerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(vehicle=vehicle)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        description='Get vehicle availability',
        responses={200: VehicleAvailabilitySerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get vehicle availability periods"""
        vehicle = self.get_object()
        availability = VehicleAvailability.objects.filter(
            vehicle=vehicle,
            end_date__gte=timezone.now().date()
        )
        serializer = VehicleAvailabilitySerializer(
            availability,
            many=True
        )
        return Response(serializer.data)
    
    @extend_schema(
        description='Add inspection record',
        request=VehicleInspectionSerializer,
        responses={201: VehicleInspectionSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_inspection(self, request, pk=None):
        """Add inspection record"""
        vehicle = self.get_object()
        serializer = VehicleInspectionSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(
                vehicle=vehicle,
                inspector=request.user
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        description='Get inspection records',
        responses={200: VehicleInspectionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def inspections(self, request, pk=None):
        """Get vehicle inspection records"""
        vehicle = self.get_object()
        inspections = VehicleInspection.objects.filter(
            vehicle=vehicle
        )
        serializer = VehicleInspectionSerializer(
            inspections,
            many=True
        )
        return Response(serializer.data)

class VehicleDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleDocumentSerializer
    permission_classes = [IsVerifiedUser, IsCarrier]
    
    def get_queryset(self):
        return VehicleDocument.objects.filter(
            vehicle__owner=self.request.user
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        vehicle_id = self.kwargs.get('vehicle_pk')
        vehicle = Vehicle.objects.get(id=vehicle_id)
        if vehicle.owner != self.request.user:
            raise permissions.PermissionDenied(
                'You do not have permission to add documents to this vehicle'
            )
        serializer.save(vehicle=vehicle)
    
    @extend_schema(
        description='Verify document',
        request=None,
        responses={200: VehicleDocumentSerializer}
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAdminUser]
    )
    def verify(self, request, pk=None):
        """Verify document (admin only)"""
        document = self.get_object()
        document.verified = True
        document.verified_at = timezone.now()
        document.verified_by = request.user
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)
```

