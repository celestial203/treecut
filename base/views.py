from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from base.forms import LoginForm, LumberForm, CuttingForm, ChainsawForm, WoodForm, CuttingRecordForm
from base.models import Lumber, Cutting, Chainsaw, Wood, CuttingRecord, CuttingPermit
from datetime import datetime, timedelta, date
from django.utils import timezone
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
from django.http import JsonResponse
from django.urls import reverse

# Login view
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

# Logout view
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# Dashboard view
@login_required
def dashboard(request):
    # Get current date
    current_date = timezone.now().date()

    # Cutting Permits counts
    cutting_count = Cutting.objects.count()
    expired_cutting_count = Cutting.objects.filter(
        expiry_date__lt=current_date
    ).count()

    # Lumber Records counts
    lumber_count = Lumber.objects.count()
    expired_lumber_count = Lumber.objects.filter(
        expiry_date__lt=current_date
    ).count()

    # Chainsaw counts
    chainsaw_count = Chainsaw.objects.count()
    expired_chainsaw_count = Chainsaw.objects.filter(
        expiry_date__lt=current_date
    ).count()

    # Wood counts
    wood_count = Wood.objects.count()
    expired_wood_count = Wood.objects.filter(
        expiry_date__lt=current_date
    ).count()

    context = {
        'cutting_count': cutting_count,
        'expired_cutting_count': expired_cutting_count,
        'lumber_count': lumber_count,
        'expired_lumber_count': expired_lumber_count,
        'chainsaw_count': chainsaw_count,
        'expired_chainsaw_count': expired_chainsaw_count,
        'wood_count': wood_count,
        'expired_wood_count': expired_wood_count,
    }

    return render(request, 'dashboard.html', context)

@login_required
def cutting(request):
    if request.method == 'POST':
        form = CuttingForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                cutting = form.save(commit=False)
                
                # Calculate net volume
                if cutting.gross_volume:
                    cutting.net_volume = round(float(cutting.gross_volume) * 0.70, 2)
                
                cutting.save()
                messages.success(request, f'Successfully added cutting record for {cutting.permit_type}-{cutting.permit_number}')
                return redirect('cutting')
            except Exception as e:
                messages.error(request, f'Error saving record: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_data = {
            'date_issued': timezone.now().date()  # Set initial date this way
        }
        form = CuttingForm(initial=initial_data)  # Pass initial data to form

    cuttings = Cutting.objects.all().order_by('-created_at')
    context = {
        'form': form,
        'cuttings': cuttings,
        'today': timezone.now().date(),
        'page_title': 'Cutting Records'
    }
    return render(request, 'cutting.html', context)

@login_required
def wood(request):
    current_date = timezone.now().date()
    
    # Get all records
    wood_records = Wood.objects.all().order_by('-date_issued')
    
    # Count expired records from the actual table data
    expired_records = [record for record in wood_records if record.expiry_date and record.expiry_date < current_date]
    expired_count = len(expired_records)
    
    # Count records expiring soon from the actual table data
    thirty_days_from_now = current_date + timedelta(days=30)
    expiring_soon_records = [
        record for record in wood_records 
        if record.expiry_date 
        and record.expiry_date > current_date 
        and record.expiry_date <= thirty_days_from_now
    ]
    expiring_soon_count = len(expiring_soon_records)

    context = {
        'wood_records': wood_records,
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
    }
    return render(request, 'wood.html', context)

#FOR LUMBERRRR #####
@login_required
def lumber(request):
    current_date = timezone.now().date()
    lumber_records = Lumber.objects.all()
    
    # Count expired records
    expired_count = Lumber.objects.filter(expiry_date__lt=current_date).count()
    
    # Count records expiring in next 30 days but not expired yet
    thirty_days_from_now = current_date + timedelta(days=30)
    expiring_soon_count = Lumber.objects.filter(
        expiry_date__gte=current_date,
        expiry_date__lte=thirty_days_from_now
    ).count()

    context = {
        'lumber_records': lumber_records,
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
    }
    
    return render(request, 'lumber.html', context)

@login_required
def search(request):
    return render(request, 'search.html')

### FOR CHAINSAW### 
@login_required(login_url='login')
def chainsaw(request):
    current_date = timezone.now().date()
    chainsaw_records = Chainsaw.objects.all()
    
    if request.method == 'POST':
        form = ChainsawForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chainsaw record added successfully!')
            return redirect('chainsaw')
        else:
            messages.error(request, 'Error adding chainsaw record. Please check the form.')
    else:
        form = ChainsawForm()
    
    # Count expired records
    expired_count = Chainsaw.objects.filter(
        expiry_date__lt=current_date
    ).count()
    
    # Count records expiring in next 30 days but not expired yet
    thirty_days_from_now = current_date + timedelta(days=30)
    expiring_soon_count = Chainsaw.objects.filter(
        expiry_date__gt=current_date,
        expiry_date__lte=thirty_days_from_now
    ).count()

    context = {
        'form': form,
        'chainsaw_records': chainsaw_records,
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
    }
    return render(request, 'chainsaw.html', context)

