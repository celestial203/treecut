from django.contrib.auth.models import User  # Import the User model
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
import re
import os
from django.core.validators import MinValueValidator, MaxValueValidator, DecimalValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
# The import statement for VolumeRecord should be placed at the top of the file with other import statements.

class Lumber(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Expired', 'Expired'),
        ('Pending', 'Pending'),
    ]

    # Basic Information
    no = models.IntegerField(null=True, blank=True)
    trade_name = models.CharField(max_length=100)
    manager_owner = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=11, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    
    # Location
    brgy = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    
    # Permit Details
    source_supplier = models.CharField(max_length=100)
    permit_no = models.CharField(max_length=100)
    date_issued = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    # Volume Information
    volume_cubic_meter = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    species = models.CharField(max_length=100)
    
    # File Attachment
    file = models.FileField(upload_to='lumber_files/', null=True, blank=True)
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # Changed from CASCADE to SET_NULL
        null=True,
        blank=True,  # Added blank=True
        related_name='lumber_records'
    )

    class Meta:
        ordering = ['-date_issued']

    def __str__(self):
        return f"{self.trade_name} - {self.permit_no}"

    def clean(self):
        # Validate dates
        if self.date_issued and self.date_issued > timezone.now().date():
            # Only raise error if not a special case
            if not self.is_special_case:  # Define your condition here
                raise ValidationError({'date_issued': 'Date issued cannot be in the future'})
            
        if self.date_issued and self.expiry_date and self.expiry_date < self.date_issued:
            raise ValidationError({'expiry_date': 'Expiry date must be after date issued'})
            
        # Validate contact number
        if self.contact_number:
            if not self.contact_number.startswith('09'):
                raise ValidationError({'contact_number': 'Contact number must start with 09'})
            if len(self.contact_number) != 11:
                raise ValidationError({'contact_number': 'Contact number must be 11 digits'})
            if not self.contact_number.isdigit():
                raise ValidationError({'contact_number': 'Contact number must contain only digits'})
                
        # Validate volume
        if self.volume_cubic_meter and self.volume_cubic_meter <= 0:
            raise ValidationError({'volume_cubic_meter': 'Volume must be greater than 0'})

    def save(self, *args, **kwargs):
        # Auto-generate number if not set
        if not self.no:
            last_record = Lumber.objects.order_by('-no').first()
            self.no = 1 if not last_record else last_record.no + 1
            
        # Update status based on expiry date
        if self.expiry_date:
            today = timezone.now().date()
            if today > self.expiry_date:
                self.status = 'Expired'
            else:
                self.status = 'Active'
                
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def expiry_warning(self):
        """Returns True if the permit is expiring within 3 months"""
        if not self.expiry_date:
            return False
            
        today = timezone.now().date()
        three_months_from_now = today + timedelta(days=90)
        
        return today <= self.expiry_date <= three_months_from_now

    @property
    def location(self):
        """Returns a formatted location string"""
        location_parts = []
        if self.brgy:
            location_parts.append(self.brgy)
        if self.municipality:
            location_parts.append(self.municipality)
        if self.province:
            location_parts.append(self.province)
        
        return ", ".join(location_parts) if location_parts else "No location specified"

    @property
    def is_complete(self):
        """Check if all required information is present"""
        required_fields = [
            self.no, self.trade_name, self.manager_owner, 
            self.permit_no, self.date_issued, self.volume_cubic_meter, 
            self.species
        ]
        return all(required_fields)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

def permit_file_path(instance, filename):
    return f'permit_files/{timezone.now().year}/{timezone.now().month}/{filename}'

def calculate_expiry_date(date_issued):
    """Calculate expiry date as 50 business days from date issued"""
    if not date_issued:
        return None
        
    current_date = date_issued
    business_days = 0
    
    while business_days < 50:
        current_date += timedelta(days=1)
        # Skip weekends (5 = Saturday, 6 = Sunday)
        if current_date.weekday() not in [5, 6]:
            business_days += 1
    
    return current_date

