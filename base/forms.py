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
        fields = '__all__'
        widgets = {
            'date_issued': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'required': True
                }
            ),
            'expiry_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Format dates for the form
            if self.instance.date_issued:
                self.initial['date_issued'] = self.instance.date_issued.strftime('%Y-%m-%d')

    def clean_date_issued(self):
        date_issued = self.cleaned_data.get('date_issued')
        if not date_issued:
            raise forms.ValidationError("Date issued is required.")
        
        # Prevent future dates
        if date_issued > timezone.now().date():
            raise forms.ValidationError("Date issued cannot be in the future.")
            
        return date_issued

    def clean(self):
        cleaned_data = super().clean()
        # Any additional form validation logic here
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # The net_volume and expiry_date will be calculated in the model's save method
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
            'name', 'type', 'wpp_number', 'integrated', 
            'business', 'plant', 'drc', 'alr',
            'longitude', 'latitude', 'supplier_info',
            'local_volume', 'imported_volume', 'area',
            'approved_by', 'date_issued', 'date_released',
            'expiry_date', 'wood_status', 'attachment'
        ]
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'}),
            'date_released': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the type field has both options
        self.fields['type'].choices = [
            ('', 'Select Type'),
            ('Resawmill-new', 'Resawmill-new'),
            ('Resawmill-renew', 'Resawmill-renew')
        ]
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
        fields = ['species', 'number_of_trees', 'volume', 'calculated_volume', 'remarks']
        widgets = {
            'volume': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01'
            }),
            'number_of_trees': forms.NumberInput(attrs={
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

    def clean_number_of_trees(self):
        number_of_trees = self.cleaned_data.get('number_of_trees')
        if number_of_trees <= 0:
            raise ValidationError("Number of trees must be greater than 0")
        return number_of_trees

    def clean(self):
        cleaned_data = super().clean()
        volume = cleaned_data.get('volume')
        species = cleaned_data.get('species')
        calculated_volume = cleaned_data.get('calculated_volume')
        
        if volume and species:
            if species.endswith('Fuel Wood'):
                # For Fuel Wood, use the volume directly as deduction
                cleaned_data['calculated_volume'] = volume
            elif species.endswith('SL'):
                # For SL species, add 40%
                calculated_volume = volume + (volume * Decimal('0.40'))
                cleaned_data['calculated_volume'] = calculated_volume
            else:
                # For regular species, add 30%
                calculated_volume = volume + (volume * Decimal('0.30'))
                cleaned_data['calculated_volume'] = calculated_volume
            
        return cleaned_data

class VolumeRecordForm(forms.ModelForm):
    class Meta:
        model = VolumeRecord
        fields = [
            'species',
            'volume',
            'number_of_trees',
            'remarks',
            'attachment'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
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