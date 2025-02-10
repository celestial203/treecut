# forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from .models import Lumber, Cutting, Chainsaw, Wood
import re
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta


# Get the user model
User = get_user_model()
##LOGIN FORM#####
class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)

            if not user:
                if not User.objects.filter(username=username).exists():
                    raise forms.ValidationError("User does not exist.")
                else:
                    raise forms.ValidationError("Incorrect password.")

        return cleaned_data

    def get_user(self):
        return User.objects.get(username=self.cleaned_data.get("username"))

# LumberForm
class LumberForm(forms.ModelForm):
    class Meta:
        model = Lumber
        fields = [
            'no', 'trade_name', 'manager_owner', 'contact_no', 'gender',
            'brgy', 'municipality', 'province',
            'permit_no', 'date_issued', 'expiry_date',
            'source_supplier', 'volume_cubic_meter', 'species', 'remarks'
        ]
        widgets = {
            'no': forms.TextInput(attrs={'placeholder': 'Enter number'}),
            'trade_name': forms.TextInput(attrs={'placeholder': 'Enter trade name'}),
            'manager_owner': forms.TextInput(attrs={'placeholder': 'Enter manager/owner name'}),
            'contact_no': forms.TextInput(attrs={'placeholder': 'Enter contact number'}),
            'gender': forms.Select(choices=[
                ('', 'Select gender'),
                ('M', 'Male'),
                ('F', 'Female')
            ]),
            'brgy': forms.TextInput(attrs={'placeholder': 'Barangay'}),
            'municipality': forms.TextInput(attrs={'placeholder': 'Municipality'}),
            'province': forms.TextInput(attrs={'placeholder': 'Province'}),
            'permit_no': forms.TextInput(attrs={'placeholder': 'Enter permit number'}),
            'date_issued': forms.DateInput(attrs={
                'type': 'date',
                'class': 'datepicker'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'datepicker'
            }),
            'source_supplier': forms.TextInput(attrs={'placeholder': 'Enter source/supplier'}),
            'volume_cubic_meter': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter volume'
            }),
            'species': forms.TextInput(attrs={'placeholder': 'Enter species'}),
            'remarks': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter any additional remarks'
            })
        }

    def clean_volume_cubic_meter(self):
        volume = self.cleaned_data.get('volume_cubic_meter')
        if volume is not None and volume < 0:
            raise forms.ValidationError("Volume cannot be negative")
        return volume

