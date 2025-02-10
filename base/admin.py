# admin.py
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import path
from .models import Lumber, Cutting, Chainsaw, Wood

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
    list_display = ('tcp_no', 'permittee', 'location', 'permit_issue_date', 'species_name', 'no_of_trees')
    list_filter = ('permit_issue_date', 'created_at')
    search_fields = ('tcp_no', 'permittee', 'location')
    date_hierarchy = 'permit_issue_date'
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new record
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Chainsaw)
class ChainsawAdmin(admin.ModelAdmin):
    list_display = ('no', 'name', 'brand', 'model', 'serial_number', 'date_issued', 'expiry_date')
    list_filter = ('date_issued', 'expiry_date')
    search_fields = ('no', 'name', 'brand', 'serial_number')
    date_hierarchy = 'date_issued'

@admin.register(Wood)
class WoodAdmin(admin.ModelAdmin):
    pass  # Add appropriate fields when Wood model is implemented
