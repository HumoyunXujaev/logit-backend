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