# forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from .models import Lumber, Cutting, Chainsaw, Wood, CuttingRecord, VolumeRecord
import re
from .models import CuttingRecord
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta, date
from django.contrib.auth.forms import AuthenticationForm
from decimal import Decimal
from django.core.validators import MinValueValidator, DecimalValidator


# Get the user model
User = get_user_model()
##LOGIN FORM#####
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

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
        exclude = ['created_by']
        fields = [
            'no',
            'trade_name',
            'manager_owner',
            'contact_number',
            'gender',
            'brgy',
            'municipality',
            'province',
            'source_supplier',
            'permit_no',
            'date_issued',
            'expiry_date',
            'volume_cubic_meter',
            'species',
            'file'
        ]
        widgets = {
            'no': forms.TextInput(attrs={'readonly': 'readonly'}),
            'trade_name': forms.TextInput(attrs={'required': True, 'class': 'form-input'}),
            'manager_owner': forms.TextInput(attrs={'required': True, 'class': 'form-input'}),
            'contact_number': forms.TextInput(attrs={'required': True, 'pattern': r'^09\d{9}$', 'class': 'form-input'}),
            'gender': forms.Select(attrs={'required': True, 'class': 'form-input'}),
            'brgy': forms.TextInput(attrs={'required': True, 'class': 'form-input'}),
            'municipality': forms.TextInput(attrs={'required': True, 'class': 'form-input'}),
            'province': forms.TextInput(attrs={'required': True, 'class': 'form-input'}),
            'source_supplier': forms.TextInput(attrs={'required': True, 'class': 'form-input'}),
            'permit_no': forms.TextInput(attrs={'required': True, 'class': 'form-input'}),
            'date_issued': forms.DateInput(attrs={'type': 'date', 'required': True, 'class': 'form-input'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'volume_cubic_meter': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'required': True, 'class': 'form-input'}),
            'species': forms.TextInput(attrs={'required': True, 'class': 'form-input'}),
            'file': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date_issued = cleaned_data.get('date_issued')
        expiry_date = cleaned_data.get('expiry_date')

        # Validate date_issued is not in the future
        if date_issued and date_issued > timezone.now().date():
            self.add_error('date_issued', 'Date issued cannot be in the future')

        # Validate expiry_date is after date_issued if provided
        if date_issued and expiry_date and expiry_date < date_issued:
            self.add_error('expiry_date', 'Expiry date must be after date issued')

        return cleaned_data

    def clean_volume_cubic_meter(self):
        volume = self.cleaned_data.get('volume_cubic_meter')
        if volume is not None:
            if volume <= 0:
                raise forms.ValidationError("Volume must be greater than 0")
        return volume

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if not contact_number:
            raise forms.ValidationError("Contact number is required")
        if not contact_number.startswith('09'):
            raise forms.ValidationError("Contact number must start with '09'")
        if len(contact_number) != 11:
            raise forms.ValidationError("Contact number must be 11 digits long")
        if not contact_number.isdigit():
            raise forms.ValidationError("Contact number must contain only digits")
        return contact_number

# CuttingForm
class CuttingForm(forms.ModelForm):
    class Meta:
        model = Cutting
        fields = [
            'permit_type',
            'permit_number',
            'date_issued',
            'expiry_date',
            'permittee',
            'rep_by',
            'location',
            'latitude',
            'longitude',
            'tct_oct_no',
            'tax_dec_no',
            'lot_no',
            'area',
            'species',
            'no_of_trees',
            'total_volume_granted',
            'gross_volume',
            'net_volume',
            'permit_file',
            'status',
            'situation'
        ]
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'gross_volume': forms.NumberInput(attrs={'step': '0.01'}),
            'net_volume': forms.NumberInput(attrs={'step': '0.01', 'readonly': True}),
            'total_volume_granted': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        print("Form cleaned data:", cleaned_data)
        return cleaned_data

# ChainsawForm
class ChainsawForm(forms.ModelForm):
    class Meta:
        model = Chainsaw
        fields = [
            'no', 'year', 'region',
            'penro', 'cenro', 'province',
            'name', 'municipality',
            'brand', 'model', 'serial_number',
            'purpose', 'date_acquired',
            'cert_reg_number', 'color',
            'registration_status', 'date_renewal',
            'horse_power', 'guidebar_length',
            'denr_sticker',
            'ctpo_number', 'date_issued', 'expiry_date',
            'file', 'municipality', 'province'
        ]
        widgets = {
            'date_acquired': forms.DateInput(attrs={'type': 'date'}),
            'date_renewal': forms.DateInput(attrs={'type': 'date'}),
            'date_issued': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'purpose': forms.Select(attrs={'class': 'form-select'}),
            'registration_status': forms.Select(attrs={'class': 'form-select'})
        }

# WoodForm
class WoodForm(forms.ModelForm):
    class Meta:
        model = Wood
        fields = [
            'name', 
            'type', 
            'wpp_number', 
            'business_name',
            'address',
            'drc',
            'alr',
            'longitude',
            'latitude',
            'supplier_info',
            'local_volume',
            'imported_volume',
            'area',
            'approved_by',
            'date_issued',
            'date_released',
            'expiry_date',
            'wood_status',
            'attachment'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any field-specific widgets or attributes
        self.fields['date_issued'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['date_released'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['expiry_date'].widget = forms.DateInput(attrs={'type': 'date'})
        
        # Remove the fields that don't exist in the model
        if 'plant' in self.fields:
            del self.fields['plant']
        if 'business' in self.fields:
            del self.fields['business']
        if 'integrated' in self.fields:
            del self.fields['integrated']
        
        # Mark required fields
        required_fields = [
            'name', 'type', 'wpp_number', 'business_name', 'address',
            'drc', 'approved_by', 'date_issued', 
            'date_released', 'wood_status'
        ]
        for field in required_fields:
            self.fields[field].required = True

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def clean_date_issued(self):
        date_issued = self.cleaned_data.get('date_issued')
        return date_issued

    def clean_alr(self):
        alr = self.cleaned_data.get('alr')
        # Remove any specific decimal place validation
        return alr

# CuttingRecordForm
class CuttingRecordForm(forms.ModelForm):
    class Meta:
        model = CuttingRecord
        fields = ['species', 'other_species', 'number_of_trees', 'volume', 'calculated_volume', 'remarks']
        widgets = {
            'volume': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01'
            }),
            'number_of_trees': forms.NumberInput(attrs={
                'class': 'form-input'
            }),
            'species': forms.Select(attrs={
                'class': 'form-input'
            }),
            'other_species': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter species name'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        species = cleaned_data.get('species')
        other_species = cleaned_data.get('other_species')
        
        if species == 'Others' and not other_species:
            raise ValidationError({'other_species': 'Please specify the species name when selecting Others'})
        
        volume = cleaned_data.get('volume')
        calculated_volume = cleaned_data.get('calculated_volume')
        
        if volume and species:
            if species.endswith('Fuel Wood'):
                cleaned_data['calculated_volume'] = volume
            elif species.endswith('SL'):
                calculated_volume = volume + (volume * Decimal('0.40'))
                cleaned_data['calculated_volume'] = calculated_volume
            else:
                calculated_volume = volume + (volume * Decimal('0.30'))
                cleaned_data['calculated_volume'] = calculated_volume
            
        return cleaned_data

class VolumeRecordForm(forms.ModelForm):
    class Meta:
        model = VolumeRecord
        fields = [
            'date',
            'species',
            'volume',
            'number_of_trees',
            'remarks',
            'attachment'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'required': True
            }),
            'remarks': forms.Textarea(attrs={'rows': 3}),
            'number_of_trees': forms.NumberInput(attrs={'class': 'form-input'}),
            'species': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf,.doc,.docx'
            })
        }

    def clean_volume(self):
        volume = self.cleaned_data.get('volume')
        if volume and volume <= 0:
            raise ValidationError("Volume must be greater than 0")
        return volume