class Cutting(models.Model):
    PERMIT_CHOICES = [
        ('TCP', 'TCP'),
        ('STCP', 'STCP'),
        ('PLTP', 'PLTP'),
        ('SPLTP', 'SPLTP'),
    ]
    
    SITUATION_CHOICES = [
        ('Good', 'Good'),
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Expired', 'Expired'),
    ]
    
    permit_type = models.CharField(max_length=5, choices=PERMIT_CHOICES, default='TCP')
    permit_number = models.CharField(max_length=20, help_text='Permit identification number')
    permittee = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True, null=True)
    
    # Making new fields nullable
    tct_oct_no = models.CharField(max_length=100, verbose_name="TCT/OCT No.", null=True, blank=True)
    tax_dec_no = models.CharField(max_length=100, verbose_name="Tax Declaration No.", null=True, blank=True)
    lot_no = models.CharField(max_length=100, verbose_name="Lot No.", null=True, blank=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Area (ha.)", null=True, blank=True)
    no_of_trees = models.IntegerField(verbose_name="Number of Trees", null=True, blank=True)
    species = models.TextField(help_text="For PLTP, separate multiple species with commas")
    permit_file = models.FileField(
        upload_to='permits/',
        null=True,
        blank=True,
        help_text="Upload permit document"
    )
    
    total_volume_granted = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Volume Granted (cu.m.)")
    gross_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    net_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False  # Make this field non-editable since it's calculated
    )
    
    date_issued = models.DateField(default=timezone.now)
    expiry_date = models.DateField(editable=False)
    rep_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Representative")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    situation = models.CharField(
        max_length=50, 
        choices=SITUATION_CHOICES,
        default='Pending',
        verbose_name='Situation'
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MaxValueValidator(999.999999),
        ],
        null=True,
        blank=True,
        help_text="Latitude coordinates (e.g. 10.123456)"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MaxValueValidator(999.999999),
        ],
        null=True,
        blank=True,
        help_text="Longitude coordinates (e.g. 123.456789)"
    )

    class Meta:
        ordering = ['-date_issued']
        unique_together = ['permit_type', 'permit_number']

    def __str__(self):
        return f"{self.permit_type}-{self.permit_number}"

    def save(self, *args, **kwargs):
        if self.date_issued:
            # Always calculate expiry date as 50 business days
            self.expiry_date = calculate_expiry_date(self.date_issued)
            
        # Calculate net volume if gross volume exists
        if self.gross_volume:
            self.net_volume = round(float(self.gross_volume) * 0.70, 2)
        
        # Handle status based on permit type
        today = timezone.now().date()
        
        if self.permit_type == 'STCP':
            # For STCP: Status depends on volume records
            if not self.pk:  # New record
                self.situation = 'Pending'
            else:
                has_records = CuttingRecord.objects.filter(parent_tcp=self).exists()
                self.situation = 'Good' if has_records else 'Pending'
        else:
            # For TCP, PLTP, SPLTP: Status depends on dates
            if self.expiry_date:
                if today > self.expiry_date:
                    self.situation = 'Expired'
                else:
                    self.situation = 'Active'
        
        super().save(*args, **kwargs)

    def update_situation(self):
        """Update the situation status based on permit type and conditions"""
        today = timezone.now().date()
        
        if self.permit_type == 'STCP':
            # Only update STCP permits based on volume records
            has_records = CuttingRecord.objects.filter(parent_tcp=self).exists()
            new_situation = 'Good' if has_records else 'Pending'
            
            if self.situation != new_situation:
                self.situation = new_situation
                self.save(update_fields=['situation'])
        else:
            # For other permit types, update based on expiry date
            if self.expiry_date:
                new_situation = 'Expired' if today > self.expiry_date else 'Active'
                
                if self.situation != new_situation:
                    self.situation = new_situation
                    self.save(update_fields=['situation'])

def chainsaw_file_path(instance, filename):
    # Generate file path: chainsaw_files/YYYY/MM/filename
    return f'chainsaw_files/{timezone.now().year}/{timezone.now().month}/{filename}'