@login_required
def profile(request):
    return render(request, 'profile.html')
####FOR LUMBER ######
@login_required
def edit_recordlumber(request, pk):
    lumber = get_object_or_404(Lumber, pk=pk)
    if request.method == 'POST':
        form = LumberForm(request.POST, instance=lumber)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lumber record updated successfully!')
            return redirect('lumber')
    else:
        form = LumberForm(instance=lumber)
    
    return render(request, 'edit_lumber.html', {
        'form': form,
        'lumber': lumber
    })
#FOR CUTTING ####
@login_required
def edit_cutting(request, cutting_id):
    cutting = get_object_or_404(Cutting, id=cutting_id)
    if request.method == 'POST':
        form = CuttingForm(request.POST, request.FILES, instance=cutting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Record updated successfully')
            return redirect('view_cutting', cutting_id=cutting_id)
    else:
        form = CuttingForm(instance=cutting)
    
    return render(request, 'edit_cutting.html', {
        'form': form,
        'cutting': cutting
    })

def view_cutting(request, cutting_id):
    cutting = get_object_or_404(Cutting, id=cutting_id)
    today = date.today()
    context = {
        'cutting': cutting,
        'page_title': 'View Cutting Record',
        'today': today
    }
    return render(request, 'view_cutting.html', context)

@login_required
def add_cutting_record(request, cutting_id):
    cutting = get_object_or_404(Cutting, id=cutting_id)
    
    if request.method == 'POST':
        form = CuttingRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.parent_tcp = cutting
            record.save()
            
            # Update parent cutting situation to "Good" when volume is added
            cutting.situation = 'Good'
            cutting.save()
            
            messages.success(request, 'Record added successfully!')
            return redirect('view_cutting', cutting_id=cutting_id)
    
    # Get existing records for display
    records = CuttingRecord.objects.filter(parent_tcp=cutting).order_by('-date_added')
    
    context = {
        'cutting': cutting,
        'parent_tcp': cutting,  # For breadcrumb
        'records': records,
    }
    return render(request, 'add_cutting_record.html', context)

###FOR CHAINSAW####
@login_required(login_url='login')
def edit_chainsaw(request, pk):
    chainsaw = get_object_or_404(Chainsaw, id=pk)
    
    if request.method == 'POST':
        form = ChainsawForm(request.POST, request.FILES, instance=chainsaw)
        if form.is_valid():
            # Handle file upload
            if 'file' in request.FILES:
                # If there's an existing file, delete it
                if chainsaw.file:
                    if os.path.isfile(chainsaw.file.path):
                        os.remove(chainsaw.file.path)
                
                file = request.FILES['file']
                chainsaw.file = file
            elif 'file-clear' in request.POST:
                # If clearing the file, delete it
                if chainsaw.file:
                    if os.path.isfile(chainsaw.file.path):
                        os.remove(chainsaw.file.path)
                chainsaw.file = None
                
            chainsaw.save()
            messages.success(request, 'Chainsaw registration successfully updated!')
            return redirect('chainsaw')
        else:
            messages.error(request, 'Error updating chainsaw registration. Please check the form.')
    else:
        form = ChainsawForm(instance=chainsaw)

    context = {
        'form': form,
        'chainsaw': chainsaw,
    }
    
    return render(request, 'edit_chainsaw.html', context)

def your_save_view(request):
    # ... your existing save logic ...
    messages.success(request, 'Record successfully added!')
    return redirect('chainsaw.html')

@login_required
def edit_wood(request, pk):
    wood = get_object_or_404(Wood, pk=pk)
    if request.method == 'POST':
        form = WoodForm(request.POST, instance=wood)
        if form.is_valid():
            form.save()
            messages.success(request, 'Wood record updated successfully!')
            return redirect('wood')
    else:
        form = WoodForm(instance=wood)
    return render(request, 'edit_wood.html', {'form': form, 'wood': wood})

def login_page(request):
    return render(request, 'login.html')

@login_required
def edit_cutting_record(request, record_id):
    record = get_object_or_404(CuttingRecord, id=record_id)
    
    if request.method == 'POST':
        form = CuttingRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Record updated successfully!')
            return redirect('add_cutting_record', cutting_id=record.parent_tcp.id)
    else:
        form = CuttingRecordForm(instance=record)
    
    return render(request, 'edit_cutting_record.html', {
        'form': form,
        'record': record
    })

def cutting_records(request):
    cuttings = Cutting.objects.all().order_by('-created_at')
    today = date.today()
    
    context = {
        'cuttings': cuttings,
        'today': today,
    }
    return render(request, 'CuttingRecord.html', context)

def cutting_records(request):
    cuttings = Cutting.objects.all().order_by('-created_at')
    today = date.today()
    
    context = {
        'cuttings': cuttings,
        'today': today,
    }
    return render(request, 'CuttingRecord.html', context)