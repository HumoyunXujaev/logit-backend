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