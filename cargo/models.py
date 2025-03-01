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