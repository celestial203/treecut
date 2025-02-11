from django.contrib.auth.models import User  # Import the User model
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
import re
import os

# models.py
from django.db import models
from django.contrib.auth.models import User

class Lumber(models.Model):
    no = models.CharField(max_length=50, unique=True)
    trade_name = models.CharField(max_length=200, verbose_name="Trade Name", null=True, blank=True)
    manager_owner = models.CharField(max_length=200, verbose_name="Manager/Owner", null=True, blank=True)
    contact_no = models.CharField(max_length=50, verbose_name="Contact No.", null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], verbose_name="Gender", null=True, blank=True)
    
    # Location fields
    brgy = models.CharField(max_length=100, verbose_name="Barangay", null=True, blank=True)
    municipality = models.CharField(max_length=100, verbose_name="Municipality", null=True, blank=True)
    province = models.CharField(max_length=100, verbose_name="Province", null=True, blank=True)
    
    # Permit details
    permit_no = models.CharField(max_length=50, verbose_name="Permit No.", null=True, blank=True)
    date_issued = models.DateField(verbose_name="Date Issued", null=True, blank=True)
    expiry_date = models.DateField(verbose_name="Expiry Date", null=True, blank=True)
    
    # Additional details
    source_supplier = models.CharField(max_length=200, verbose_name="Source/Supplier", null=True, blank=True)
    volume_cubic_meter = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Volume (cubic meter)", null=True, blank=True)
    species = models.CharField(max_length=100, verbose_name="Species", null=True, blank=True)
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lumber"
        verbose_name_plural = "Lumber Records"
        constraints = [
            models.UniqueConstraint(fields=['trade_name', 'permit_no'], name='unique_trade_permit')
        ]

    def __str__(self):
        return f"{self.trade_name} - {self.permit_no}"

    def clean(self):
        # Date validations
        if self.date_issued:
            # Check if expiry date is not more than 5 years from date issued
            max_expiry = self.date_issued + timezone.timedelta(days=5*365)
            if self.expiry_date > max_expiry:
                raise ValidationError({'expiry_date': 'Expiry date cannot be more than 5 years from date issued.'})

        if not self.date_issued:
            raise ValidationError({'date_issued': 'Date issued is required.'})

        if not self.expiry_date:
            raise ValidationError({'expiry_date': 'Expiry date is required.'})

        # Contact number validation
        if self.contact_no:
            phone_pattern = re.compile(r'^\+?[0-9]{10,15}$')
            if not phone_pattern.match(self.contact_no):
                raise ValidationError({'contact_no': 'Invalid contact number format. Please enter a valid phone number.'})

        # Volume validation
        if self.volume_cubic_meter is not None:
            if self.volume_cubic_meter <= 0:
                raise ValidationError({'volume_cubic_meter': 'Volume must be greater than 0.'})

        # Permit number validation
        if self.permit_no:
            permit_pattern = re.compile(r'^[A-Za-z0-9-]+$')
            if not permit_pattern.match(self.permit_no):
                raise ValidationError({'permit_no': 'Permit number can only contain letters, numbers, and hyphens.'})

        # Trade name validation
        if self.trade_name:
            if len(self.trade_name.strip()) < 3:
                raise ValidationError({'trade_name': 'Trade name must be at least 3 characters long.'})

        # No. validation (assuming it's a required field)
        if not self.no:
            raise ValidationError({'no': 'Number is required.'})
        no_pattern = re.compile(r'^[A-Za-z0-9-]+$')
        if not no_pattern.match(self.no):
            raise ValidationError({'no': 'Number can only contain letters, numbers, and hyphens.'})

        # Location validations
        if any([self.brgy, self.municipality, self.province]) and not all([self.brgy, self.municipality, self.province]):
            raise ValidationError('All location fields (Barangay, Municipality, and Province) must be filled if any one is provided.')

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Convert fields to uppercase before saving
        if self.trade_name:
            self.trade_name = self.trade_name.upper()
        if self.permit_no:
            self.permit_no = self.permit_no.upper()
        if self.no:
            self.no = self.no.upper()
        
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        if self.date_issued:
            expiry_date = self.date_issued + timedelta(days=90)  # 3 months
            remaining = (expiry_date - timezone.now().date()).days
            return max(remaining, 0)  # Don't show negative days
        return 0

    @property
    def is_expiring_soon(self):
        remaining = self.days_remaining
        return 0 < remaining <= 15  # Warning when 15 days or less remaining

    @property
    def is_expired(self):
        return self.days_remaining <= 0

    @property
    def status(self):
        if self.is_expired:
            return 'Expired'
        elif self.is_expiring_soon:
            return 'Expiring Soon'
        return 'Active'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class Cutting(models.Model):
    tcp_no = models.CharField(max_length=50, unique=True, verbose_name="TCP Number")
    permittee = models.CharField(max_length=200, verbose_name="Permittee")
    rep_by = models.CharField(max_length=200, verbose_name="Representative")
    location = models.CharField(max_length=200, verbose_name="Location")
    permit_issue_date = models.DateField(verbose_name="Permit Issue Date")
    
    # Property Details
    tct_oct_no = models.CharField(max_length=100, verbose_name="TCT/OCT Number", null=True, blank=True)
    tax_dec_no = models.CharField(max_length=100, verbose_name="Tax Declaration Number", null=True, blank=True)
    lot_no = models.CharField(max_length=100, verbose_name="Lot Number", null=True, blank=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Area (ha.)", null=True, blank=True)
    
    # Tree Details
    species_name = models.CharField(max_length=200, verbose_name="Species Name")
    no_of_trees = models.IntegerField(verbose_name="Number of Trees")
    gross_volume = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Gross Volume (cu.m.)")
    total_volume_granted = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Volume Granted (cu.m.)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Add a database field for days_remaining
    _days_remaining = models.IntegerField(default=0, db_column='days_remaining')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tree Cutting Permit"
        verbose_name_plural = "Tree Cutting Permits"

    def __str__(self):
        return f"TCP-{self.tcp_no} - {self.permittee}"

    def clean(self):
        super().clean()
        errors = {}

        # TCP number validation
        if self.tcp_no:
            tcp_pattern = re.compile(r'^[A-Za-z0-9-]+$')
            if not tcp_pattern.match(self.tcp_no):
                errors['tcp_no'] = 'TCP number can only contain letters, numbers, and hyphens.'

        # Required fields validation
        if not self.permittee:
            errors['permittee'] = 'Permittee is required.'
        if not self.location:
            errors['location'] = 'Location is required.'
        if not self.permit_issue_date:
            errors['permit_issue_date'] = 'Permit issue date is required.'
        if not self.species_name:
            errors['species_name'] = 'Species name is required.'

        # Number validation
        if self.no_of_trees is None:
            errors['no_of_trees'] = 'Number of trees is required.'
        elif self.no_of_trees <= 0:
            errors['no_of_trees'] = 'Number of trees must be greater than 0.'

        # Volume validations
        try:
            if self.gross_volume is None:
                errors['gross_volume'] = 'Gross volume is required.'
            elif self.gross_volume <= 0:
                errors['gross_volume'] = 'Gross volume must be greater than 0.'

            if self.total_volume_granted is None:
                errors['total_volume_granted'] = 'Total volume granted is required.'
            elif self.total_volume_granted <= 0:
                errors['total_volume_granted'] = 'Total volume granted must be greater than 0.'
            elif self.total_volume_granted > self.gross_volume:
                errors['total_volume_granted'] = 'Total volume granted cannot exceed gross volume.'
        except TypeError:
            # Handle case where values are not numeric
            if 'gross_volume' not in errors:
                errors['gross_volume'] = 'Gross volume must be a number.'
            if 'total_volume_granted' not in errors:
                errors['total_volume_granted'] = 'Total volume granted must be a number.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Convert fields to uppercase before saving
        if self.tcp_no:
            self.tcp_no = self.tcp_no.upper()
        if self.permittee:
            self.permittee = self.permittee.upper()
        if self.species_name:
            self.species_name = self.species_name.upper()
        
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        """Calculate days remaining until permit expires"""
        if self.permit_issue_date:
            expiry_date = self.permit_issue_date + timedelta(days=50)  # 50 days validity
            remaining = (expiry_date - timezone.now().date()).days
            return max(remaining, 0)  # Don't show negative days
        return 0

    def update_days_remaining(self):
        """Update the stored days_remaining value"""
        self._days_remaining = self.days_remaining
        self.save(update_fields=['_days_remaining'])

    @property
    def is_expiring_soon(self):
        remaining = self.days_remaining
        return 0 < remaining <= 10

    @property
    def is_expired(self):
        return self.days_remaining <= 0

    @property
    def status(self):
        if self.is_expired:
            return 'Expired'
        elif self.is_expiring_soon:
            return 'Expiring Soon'
        return 'Active'

def chainsaw_file_path(instance, filename):
    # Generate file path: chainsaw_files/YYYY/MM/filename
    return f'chainsaw_files/{timezone.now().year}/{timezone.now().month}/{filename}'

class Chainsaw(models.Model):
    PURPOSE_CHOICES = [
        ('CUTTING IN PRIVATE PLANTATION FOR COMMERCIAL USE', 'CUTTING IN PRIVATE PLANTATION FOR COMMERCIAL USE'),
        ('CUTTING IN TENURE AREA FOR PERSONAL/NON COMMERCIAL USE', 'CUTTING IN TENURE AREA FOR PERSONAL/NON COMMERCIAL USE'),
    ]

    REGISTRATION_STATUS_CHOICES = [
        ('RENEWED', 'RENEWED'),
        ('FOR RENEWAL', 'FOR RENEWAL'),
        ('EXPIRED', 'EXPIRED'),
    ]

    # Basic Information
    no = models.CharField(max_length=50)
    year = models.IntegerField()
    region = models.CharField(max_length=50)
    
    # Location Details
    penro = models.CharField(max_length=100)
    cenro = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    
    # Owner Details
    name = models.CharField(max_length=200)
    municipality = models.CharField(max_length=100)
    
    # Chainsaw Details
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    
    # Additional Chainsaw Information
    purpose = models.CharField(max_length=100, choices=PURPOSE_CHOICES)
    date_acquired = models.DateField()
    cert_reg_number = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    registration_status = models.CharField(max_length=50, choices=REGISTRATION_STATUS_CHOICES)
    date_renewal = models.DateField(null=True, blank=True)
    horse_power = models.CharField(max_length=50)
    guidebar_length = models.CharField(max_length=50)
    denr_sticker = models.CharField(max_length=100)
    
    # Permit Details
    ctpo_number = models.CharField(max_length=100)
    date_issued = models.DateField()
    expiry_date = models.DateField()
    
    # File Upload
    file = models.FileField(upload_to=chainsaw_file_path, null=True, blank=True, verbose_name='Upload File')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def days_remaining(self):
        if self.expiry_date:
            today = timezone.now().date()
            delta = self.expiry_date - today
            return max(0, delta.days)
        return 0

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def is_expiring_soon(self):
        if self.expiry_date:
            days = self.days_remaining
            return 0 < days <= 30
        return False

    def __str__(self):
        return f"{self.name} - {self.serial_number}"

class Wood(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    type = models.CharField(max_length=200, null=True, blank=True)
    integrated = models.CharField(
        max_length=20,
        choices=[
            ('APPLICABLE', 'Applicable'),
            ('NOT_APPLICABLE', 'Not Applicable'),
        ],
        default='NOT_APPLICABLE',
        null=True,
        blank=True
    )
    wpp_number = models.CharField(max_length=100, null=True, blank=True)
    business = models.CharField(max_length=200, null=True, blank=True)
    plant = models.CharField(max_length=200, null=True, blank=True)
    drc = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    alr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    longitude = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.CharField(max_length=50, null=True, blank=True)
    local_volume = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    imported_volume = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    supplier_info = models.CharField(max_length=500, null=True, blank=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date_issued = models.DateField(null=True, blank=True)
    date_released = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    approved_by = models.CharField(max_length=200, null=True, blank=True)
    wood_status = models.CharField(  # Changed from 'status' to 'wood_status'
        max_length=20,
        choices=[
            ('ACTIVE_NEW', 'Active/New'),
            ('ACTIVE_RENEWAL', 'Active/Renewed'),
            ('EXISTING', 'Existing'),
            ('EXPIRED', 'Expired'),
            ('CANCELLED', 'Cancelled')
        ],
        default='ACTIVE_NEW',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.wpp_number}"

    def save(self, *args, **kwargs):
        if not self.pk:  # If this is a new record
            self.wood_status = 'ACTIVE_NEW'
        elif self.expiry_date and self.expiry_date < timezone.now().date():
            self.wood_status = 'EXPIRED'
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        if self.expiry_date:
            remaining = (self.expiry_date - timezone.now().date()).days
            return max(remaining, 0)
        return 0

    @property
    def is_expiring_soon(self):
        remaining = self.days_remaining
        return 0 < remaining <= 30

    @property
    def is_expired(self):
        return self.days_remaining <= 0

    @property
    def status(self):
        if self.is_expired:
            return 'Expired'
        elif self.is_expiring_soon:
            return 'Expiring Soon'
        return 'Active'