# CuttingForm
class CuttingForm(forms.ModelForm):
    class Meta:
        model = Cutting
        fields = [
            'tcp_no', 'permittee', 'rep_by', 'location', 'permit_issue_date',
            'tct_oct_no', 'tax_dec_no', 'lot_no', 'area',
            'species_name', 'no_of_trees', 'gross_volume', 'total_volume_granted'
        ]
        widgets = {
            'tcp_no': forms.TextInput(attrs={
                'placeholder': 'Enter TCP number',
                'class': 'form-input'
            }),
            'permittee': forms.TextInput(attrs={
                'placeholder': 'Enter permittee name',
                'class': 'form-input'
            }),
            'rep_by': forms.TextInput(attrs={
                'placeholder': 'Enter representative name',
                'class': 'form-input'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'Enter location',
                'class': 'form-input'
            }),
            'permit_issue_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'tct_oct_no': forms.TextInput(attrs={
                'placeholder': 'Enter TCT/OCT number',
                'class': 'form-input'
            }),
            'tax_dec_no': forms.TextInput(attrs={
                'placeholder': 'Enter tax declaration number',
                'class': 'form-input'
            }),
            'lot_no': forms.TextInput(attrs={
                'placeholder': 'Enter lot number',
                'class': 'form-input'
            }),
            'area': forms.NumberInput(attrs={
                'placeholder': 'Enter area in hectares',
                'step': '0.01',
                'class': 'form-input'
            }),
            'species_name': forms.TextInput(attrs={
                'placeholder': 'Enter species name',
                'class': 'form-input'
            }),
            'no_of_trees': forms.NumberInput(attrs={
                'placeholder': 'Enter number of trees',
                'class': 'form-input'
            }),
            'gross_volume': forms.NumberInput(attrs={
                'placeholder': 'Enter gross volume',
                'step': '0.01',
                'class': 'form-input'
            }),
            'total_volume_granted': forms.NumberInput(attrs={
                'placeholder': 'Enter total volume granted',
                'step': '0.01',
                'class': 'form-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Required fields validation
        required_fields = ['tcp_no', 'permittee', 'rep_by', 'location', 'permit_issue_date', 
                         'species_name', 'no_of_trees', 'gross_volume', 'total_volume_granted']
        
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'This field is required.')

        # TCP Number format validation
        tcp_no = cleaned_data.get('tcp_no')
        if tcp_no:
            if not re.match(r'^[A-Za-z0-9-]+$', tcp_no):
                self.add_error('tcp_no', 'TCP number can only contain letters, numbers, and hyphens.')
            if len(tcp_no) < 3:
                self.add_error('tcp_no', 'TCP number must be at least 3 characters long.')

        # Name validations
        permittee = cleaned_data.get('permittee')
        if permittee:
            if len(permittee.strip()) < 2:
                self.add_error('permittee', 'Permittee name must be at least 2 characters long.')
            if not re.match(r'^[A-Za-z\s\'-]+$', permittee):
                self.add_error('permittee', 'Permittee name can only contain letters, spaces, hyphens, and apostrophes.')

        rep_by = cleaned_data.get('rep_by')
        if rep_by:
            if len(rep_by.strip()) < 2:
                self.add_error('rep_by', 'Representative name must be at least 2 characters long.')
            if not re.match(r'^[A-Za-z\s\'-]+$', rep_by):
                self.add_error('rep_by', 'Representative name can only contain letters, spaces, hyphens, and apostrophes.')

        # Location validation
        location = cleaned_data.get('location')
        if location and len(location.strip()) < 5:
            self.add_error('location', 'Location must be at least 5 characters long.')

        # Date validation
        permit_issue_date = cleaned_data.get('permit_issue_date')
        if not permit_issue_date:
            self.add_error('permit_issue_date', 'This field is required.')

        # Numeric validations
        area = cleaned_data.get('area')
        if area is not None and area <= 0:
            self.add_error('area', 'Area must be greater than 0.')

        no_of_trees = cleaned_data.get('no_of_trees')
        if no_of_trees is not None:
            if no_of_trees <= 0:
                self.add_error('no_of_trees', 'Number of trees must be greater than 0.')
            if no_of_trees > 1000:  # Example maximum limit
                self.add_error('no_of_trees', 'Number of trees cannot exceed 1000.')

        gross_volume = cleaned_data.get('gross_volume')
        total_volume_granted = cleaned_data.get('total_volume_granted')

        if gross_volume is not None and gross_volume <= 0:
            self.add_error('gross_volume', 'Gross volume must be greater than 0.')

        if total_volume_granted is not None:
            if total_volume_granted <= 0:
                self.add_error('total_volume_granted', 'Total volume granted must be greater than 0.')
            if gross_volume and total_volume_granted > gross_volume:
                self.add_error('total_volume_granted', 'Total volume granted cannot exceed gross volume.')

        # Document number validations
        tct_oct_no = cleaned_data.get('tct_oct_no')
        if tct_oct_no and not re.match(r'^[A-Za-z0-9-]+$', tct_oct_no):
            self.add_error('tct_oct_no', 'TCT/OCT number can only contain letters, numbers, and hyphens.')

        tax_dec_no = cleaned_data.get('tax_dec_no')
        if tax_dec_no and not re.match(r'^[A-Za-z0-9-]+$', tax_dec_no):
            self.add_error('tax_dec_no', 'Tax declaration number can only contain letters, numbers, and hyphens.')

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make specific fields required
        required_fields = ['tcp_no', 'permittee', 'rep_by', 'location', 'permit_issue_date', 
                         'species_name', 'no_of_trees', 'gross_volume', 'total_volume_granted']
        for field in required_fields:
            self.fields[field].required = True

# ChainsawForm
class ChainsawForm(forms.ModelForm):
    PURPOSE_CHOICES = [
        ('cutting_private_plantation_commercial', 'Cutting in Private Plantation for Commercial Use'),
        ('cutting_tenure_area_personal_non_commercial', 'Cutting in Tenure Area for Personal/Non-Commercial Use'),
    ]
    purpose = forms.ChoiceField(choices=PURPOSE_CHOICES)

    class Meta:
        model = Chainsaw
        fields = [
            'no', 'year', 'region', 'penro', 'cenro', 'province',
            'name', 'municipality', 'purpose', 'date_acquisition',
            'ctpo_number', 'brand', 'model', 'serial_number',
            'color', 'horse_power', 'guidebar_length', 'denr_sticker',
            'registration_status', 'date_issued', 'expiry_date',
            'date_renewal', 'file'
        ]
        widgets = {
            'date_acquisition': forms.DateInput(attrs={'type': 'date'}),
            'date_issued': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'date_renewal': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields not required by default
        for field in self.fields:
            self.fields[field].required = False

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Add file validation if needed
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if file.content_type not in allowed_types:
                raise forms.ValidationError('Invalid file type. Please upload PDF, DOC, DOCX, JPG or PNG files only.')
        return file

# WoodForm
class WoodForm(forms.ModelForm):
    class Meta:
        model = Wood
        fields = [
            'name', 'type', 'integrated', 'wpp_number', 
            'business', 'plant', 'drc', 'alr',
            'longitude', 'latitude', 'local_volume', 
            'imported_volume', 'supplier_info', 'area',
            'date_issued', 'date_released', 'expiry_date',
            'approved_by', 'wood_status'
        ]
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'}),
            'date_released': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'drc': forms.NumberInput(attrs={'step': '0.01'}),
            'alr': forms.NumberInput(attrs={'step': '0.01', 'readonly': True}),
            'local_volume': forms.NumberInput(attrs={'step': '0.001'}),
            'imported_volume': forms.NumberInput(attrs={'step': '0.001'}),
            'wood_status': forms.Select(
                choices=[
                    ('ACTIVE_NEW', 'Active/New'),
                    ('ACTIVE_RENEWAL', 'Active/Renewed'),
                    ('EXISTING', 'Existing'),
                    ('EXPIRED', 'Expired'),
                    ('CANCELLED', 'Cancelled')
                ]
            )
        }

    def clean(self):
        cleaned_data = super().clean()
        date_issued = cleaned_data.get('date_issued')
        expiry_date = cleaned_data.get('expiry_date')

        if date_issued and expiry_date:
            if expiry_date < date_issued:
                raise forms.ValidationError('Expiry date cannot be before date issued')

            # 5-year validation
            max_date = date_issued + timezone.timedelta(days=5*365)
            if expiry_date > max_date:
                raise forms.ValidationError('Expiry date cannot be more than 5 years from date issued')

        return cleaned_data

    def clean_volume_cubic_meter(self):
        volume = self.cleaned_data.get('volume_cubic_meter')
        if volume is not None and volume < 0:
            raise forms.ValidationError("Volume cannot be negative")
        return volume