class Chainsaw(models.Model):
    
    PURPOSE_CHOICES = [
        ('CUTTING IN PRIVATE PLANTATION FOR COMMERCIAL USE', 'CUTTING IN PRIVATE PLANTATION FOR COMMERCIAL USE'),
        ('CUTTING IN TENURE AREA FOR PERSONAL/NON COMMERCIAL USE', 'CUTTING IN TENURE AREA FOR PERSONAL/NON COMMERCIAL USE'),
    ]

    REGISTRATION_STATUS_CHOICES = [
        ('NEW', 'NEW'),
        ('RENEWED', 'RENEWED'),
        ('RENEWAL', 'RENEWAL'),
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

    def save(self, *args, **kwargs):
        # Calculate expiry date (2 years from date issued, excluding weekends)
        if self.date_issued:
            # Start with the initial date
            current_date = self.date_issued
            days_to_add = 2 * 365  # 2 years worth of days
            days_added = 0
            
            while days_added < days_to_add:
                current_date += timedelta(days=1)
                # Skip weekends (5 = Saturday, 6 = Sunday)
                if current_date.weekday() not in [5, 6]:
                    days_added += 1
            
            self.expiry_date = current_date
            
            # Update registration status based on expiry date
            today = timezone.now().date()
            if today > self.expiry_date:
                self.registration_status = 'EXPIRED'
            elif (self.expiry_date - today).days <= 90:  # If within 90 days (3 months) of expiry
                self.registration_status = 'FOR RENEWAL'
            
        super().save(*args, **kwargs)

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
        
    @property
    def expiry_status(self):
        """Returns the expiry status for display purposes"""
        if self.is_expired:
            return 'EXPIRED'
        elif self.is_expiring_soon:
            return f'Expires in {self.days_remaining} days'
        else:
            return 'Active'

class Wood(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE_NEW', 'Active (New)'),
        ('ACTIVE_RENEWED', 'Active (Renewed)'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('Resawmill-new', 'Resawmill-new'),
        ('Resawmill-renew', 'Resawmill-renew'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, default='', help_text="Name of the wood processing plant")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    wpp_number = models.CharField(max_length=100, default='', help_text="WPP registration number")
    integrated = models.CharField(max_length=100, blank=True, null=True)
    business = models.CharField(max_length=200, default='', help_text="Business name")
    plant = models.CharField(max_length=200, default='', help_text="Plant location/address")
    
    # Technical Details
    drc = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="DRC in cubic meters",
        default=Decimal('0.00')
    )
    alr = models.CharField(  # Changed from DecimalField to CharField
        max_length=20,
        null=True,
        blank=True,
        help_text="Annual Log Requirement (ALR)"
    )
    
    # Location Information
    latitude = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Enter latitude (e.g., 9.990572)"
    )
    longitude = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Enter longitude (e.g., 123.305953)"
    )
    supplier_info = models.CharField(
        max_length=500, 
        help_text="Location/Address of supplier",
        null=True,
        blank=True
    )
    
    # Volume Contracted
    local_volume = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.000'))],
        help_text="Local volume in cubic meters",
        default=Decimal('0.000')
    )
    imported_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    area = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Dates
    date_issued = models.DateField()
    date_released = models.DateField(default=timezone.now)
    expiry_date = models.DateField(default=timezone.now)
    
    # Approval and Status
    approved_by = models.CharField(max_length=200, null=True, blank=True, default='')
    wood_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE_NEW'
    )
    
    # File Attachment
    attachment = models.FileField(
        upload_to='wood_files/',
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.date_issued and self.expiry_date:
            # Convert datetime to date if needed
            if isinstance(self.date_issued, datetime):
                self.date_issued = self.date_issued.date()
            if isinstance(self.expiry_date, datetime):
                self.expiry_date = self.expiry_date.date()
            
            # Now compare dates
            if self.expiry_date <= self.date_issued:
                raise ValidationError('Expiry date must be after date issued.')

    def save(self, *args, **kwargs):
        # Calculate expiry date if not set (5 years from date issued)
        if self.date_issued and not self.expiry_date:
            if isinstance(self.date_issued, datetime):
                self.date_issued = self.date_issued.date()
            self.expiry_date = self.date_issued + timedelta(days=5*365)
        
        # Calculate ALR if not set
        if self.drc and (self.alr is None or self.alr == 0):
            self.alr = self.drc * 290 * Decimal('0.80')
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.wpp_number}"

    class Meta:
        ordering = ['-date_issued']
        verbose_name = "Wood Processing Plant"
        verbose_name_plural = "Wood Processing Plants"

