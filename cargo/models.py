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

class Cargo(models.Model):
    class CargoStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending Assignment')
        ASSIGNED = 'assigned', _('Assigned to Carrier')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
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
        related_name='owned_cargos'
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
    source_type = models.CharField(max_length=50, null=True, blank=True)
    source_id = models.CharField(max_length=100, null=True, blank=True)
    
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
    
    def save(self, *args, **kwargs):
        """Calculate volume if dimensions are provided"""
        if all([self.length, self.width, self.height]):
            self.volume = self.length * self.width * self.height
        super().save(*args, **kwargs)

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