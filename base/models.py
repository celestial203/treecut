from django.contrib.auth.models import User  # Import the User model
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
import re
import os
from decimal import Decimal

# models.py
from django.db import models
from django.contrib.auth.models import User

class Lumber(models.Model):
    no = models.CharField(max_length=50)
    trade_name = models.CharField(max_length=200)
    manager_owner = models.CharField(max_length=200)
    permit_no = models.CharField(max_length=100)
    date_issued = models.DateField()
    expiry_date = models.DateField()
    volume_cubic_meter = models.DecimalField(max_digits=10, decimal_places=2)
    species = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

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
    tcp_no = models.CharField(max_length=100, unique=True, verbose_name="TCP No.")
    permittee = models.CharField(max_length=100)
    location = models.CharField(max_length=200, null=True, blank=True)
    tct_oct_no = models.CharField(max_length=100, verbose_name="TCT/OCT No.", null=True, blank=True)
    tax_dec_no = models.CharField(max_length=100, verbose_name="Tax Declaration No.", null=True, blank=True)
    lot_no = models.CharField(max_length=100, verbose_name="Lot No.", null=True, blank=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Area (ha.)", null=True, blank=True)
    no_of_trees = models.IntegerField(verbose_name="Number of Trees", default=0)
    species = models.CharField(max_length=100, null=True, blank=True)
    total_volume_granted = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Volume Granted (cu.m.)")
    gross_volume = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Gross Volume (cu.m.)", null=True, blank=True)
    net_volume = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Net Volume (cu.m.)", null=True, blank=True)
    permit_issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    rep_by = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tcp_no

    class Meta:
        ordering = ['-created_at']

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
    
    # Additional Information
    purpose = models.CharField(max_length=100, choices=PURPOSE_CHOICES)
    date_acquired = models.DateField(null=True, blank=True)
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
    file = models.FileField(upload_to='chainsaw_files/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.serial_number}"

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

class CuttingRecord(models.Model):
    parent_tcp = models.ForeignKey(Cutting, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    species = models.CharField(max_length=100)
    no_of_trees = models.IntegerField()
    volume = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_volume = models.DecimalField(max_digits=10, decimal_places=2)
    _remaining_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        db_column='remaining_balance',
        default=Decimal('0.00')  # Add default value
    )
    remarks = models.TextField(blank=True, null=True)

    @property
    def remaining_balance(self):
        return self._remaining_balance

    @remaining_balance.setter
    def remaining_balance(self, value):
        self._remaining_balance = value

    def save(self, *args, **kwargs):
        if not self.calculated_volume:
            self.calculated_volume = self.volume + (self.volume * Decimal('0.30'))
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_added']