class CuttingRecord(models.Model):
    SPECIES_CHOICES = [
        ('Molave', 'Molave'),
        ('Sawn Lumber', 'Sawn Lumber'),
        ('Fuel Wood', 'Fuel Wood'),
        ('Yemane', 'Yemane'),
        ('Mahogany', 'Mahogany'),
        ('Narra', 'Narra'),
        ('Minepoles', 'Minepoles'),
        ('Teabolts', 'Teabolts'),
    ]
    
    VOLUME_TYPE_CHOICES = [
        ('Initial', 'Initial'),
        ('Additional', 'Additional'),
    ]
    
    parent_tcp = models.ForeignKey(
        Cutting, 
        on_delete=models.CASCADE, 
        related_name='cutting_records'
    )
    date = models.DateField(default=timezone.now)
    volume_type = models.CharField(
        max_length=20,
        choices=VOLUME_TYPE_CHOICES,
        default='Initial'
    )
    species = models.CharField(max_length=100, choices=SPECIES_CHOICES, default='Molave')
    volume = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_volume = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True
    )
    remaining_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal('0.00')
    )
    number_of_trees = models.IntegerField()
    remarks = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.parent_tcp.permit_number} - {self.species} - {self.volume}cu.m"

    def clean(self):
        if self.volume is None:
            raise ValidationError({'volume': 'Volume is required.'})
        if self.number_of_trees is None:
            raise ValidationError({'number_of_trees': 'Number of trees is required.'})
        
        try:
            volume = Decimal(str(self.volume))
            if volume <= 0:
                raise ValidationError({'volume': 'Volume must be greater than 0.'})
        except (TypeError, ValueError, InvalidOperation):
            raise ValidationError({'volume': 'Invalid volume value.'})
        
        try:
            trees = int(self.number_of_trees)
            if trees <= 0:
                raise ValidationError({'number_of_trees': 'Number of trees must be greater than 0.'})
        except (TypeError, ValueError):
            raise ValidationError({'number_of_trees': 'Invalid number of trees.'})

    def save(self, *args, **kwargs):
        if not self.pk:  # If this is a new record
            latest_record = CuttingRecord.objects.filter(
                parent_tcp=self.parent_tcp
            ).order_by('-date_added').first()

            # Ensure volume is Decimal
            self.volume = Decimal(str(self.volume)).quantize(Decimal('0.01'))
            
            # Calculate the calculated_volume (40% addition for Sawn Lumber)
            if self.species == 'Sawn Lumber':
                self.calculated_volume = (self.volume * Decimal('1.40')).quantize(Decimal('0.01'))
            else:
                self.calculated_volume = self.volume
            
            if latest_record:
                # For subsequent entries
                latest_balance = Decimal(str(latest_record.remaining_balance))
                # Subtract the calculated volume
                self.remaining_balance = (latest_balance - self.calculated_volume).quantize(Decimal('0.01'))
            else:
                # For first entry, use gross_volume instead of total_volume_granted
                gross_volume = Decimal(str(self.parent_tcp.gross_volume))
                self.remaining_balance = (gross_volume - self.calculated_volume).quantize(Decimal('0.01'))

        self.full_clean()
        super().save(*args, **kwargs)

class CuttingPermit(models.Model):
    # ... existing fields ...
    
    # Add these new fields
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinates (e.g. 10.123456)"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinates (e.g. 123.456789)"
    )

    # ... rest of the model ...

class VolumeRecord(models.Model):
    cutting = models.ForeignKey('Cutting', on_delete=models.CASCADE, related_name='volume_records')
    date = models.DateField(default=timezone.now)
    species = models.CharField(max_length=100)
    number_of_trees = models.IntegerField()
    volume = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='volume_records/', null=True, blank=True)

    class Meta:
        db_table = 'base_volumerecord'
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.cutting} - {self.volume} cu.m ({self.date})"

class WoodProcessingPlant(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    owner = models.CharField(max_length=255)
    permit_number = models.CharField(max_length=100)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE_NEW', 'Active (New)'),
        ('ACTIVE_RENEWED', 'Active (Renewed)'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled')
    ], default='ACTIVE_NEW')
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-update status based on expiry date
        today = datetime.now().date()
        thirty_days_from_now = today + timedelta(days=30)
        
        if self.expiry_date < today:
            self.status = 'EXPIRED'
        elif self.expiry_date <= thirty_days_from_now:
            self.status = 'EXPIRED'
        else:
            self.status = 'ACTIVE_NEW'
            
        super().save(*args, **kwargs)