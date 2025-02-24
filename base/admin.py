# admin.py
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import path
from .models import Lumber, Cutting, Chainsaw, Wood, CuttingRecord

# Custom admin login view
def custom_admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('admin:index')  # Redirect to admin index page
        else:
            messages.error(request, "Invalid credentials. Please try again.")
    return render(request, "admin/login.html")

@admin.register(Lumber)
class LumberAdmin(admin.ModelAdmin):
    list_display = ('no', 'trade_name', 'manager_owner', 'permit_no', 'date_issued', 'expiry_date', 'volume_cubic_meter')
    list_filter = ('species', 'date_issued', 'created_at')
    search_fields = ('no', 'trade_name', 'manager_owner', 'permit_no')
    date_hierarchy = 'date_issued'
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new record
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Cutting)
class CuttingAdmin(admin.ModelAdmin):
    list_display = ['permit_type', 'permit_number', 'date_issued', 'expiry_date', 'gross_volume', 'net_volume']
    list_filter = ['date_issued', 'permit_type']
    date_hierarchy = 'date_issued'
    search_fields = ['permit_number', 'permit_type']
    readonly_fields = ['expiry_date', 'net_volume']

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new record
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Chainsaw)
class ChainsawAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'brand', 'model', 'purpose', 'registration_status', 'date_issued', 'expiry_date')
    list_filter = ('registration_status', 'purpose', 'brand')
    search_fields = ('name', 'serial_number', 'brand', 'model')
    date_hierarchy = 'date_issued'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('no', 'year', 'region')
        }),
        ('Location Details', {
            'fields': ('penro', 'cenro', 'province')
        }),
        ('Owner Details', {
            'fields': ('name', 'municipality')
        }),
        ('Chainsaw Details', {
            'fields': ('brand', 'model', 'serial_number')
        }),
        ('Additional Information', {
            'fields': ('purpose', 'date_acquired', 'cert_reg_number', 'color', 
                      'registration_status', 'date_renewal', 'horse_power', 
                      'guidebar_length', 'denr_sticker')
        }),
        ('Permit Details', {
            'fields': ('ctpo_number', 'date_issued', 'expiry_date')
        }),
        ('Documentation', {
            'fields': ('file',)
        })
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ('created_at', 'updated_at')
        return ()

@admin.register(Wood)
class WoodAdmin(admin.ModelAdmin):
    pass  # Add appropriate fields when Wood model is implemented

@admin.register(CuttingRecord)
class CuttingRecordAdmin(admin.ModelAdmin):
    list_display = [
        'parent_tcp',
        'species',
        'number_of_trees',
        'volume',
        'calculated_volume',
        'remaining_balance',
        'date_added'
    ]
    list_filter = ['species', 'date_added']
    search_fields = ['parent_tcp__permit_number', 'species']
    readonly_fields = ['calculated_volume', 'remaining_balance', 'date_added']
