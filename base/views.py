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
    cutting_count = Cutting.objects.count()
    lumber_count = Lumber.objects.count()
    chainsaw_count = Chainsaw.objects.count()
    wood_count = Wood.objects.count()

    context = {
        'cutting_count': cutting_count,
        'lumber_count': lumber_count,
        'chainsaw_count': chainsaw_count,
        'wood_count': wood_count,
    }
    return render(request, 'dashboard.html', context)

@login_required
def cutting(request):
    if request.method == 'POST':
        form = CuttingForm(request.POST)
        if form.is_valid():
            permit_date = form.cleaned_data.get('permit_issue_date')
            if permit_date and permit_date > date.today():
                messages.error(request, 'Date issued cannot be in the future')
            else:
                form.save()
                messages.success(request, 'Record added successfully')
                return redirect('cutting')
    else:
        form = CuttingForm()

    # Get all cutting records ordered by created_at
    cuttings = Cutting.objects.all().order_by('-created_at')
    
    context = {
        'form': form,
        'cuttings': cuttings,
        'page_title': 'Cutting Records'
    }
    return render(request, 'cutting.html', context)

@login_required
def wood(request):
    if request.method == 'POST':
        form = WoodForm(request.POST)
        print("Form data:", request.POST)  # Debug print
        if form.is_valid():
            print("Form is valid")  # Debug print
            try:
                wood = form.save()
                messages.success(request, 'Wood record created successfully!')
                return redirect('wood')
            except Exception as e:
                print("Save error:", str(e))  # Debug print
                messages.error(request, f'Error saving record: {str(e)}')
        else:
            print("Form errors:", form.errors)  # Debug print
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WoodForm()
    
    wood_records = Wood.objects.all()
    return render(request, 'wood.html', {'form': form, 'wood_records': wood_records})

#FOR LUMBERRRR #####
@login_required
def lumber(request):
    if request.method == 'POST':
        form = LumberForm(request.POST)
        if form.is_valid():
            lumber = form.save(commit=False)
            lumber.created_by = request.user
            lumber.save()
            messages.success(request, 'Lumber record created successfully!')
            return redirect('lumber')
    else:
        form = LumberForm()
    
    # Get all lumber records
    lumber_records = Lumber.objects.all()
    
    # Calculate the date 3 months from now
    three_months_from_now = timezone.now().date() + timedelta(days=90)
    
    # Add expiry warning flag to records
    has_expiring = False
    for record in lumber_records:
        if record.expiry_date:
            record.expiry_warning = record.expiry_date <= three_months_from_now
            if record.expiry_warning:
                has_expiring = True
    
    context = {
        'form': form,
        'lumber_records': lumber_records,
        'any_expiring_records': has_expiring,
    }
    
    return render(request, 'lumber.html', context)

@login_required
def search(request):
    return render(request, 'search.html')

### FOR CHAINSAW### 
@login_required(login_url='login')
def chainsaw(request):
    if request.method == 'POST':
        form = ChainsawForm(request.POST, request.FILES)
        if form.is_valid():
            chainsaw = form.save(commit=False)
            chainsaw.created_by = request.user
            
            # Handle file upload
            if 'file' in request.FILES:
                file = request.FILES['file']
                # Save the chainsaw first to generate the ID
                chainsaw.save()
                
                # Create the directory if it doesn't exist
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'chainsaw_files')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save the file
                chainsaw.file = file
                chainsaw.save()
                
            messages.success(request, 'Chainsaw registration successfully added!')
            return redirect('chainsaw')
        else:
            messages.error(request, 'Error in form submission. Please check the fields.')
            print(form.errors)
    else:
        form = ChainsawForm()

    chainsaw_records = Chainsaw.objects.all().order_by('-date_acquired')
    
    context = {
        'form': form,
        'chainsaw_records': chainsaw_records,
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
def add_cutting_record(request, tcp_no):
    parent_tcp = get_object_or_404(Cutting, tcp_no=tcp_no)
    cutting_records = CuttingRecord.objects.filter(parent_tcp=parent_tcp).order_by('date_added')
    
    # Get the new_record_id from the session if it exists
    new_record_id = request.session.pop('new_record_id', None)
    
    if cutting_records.exists():
        remaining_balance = cutting_records.last().remaining_balance
        is_first_entry = False
    else:
        remaining_balance = parent_tcp.total_volume_granted
        is_first_entry = True
    
    if request.method == 'POST':
        try:
            species = request.POST.get('species')
            no_of_trees = request.POST.get('no_of_trees')
            volume = Decimal(request.POST.get('volume', '0'))
            remarks = request.POST.get('remarks')

            if is_first_entry:
                calculated_volume = volume + (volume * Decimal('0.30'))
                new_remaining_balance = calculated_volume
            else:
                calculated_volume = volume
                new_remaining_balance = remaining_balance - volume

            if not is_first_entry and new_remaining_balance < 0:
                messages.error(request, 'Cannot add record. Volume exceeds remaining balance.')
                return redirect('add_cutting_record', tcp_no=tcp_no)

            cutting_record = CuttingRecord.objects.create(
                parent_tcp=parent_tcp,
                species=species,
                no_of_trees=no_of_trees,
                volume=volume,
                calculated_volume=calculated_volume,
                remaining_balance=new_remaining_balance,
                remarks=remarks
            )
            
            # Store the new record ID in session
            request.session['new_record_id'] = cutting_record.id
            messages.success(request, f'Record successfully added! New balance: {new_remaining_balance:.2f} cu.m')
            return redirect('add_cutting_record', tcp_no=tcp_no)
            
        except Exception as e:
            messages.error(request, f'Error adding record: {str(e)}')
            return redirect('add_cutting_record', tcp_no=tcp_no)
    
    context = {
        'parent_tcp': parent_tcp,
        'volume_records': cutting_records,
        'remaining_balance': remaining_balance,
        'is_first_entry': is_first_entry,
        'total_volume_granted': parent_tcp.total_volume_granted,
        'new_record_id': new_record_id,  # Pass the new record ID to the template
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

