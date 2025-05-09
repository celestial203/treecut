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
from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
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
    PERMIT_TYPE_CHOICES = [
        ('TCP', 'TCP'),
        ('PLTP', 'PLTP'),
        ('STCP', 'STCP'),
        ('SPLTP', 'SPLTP'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CONSUMED', 'Consumed'),
        ('PENDING', 'Pending'),
        ('Active', 'Active'),
        ('Expired', 'Expired'),
        ('Pending', 'Pending'),
    ]

    permit_type = models.CharField(
        max_length=100,
        choices=PERMIT_TYPE_CHOICES,
        default='TCP'
    )
    permit_number = models.CharField(max_length=100)
    date_issued = models.DateField()
    expiry_date = models.DateField()
    permittee = models.CharField(max_length=200)
    rep_by = models.CharField(max_length=200, blank=True, null=True)
    location = models.TextField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    tct_oct_no = models.CharField(max_length=100, blank=True, null=True)
    tax_dec_no = models.CharField(max_length=100, blank=True, null=True)
    lot_no = models.CharField(max_length=100, blank=True, null=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    species = models.TextField(blank=True, null=True)
    no_of_trees = models.IntegerField(default=0)
    total_volume_granted = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gross_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    permit_file = models.FileField(upload_to='permits/', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    situation = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    other_species = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='cutting_files/', blank=True, null=True)
    contact_number = models.CharField(max_length=11, null=True, blank=True)
    or_number = models.CharField(max_length=100, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.permit_type} - {self.permit_number}"

    def save(self, *args, **kwargs):
        # Auto-calculate expiry date if date_issued is provided and expiry_date is not
        if self.date_issued and not self.expiry_date:
            self.expiry_date = calculate_expiry_date(self.date_issued)
        
        # Auto-determine status based on expiry date
        today = timezone.now().date()
        if self.expiry_date:
            if today > self.expiry_date:
                self.status = 'Expired'
            else:
                if self.permit_type == 'STCP':
                    # For STCP, use the situation field to determine status
                    if self.situation == 'Pending':
                        self.status = 'Pending'
                    else:
                        self.status = 'Active'
                else:
                    # For other permit types, use expiry date
                    self.status = 'Active'
        
        # Calculate volumes if total_volume_granted is provided
        if self.total_volume_granted and (not self.gross_volume or not self.net_volume):
            self.gross_volume = self.total_volume_granted * Decimal('1.3')
            self.net_volume = self.total_volume_granted * Decimal('1.7')
        
        super().save(*args, **kwargs)

    def is_consumed(self):
        return self.gross_volume >= self.total_volume_granted

@receiver(pre_save, sender=Cutting)
def update_cutting_status(sender, instance, **kwargs):
    print(f"Pre-save signal triggered for cutting: {instance.id}")
    
    # Check if this is an existing record
    if instance.id:
        # Check if the permit is consumed (remaining balance <= 0)
        latest_volume_record = VolumeRecord.objects.filter(
            cutting=instance
        ).order_by('-date_added').first()
        
        if latest_volume_record and latest_volume_record.remaining_balance <= 0:
            print("Permit is consumed")
            # You might want to update the status or set a flag here
            instance.is_consumed = True

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
        if self.date_issued and self.expiry_date:
            # Validate that expiry date is not on a weekend
            if self.expiry_date.weekday() in [5, 6]:  # 5 = Saturday, 6 = Sunday
                raise ValidationError('Expiry date cannot be on a weekend')
            
            # Update registration status based on expiry date
            today = timezone.now().date()
            if today > self.expiry_date:
                self.registration_status = 'EXPIRED'
            elif (self.expiry_date - today).days <= 90:  # If within 90 days of expiry
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
    WOOD_STATUS_CHOICES = [
        ('ACTIVE_NEW', 'Active (New)'),
        ('ACTIVE_RENEWED', 'Active (Renewed)'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled')
    ]

    TYPE_CHOICES = [
        ('Resawmill-new', 'RESAWMILL-NEW'),
        ('Resawmill-renew', 'RESAWMILL-RENEWAL')
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    wpp_number = models.CharField(max_length=100)
    business_name = models.CharField(max_length=255, null=True, blank=True, default='Default Business Name')
    address = models.CharField(max_length=255, null=True, blank=True, default='')
    drc = models.DecimalField(max_digits=10, decimal_places=2)
    alr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    supplier_info = models.TextField(null=True, blank=True)
    local_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    imported_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    approved_by = models.CharField(max_length=255, default='CENRO')
    date_issued = models.DateField()
    date_released = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    wood_status = models.CharField(max_length=20, choices=WOOD_STATUS_CHOICES, default='ACTIVE_NEW')
    attachment = models.FileField(upload_to='wood_attachments/', null=True, blank=True)

    class Meta:
        db_table = 'base_wood'

    def __str__(self):
        return f"{self.name} - {self.wpp_number}"

    def save(self, *args, **kwargs):
        # Update status based on expiry date
        if self.expiry_date:
            today = timezone.now().date()
            if today > self.expiry_date:
                self.wood_status = 'EXPIRED'
        super().save(*args, **kwargs)

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
        ('Others', 'Others'),  # Add Others option
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
    other_species = models.CharField(max_length=100, blank=True, null=True)  # New field for custom species
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
        species_name = self.other_species if self.species == 'Others' else self.species
        return f"{self.parent_tcp.permit_number} - {species_name} - {self.volume}cu.m"

    def clean(self):
        super().clean()
        if self.species == 'Others' and not self.other_species:
            raise ValidationError({'other_species': 'Please specify the species name when selecting Others'})
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
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # ... rest of the model ...

class VolumeRecord(models.Model):
    SPECIES_CHOICES = [
        ('Sawn Lumber', 'Sawn Lumber'),
        ('Fuel Wood', 'Fuel Wood'),
        ('Minepoles', 'Minepoles'),
        ('Molave', 'Molave'),
        ('Yemane', 'Yemane'),
        ('Mahogany', 'Mahogany'),
        ('Narra', 'Narra'),
        ('Logbolts', 'Logbolts'),
        ('Others', 'Others'),
    ]
    
    cutting = models.ForeignKey('Cutting', on_delete=models.CASCADE, related_name='volume_records')
    date = models.DateField(default=timezone.now)
    species = models.CharField(max_length=100, choices=SPECIES_CHOICES)
    other_species = models.CharField(max_length=100, blank=True, null=True)
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
        species_display = self.other_species if self.species == 'Others' else self.species
        return f"{self.cutting} - {species_display} - {self.volume} cu.m ({self.date})"

    def clean(self):
        if self.species == 'Others' and not self.other_species:
            raise ValidationError({'other_species': 'Please specify the species name when selecting Others'})

    def save(self, *args, **kwargs):
        # Convert any float values to Decimal before operations
        if isinstance(self.volume, float):
            self.volume = Decimal(str(self.volume))
        
        # Calculate the volume if needed
        if self.calculated_volume is None:
            self.calculated_volume = self.volume

        # Make sure the cutting instance is saved first
        if self.cutting and not self.cutting.pk:
            self.cutting.save()

        # Get the latest record for this cutting
        latest_record = VolumeRecord.objects.filter(
            cutting=self.cutting,
            date_added__lt=timezone.now()
        ).order_by('-date_added').first()

        if latest_record:
            # Ensure values are Decimal
            latest_balance = Decimal(str(latest_record.remaining_balance))
            current_volume = Decimal(str(self.calculated_volume))
            self.remaining_balance = latest_balance - current_volume
        else:
            # For first entry
            if hasattr(self.cutting, 'gross_volume'):
                gross_volume = Decimal(str(self.cutting.gross_volume))
                current_volume = Decimal(str(self.calculated_volume))
                self.remaining_balance = gross_volume - current_volume

        super().save(*args, **kwargs)

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

class TreeSpecies(models.Model):
    cutting = models.ForeignKey(Cutting, on_delete=models.CASCADE, related_name='tree_species')
    species = models.CharField(max_length=100)
    quantity = models.IntegerField()
    volume = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,  # Allow null values initially
        blank=True,  # Allow blank in forms
        default=0.00  # Default value for existing records
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Tree Species"
        ordering = ['species']

    def __str__(self):
        return f"{self.species} ({self.quantity} trees, {self.volume} cu.m)"