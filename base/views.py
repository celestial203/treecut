from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from base.forms import LoginForm, LumberForm, CuttingForm, ChainsawForm, WoodForm, CuttingRecordForm
from base.models import Lumber, Cutting, Chainsaw, Wood, CuttingRecord
from datetime import datetime, timedelta, date
from django.utils import timezone
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal

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
                cutting = form.save()
                messages.success(request, f'Successfully added cutting record for {cutting.permit_type}-{cutting.permit_number}')
                return redirect('cutting')
            except Exception as e:
                messages.error(request, f'Error saving record: {str(e)}')
        else:
            # Print form errors to console for debugging
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CuttingForm()

    # Get all cutting records ordered by created_at
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
def edit_cutting(request, pk):
    cutting = get_object_or_404(Cutting, pk=pk)
    if request.method == 'POST':
        form = CuttingForm(request.POST, instance=cutting)
        if form.is_valid():
            try:
                cutting = form.save()
                messages.success(request, f'Successfully updated cutting record for TCP No. {cutting.tcp_no}')
                return redirect('view_cutting', pk=cutting.pk)
            except Exception as e:
                messages.error(request, f'Error updating record: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CuttingForm(instance=cutting)
    
    return render(request, 'edit_cutting.html', {
        'form': form,
        'cutting': cutting
    })

def view_cutting(request, pk):
    try:
        cutting = get_object_or_404(Cutting, pk=pk)
        cutting_records = CuttingRecord.objects.filter(parent_tcp=cutting)
        
        # Calculate net volume
        net_volume = cutting.gross_volume * Decimal('0.7') if cutting.gross_volume else None

        # Get the last update timestamp
        last_updated = cutting.updated_at if hasattr(cutting, 'updated_at') else None
        
        # Add success message if coming from edit
        if request.GET.get('edited'):
            messages.success(request, f'Record for TCP No. {cutting.tcp_no} was successfully updated.')
        
        context = {
            'cutting': cutting,
            'cutting_records': cutting_records,
            'net_volume': net_volume,
            'last_updated': last_updated
        }
        return render(request, 'view_cutting.html', context)
    except Exception as e:
        messages.error(request, f'Error viewing record: {str(e)}')
        return redirect('cutting')

@login_required
def add_cutting_record(request, permit_number):
    parent_tcp = get_object_or_404(Cutting, permit_number=permit_number)
    cutting_records = CuttingRecord.objects.filter(parent_tcp=parent_tcp).order_by('date_added')
    
    # Handle POST request
    if request.method == 'POST':
        volume = Decimal(request.POST.get('volume', 0))
        species = request.POST.get('species')
        remarks = request.POST.get('remarks', '')
        number_of_trees = int(request.POST.get('number_of_trees', 0))  # Get number_of_trees from POST
        
        if cutting_records.exists():
            remaining_balance = cutting_records.last().remaining_balance - volume
            calculated_volume = volume  # For subsequent entries, no 30% addition
        else:
            # First entry: add 30% to volume
            calculated_volume = volume + (volume * Decimal('0.30'))
            remaining_balance = calculated_volume
        
        # Create new record with number_of_trees
        new_record = CuttingRecord.objects.create(
            parent_tcp=parent_tcp,
            species=species,
            volume=volume,
            calculated_volume=calculated_volume,
            remaining_balance=remaining_balance,
            remarks=remarks,
            number_of_trees=number_of_trees  # Add number_of_trees to the record
        )
        
        # Store the new record ID in session for highlighting
        request.session['new_record_id'] = new_record.id
        messages.success(request, 'Volume record added successfully!')
        return redirect('add_cutting_record', permit_number=permit_number)
    
    # Get the new_record_id from the session if it exists
    new_record_id = request.session.pop('new_record_id', None)
    
    if cutting_records.exists():
        remaining_balance = cutting_records.last().remaining_balance
        is_first_entry = False
    else:
        remaining_balance = parent_tcp.total_volume_granted
        is_first_entry = True
    
    context = {
        'parent_tcp': parent_tcp,
        'volume_records': cutting_records,
        'remaining_balance': remaining_balance,
        'is_first_entry': is_first_entry,
        'total_volume_granted': parent_tcp.total_volume_granted,
        'new_record_id': new_record_id,
        'formatted_issue_date': parent_tcp.permit_issue_date,
        'formatted_expiry_date': parent_tcp.expiry_date,
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
            return redirect('add_cutting_record', permit_number=record.parent_tcp.permit_number)
    else:
        form = CuttingRecordForm(instance=record)
    
    return render(request, 'edit_cutting_record.html', {
        'form': form,
        'record': record
    })

