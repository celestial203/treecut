# forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from .models import Lumber, Cutting, Chainsaw, Wood
import re
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.contrib.auth.forms import AuthenticationForm


# Get the user model
User = get_user_model()
##LOGIN FORM#####
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

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
            'tcp_no',
            'permittee',
            'location',
            'tct_oct_no',
            'tax_dec_no',
            'lot_no',
            'area',
            'no_of_trees',
            'species',
            'total_volume_granted',
            'gross_volume',
            'permit_issue_date',
            'rep_by'
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
            'location': forms.TextInput(attrs={
                'placeholder': 'Enter location',
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
            'no_of_trees': forms.NumberInput(attrs={
                'placeholder': 'Enter number of trees',
                'class': 'form-input'
            }),
            'species': forms.TextInput(attrs={
                'placeholder': 'Enter species name',
                'class': 'form-input'
            }),
            'total_volume_granted': forms.NumberInput(attrs={
                'placeholder': 'Enter total volume granted',
                'step': '0.01',
                'class': 'form-input'
            }),
            'gross_volume': forms.NumberInput(attrs={
                'placeholder': 'Enter gross volume',
                'step': '0.01',
                'class': 'form-input'
            }),
            'permit_issue_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        gross_volume = cleaned_data.get('gross_volume')
        total_volume_granted = cleaned_data.get('total_volume_granted')

        if gross_volume and total_volume_granted:
            if gross_volume < 0:
                raise forms.ValidationError("Gross volume cannot be negative")
            if total_volume_granted < 0:
                raise forms.ValidationError("Total volume granted cannot be negative")

        permit_issue_date = cleaned_data.get('permit_issue_date')
        if permit_issue_date:
            expiry_date = permit_issue_date + timedelta(days=50)
            if expiry_date < timezone.now().date():
                raise forms.ValidationError("Permit has expired")

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