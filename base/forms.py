# forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from .models import Lumber, Cutting, Chainsaw, Wood, CuttingRecord
import re
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
        fields = [
            'no',
            'trade_name',
            'manager_owner',
            'permit_no',
            'date_issued',
            'expiry_date',
            'volume_cubic_meter',
            'species'
        ]
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'})
        }

    def clean(self):
        cleaned_data = super().clean()
        date_issued = cleaned_data.get('date_issued')
        expiry_date = cleaned_data.get('expiry_date')
        
        if date_issued and expiry_date and expiry_date < date_issued:
            raise forms.ValidationError("Expiry date cannot be earlier than date issued.")
        
        return cleaned_data

# CuttingForm
class CuttingForm(forms.ModelForm):
    class Meta:
        model = Cutting
        fields = [
            'permit_type', 'permit_number', 'permit_issue_date', 'expiry_date',
            'situation', 'permittee', 'rep_by', 'location', 'latitude', 'longitude',
            'tct_oct_no', 'tax_dec_no', 'lot_no', 'area', 'species', 'no_of_trees',
            'total_volume_granted', 'gross_volume', 'net_volume', 'permit_file'
        ]
        widgets = {
            'permit_issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'readonly': 'readonly'}),
            'net_volume': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'permit_file': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields required
        self.fields['permit_type'].required = True
        self.fields['permit_number'].required = True
        self.fields['permit_issue_date'].required = True
        self.fields['permittee'].required = True
        
        # Make certain fields not required
        self.fields['permit_file'].required = False
        self.fields['expiry_date'].required = False
        self.fields['net_volume'].required = False

    def clean_gross_volume(self):
        gross_volume = self.cleaned_data.get('gross_volume')
        if gross_volume:
            # Ensure only 2 decimal places
            return round(float(gross_volume), 2)
        return gross_volume

    def clean(self):
        cleaned_data = super().clean()
        gross_volume = cleaned_data.get('gross_volume')
        
        if gross_volume:
            # Calculate net volume (70% of gross volume)
            net_volume = float(gross_volume) * 0.70
            cleaned_data['net_volume'] = round(net_volume, 2)
            
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ensure calculations are applied
        if instance.gross_volume:
            instance.net_volume = float(instance.gross_volume) * 0.70
            
        if commit:
            instance.save()
        return instance

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
            'name', 'type', 'integrated',
            'wpp_number', 'business', 'plant',
            'drc', 'alr', 'longitude', 'latitude',
            'local_volume', 'imported_volume',
            'supplier_info', 'area',
            'date_issued', 'date_released', 'expiry_date',
            'approved_by', 'wood_status'
        ]
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'}),
            'date_released': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'integrated': forms.Select(attrs={'class': 'form-select'}),
            'wood_status': forms.Select(attrs={'class': 'form-select'})
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

# CuttingRecordForm
class CuttingRecordForm(forms.ModelForm):
    class Meta:
        model = CuttingRecord
        fields = ['species', 'no_of_trees', 'volume', 'remarks']
        widgets = {
            'volume': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01'
            }),
            'no_of_trees': forms.NumberInput(attrs={
                'class': 'form-input'
            }),
            'species': forms.TextInput(attrs={
                'class': 'form-input'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3
            })
        }

    def clean_volume(self):
        volume = self.cleaned_data.get('volume')
        if volume <= 0:
            raise ValidationError("Volume must be greater than 0")
        return volume

    def clean(self):
        cleaned_data = super().clean()
        volume = cleaned_data.get('volume')
        
        if volume:
            # Calculate the volume with 30% addition
            calculated_volume = volume + (volume * Decimal('0.30'))
            cleaned_data['calculated_volume'] = calculated_volume
            
        return cleaned_data