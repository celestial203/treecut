from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from base.forms import LoginForm, LumberForm, CuttingForm, ChainsawForm, WoodForm, CuttingRecordForm, VolumeRecordForm
from base.models import Lumber, Cutting, Chainsaw, Wood, CuttingRecord, CuttingPermit, VolumeRecord
from datetime import datetime, timedelta, date
from django.utils import timezone
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from decimal import Decimal
from django.http import JsonResponse
from django.urls import reverse
from decimal import Decimal
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django import template

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
    # Calculate active cutting permits (not expired)
    active_cutting_count = Cutting.objects.filter(
        expiry_date__gte=current_date
    ).count()
    
    # Calculate pending cutting permits (no volume records yet)
    # A permit is pending when it has no cutting records
    pending_cutting_count = Cutting.objects.filter(
        cutting_records__isnull=True
    ).count()

    # Lumber Records counts
    lumber_count = Lumber.objects.count()
    
    # For expired lumber records, we need to check if current date is past the expiry date
    expired_lumber_count = Lumber.objects.filter(
        expiry_date__lt=current_date
    ).count()
    
    # For active lumber records, the current date should be before or equal to expiry date
    active_lumber_count = Lumber.objects.filter(
        expiry_date__gte=current_date
    ).count()
    
    # For expiring soon lumber records, use records that expire within the next 30 days
    # but are not yet expired
    thirty_days_from_now = current_date + timedelta(days=30)
    expiring_soon_lumber_count = Lumber.objects.filter(
        expiry_date__gte=current_date,
        expiry_date__lte=thirty_days_from_now
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

    # Add Volume Records count
    volume_count = CuttingRecord.objects.count()
    
    # Calculate total volume from all cutting records
    total_volume = CuttingRecord.objects.aggregate(
        total=Sum('calculated_volume')
    )['total'] or 0
    
    # Convert to Decimal for consistent display
    if not isinstance(total_volume, Decimal):
        total_volume = Decimal(str(total_volume))
    
    # Format to 2 decimal places
    total_volume = total_volume.quantize(Decimal('0.01'))

    # Calculate active chainsaw records (not expired)
    active_chainsaw_count = Chainsaw.objects.filter(
        expiry_date__gte=current_date
    ).count()

    # For chainsaws expiring soon (within 3 months but not expired)
    three_months_from_now = current_date + timedelta(days=90)  # 90 days = ~3 months
    expiring_soon_chainsaw_count = Chainsaw.objects.filter(
        expiry_date__gt=current_date,  # Not expired yet
        expiry_date__lte=three_months_from_now  # But will expire within 3 months
    ).count()

    context = {
        'cutting_count': cutting_count,
        'expired_cutting_count': expired_cutting_count,
        'active_cutting_count': active_cutting_count,
        'pending_cutting_count': pending_cutting_count,
        'lumber_count': lumber_count,
        'expired_lumber_count': expired_lumber_count,
        'active_lumber_count': active_lumber_count,
        'expiring_soon_lumber_count': expiring_soon_lumber_count,
        'chainsaw_count': chainsaw_count,
        'expired_chainsaw_count': expired_chainsaw_count,
        'wood_count': wood_count,
        'expired_wood_count': expired_wood_count,
        'volume_count': volume_count,
        'total_volume': total_volume,  # Add the total volume to the context
        'active_chainsaw_count': active_chainsaw_count,
        'expiring_soon_chainsaw_count': expiring_soon_chainsaw_count,
    }

    return render(request, 'dashboard.html', context)

@login_required
def cutting(request):
    if request.method == 'POST':
        form = CuttingForm(request.POST, request.FILES)
        if form.is_valid():
            cutting = form.save(commit=False)
            
            # Handle species based on permit type
            if cutting.permit_type == 'PLTP':
                species_list = request.POST.getlist('species[]')
                quantities = request.POST.getlist('species_quantity[]')
                
                # Validate species and quantities
                if not species_list or not quantities:
                    messages.error(request, 'At least one species with quantity is required for PLTP')
                    return render(request, 'cutting.html', {'form': form})
                
                # Combine species with their quantities
                species_with_qty = []
                total_trees = 0
                for species, qty in zip(species_list, quantities):
                    if species and qty:
                        try:
                            qty_int = int(qty)
                            if qty_int <= 0:
                                messages.error(request, 'Quantity must be greater than 0')
                                return render(request, 'cutting.html', {'form': form})
                            total_trees += qty_int
                            species_with_qty.append(f"{species} ({qty})")
                        except ValueError:
                            messages.error(request, 'Invalid quantity value')
                            return render(request, 'cutting.html', {'form': form})
                
                cutting.species = ', '.join(species_with_qty)
                cutting.no_of_trees = total_trees
            else:
                # For other permit types, handle single species selection
                species = request.POST.get('species')
                if not species:
                    messages.error(request, 'Species is required')
                    return render(request, 'cutting.html', {'form': form})
                cutting.species = species
            
            # Handle volume calculations
            gross_volume = request.POST.get('gross_volume')
            if gross_volume:
                try:
                    cutting.gross_volume = float(gross_volume)
                    cutting.net_volume = cutting.gross_volume * 0.70
                except ValueError:
                    messages.error(request, 'Invalid gross volume value')
                    return render(request, 'cutting.html', {'form': form})
            
            cutting.save()
            messages.success(request, f'Successfully added cutting record for {cutting.permit_type}-{cutting.permit_number}')
            return redirect('cutting')
    else:
        form = CuttingForm()
    
    return render(request, 'cutting.html', {'form': form})

@login_required
def wood(request):
    if request.method == 'POST':
        # Print all POST data for debugging
        for key, value in request.POST.items():
            print(f"POST data: {key} = {value}")
        
        form = WoodForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:  # Make sure there's a try block before the except
                # Print form data
                print("Form is valid")
                for field in form:
                    print(f"Field {field.name}: {field.value()}")
                
                wood_record = form.save(commit=False)
                
                # Explicitly set supplier_info from POST data
                supplier_info = request.POST.get('supplier_info', '')
                print(f"Setting supplier_info to: {supplier_info}")
                wood_record.supplier_info = supplier_info
                
                # Calculate ALR based on DRC
                if wood_record.drc:
                    wood_record.alr = round(float(wood_record.drc) * 290 * 0.80, 2)
                
                # Set expiry date if not provided
                if wood_record.date_issued and not wood_record.expiry_date:
                    wood_record.expiry_date = wood_record.date_issued + timedelta(days=365*5)
                
                # Save the record to the database
                wood_record.save()
                
                # Verify after save
                saved_record = Wood.objects.get(id=wood_record.id)
                print(f"After save, supplier_info = {saved_record.supplier_info}")
                
                # Handle AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Wood record added successfully!',
                        'redirect': reverse('wood_records')
                    })
                
                # Handle regular form submission
                messages.success(request, 'Wood record added successfully!')
                return redirect('wood_records')
                
            except Exception as e:
                # Print detailed error information
                import traceback
                print(f"Error saving record: {str(e)}")
                print(traceback.format_exc())
                
                # Handle AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'Error: {str(e)}'
                    }, status=500)
                
                # Handle regular form submission
                messages.error(request, f'Error saving record: {str(e)}')
        else:
            # Form is invalid
            print("Form is invalid")
            print(f"Form errors: {form.errors}")
            
            # Handle AJAX request for invalid form
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Form validation failed',
                    'errors': form.errors
                })
            
            messages.error(request, 'Please correct the errors below.')
    else:
        # GET request - display empty form
        form = WoodForm(initial={'date_issued': timezone.now().date()})

    # Render the form
    context = {
        'form': form,
    }
    return render(request, 'wood.html', context)

#FOR LUMBERRRR #####
@login_required
def lumber(request):
    current_date = timezone.now().date()
    
    if request.method == 'POST':
        form = LumberForm(request.POST, request.FILES)
        if form.is_valid():
            lumber_record = form.save(commit=False)
            lumber_record.created_by = request.user
            
            # Debug file upload
            if 'file' in request.FILES:
                print(f"File received: {request.FILES['file'].name}")
                print(f"File size: {request.FILES['file'].size} bytes")
                lumber_record.file = request.FILES['file']
            else:
                print("No file was uploaded")
            
            lumber_record.save()
            messages.success(request, 'Lumber record added successfully!')
            return redirect('lumber')
        else:
            messages.error(request, 'Error adding lumber record. Please check the form.')
            print(f"Form errors: {form.errors}")
    else:
        form = LumberForm()
    
    # Get all lumber records
    lumber_records = Lumber.objects.all()
    
    # Check for any expiring records to show notification
    any_expiring_records = any(record.expiry_warning for record in lumber_records)
    
    # Count expired records
    expired_count = Lumber.objects.filter(expiry_date__lt=current_date).count()
    
    # Count records expiring in next 30 days but not expired yet
    thirty_days_from_now = current_date + timedelta(days=30)
    expiring_soon_count = Lumber.objects.filter(
        expiry_date__gte=current_date,
        expiry_date__lte=thirty_days_from_now
    ).count()

    context = {
        'form': form,
        'lumber_records': lumber_records,
        'any_expiring_records': any_expiring_records,
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
        form = LumberForm(request.POST, request.FILES, instance=lumber)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lumber record updated successfully!')
            return redirect('lumber_records')
    else:
        form = LumberForm(instance=lumber)
    
    return render(request, 'edit_lumber.html', {'form': form, 'lumber': lumber})


#FOR CUTTING ####
@login_required
def edit_cutting(request, pk):
    cutting = get_object_or_404(Cutting, pk=pk)
    if request.method == 'POST':
        form = CuttingForm(request.POST, request.FILES, instance=cutting)
        if form.is_valid():
            cutting = form.save(commit=False)
            
            # Handle species based on permit type
            if cutting.permit_type == 'PLTP':
                species_list = request.POST.getlist('species[]')
                quantities = request.POST.getlist('species_quantity[]')
                
                # Validate species and quantities
                if not species_list or not quantities:
                    messages.error(request, 'At least one species with quantity is required for PLTP')
                    return render(request, 'edit_cutting.html', {'form': form, 'cutting': cutting})
                
                # Combine species with their quantities
                species_with_qty = []
                total_trees = 0
                for species, qty in zip(species_list, quantities):
                    if species and qty:
                        try:
                            qty_int = int(qty)
                            if qty_int <= 0:
                                messages.error(request, 'Quantity must be greater than 0')
                                return render(request, 'edit_cutting.html', {'form': form, 'cutting': cutting})
                            total_trees += qty_int
                            species_with_qty.append(f"{species} ({qty})")
                        except ValueError:
                            messages.error(request, 'Invalid quantity value')
                            return render(request, 'edit_cutting.html', {'form': form, 'cutting': cutting})
                
                cutting.species = ', '.join(species_with_qty)
                cutting.no_of_trees = total_trees
            else:
                # For other permit types, handle single species selection
                species = request.POST.get('species')
                if not species:
                    messages.error(request, 'Species is required')
                    return render(request, 'edit_cutting.html', {'form': form, 'cutting': cutting})
                cutting.species = species
            
            # Handle volume calculations
            gross_volume = request.POST.get('gross_volume')
            if gross_volume:
                try:
                    cutting.gross_volume = float(gross_volume)
                    cutting.net_volume = cutting.gross_volume * 0.70
                except ValueError:
                    messages.error(request, 'Invalid gross volume value')
                    return render(request, 'edit_cutting.html', {'form': form, 'cutting': cutting})
            
            cutting.save()
            messages.success(request, f'Successfully updated cutting record for {cutting.permit_type}-{cutting.permit_number}')
            return redirect('cutting')
    else:
        form = CuttingForm(instance=cutting)
    
    return render(request, 'edit_cutting.html', {'form': form, 'cutting': cutting})

def view_cutting(request, cutting_id):
    cutting = get_object_or_404(Cutting, id=cutting_id)
    # Get all volume records for this cutting
    volume_records = cutting.cutting_records.all().order_by('-date_added')
    
    today = date.today()
    context = {
        'cutting': cutting,
        'volume_records': volume_records,  # Add this to the context
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
            
            # Get the volume and calculate additional 30% if this is the first record
            volume = float(form.cleaned_data['volume'])
            
            # Check if this is the first record
            if not CuttingRecord.objects.filter(parent_tcp=cutting).exists():
                calculated_volume = volume + (volume * 0.30)
            else:
                calculated_volume = volume

            # Get the latest remaining balance or use total_volume_granted if no records exist
            latest_record = CuttingRecord.objects.filter(parent_tcp=cutting).order_by('-date_added').first()
            current_balance = latest_record.remaining_balance if latest_record else cutting.total_volume_granted

            # Ensure current_balance is not None before comparison
            if current_balance is not None:
                # Calculate new remaining balance
                new_balance = float(current_balance) - calculated_volume
                record.remaining_balance = new_balance
            else:
                # If current_balance is None, use total_volume_granted as starting point
                record.remaining_balance = float(cutting.total_volume_granted) - calculated_volume

            record.calculated_volume = calculated_volume
            record.save()
            
            messages.success(request, 'Volume record added successfully.')
            return redirect('view_cutting', cutting_id=cutting.id)
    else:
        form = CuttingRecordForm()

    context = {
        'cutting': cutting,
        'form': form,
        'volume_records': CuttingRecord.objects.filter(parent_tcp=cutting).order_by('date_added')
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
        # Debug: Print all POST data
        print("POST data in edit_wood:")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
            
        form = WoodForm(request.POST, request.FILES, instance=wood)
        if form.is_valid():
            wood_record = form.save(commit=False)
            
            # Debug: Print supplier_info before save
            print(f"supplier_info before save: {wood_record.supplier_info}")
            
            # Explicitly set supplier_info from POST data
            supplier_info = request.POST.get('supplier_info', '')
            print(f"Setting supplier_info to: {supplier_info}")
            wood_record.supplier_info = supplier_info
            
            # Calculate ALR based on DRC
            if wood_record.drc:
                wood_record.alr = round(float(wood_record.drc) * 290 * 0.80, 2)
            
            wood_record.save()
            
            # Debug: Verify after save
            saved_record = Wood.objects.get(id=wood_record.id)
            print(f"After save, supplier_info = {saved_record.supplier_info}")
            
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Wood record updated successfully!',
                    'redirect': reverse('wood_records')
                })
            
            # Handle regular form submission
            messages.success(request, 'Wood record updated successfully!')
            return redirect('wood_records')
        else:
            # Debug: Print form errors
            print(f"Form errors: {form.errors}")
            
            # Handle form validation errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Form validation failed',
                    'errors': form.errors
                })
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WoodForm(instance=wood)
    
    # Get choices for type field
    type_choices = Wood.TYPE_CHOICES if hasattr(Wood, 'TYPE_CHOICES') else []
    
    context = {
        'form': form,
        'wood': wood,
        'type_choices': type_choices,
    }
    
    return render(request, 'edit_wood.html', context)

@login_required
def update_wood(request, pk):
    """
    Process the form submission to update a wood processing plant record.
    """
    wood = get_object_or_404(Wood, pk=pk)
    
    if request.method == 'POST':
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Update wood record fields
                wood.name = request.POST.get('name')
                wood.type = request.POST.get('type')
                wood.wpp_number = request.POST.get('wpp_number')
                wood.integrated = request.POST.get('integrated')
                wood.business = request.POST.get('business')
                wood.plant = request.POST.get('plant')
                wood.drc = request.POST.get('drc')
                wood.alr = request.POST.get('alr')
                wood.longitude = request.POST.get('longitude')
                wood.latitude = request.POST.get('latitude')
                wood.supplier_name = request.POST.get('supplier_name')
                wood.supplier_address = request.POST.get('supplier_address')
                wood.local = request.POST.get('local')
                wood.imported = request.POST.get('imported')
                wood.area = request.POST.get('area')
                wood.approved_by = request.POST.get('approved_by')
                wood.date_issued = request.POST.get('date_issued')
                wood.date_released = request.POST.get('date_released')
                wood.expiry_date = request.POST.get('expiry_date')
                wood.status = request.POST.get('status')
                
                # Handle file upload if a new file is provided
                if 'attachment' in request.FILES:
                    # Delete old file if it exists
                    if wood.attachment:
                        if os.path.isfile(wood.attachment.path):
                            os.remove(wood.attachment.path)
                    
                    wood.attachment = request.FILES['attachment']
                
                # Validate the model
                wood.full_clean()
                
                # Save the updated record
                wood.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Wood processing plant record updated successfully',
                    'redirect': reverse('wood_records')
                })
                
            except ValidationError as e:
                # Return validation errors
                return JsonResponse({
                    'success': False,
                    'message': 'Validation error',
                    'errors': e.message_dict
                }, status=400)
                
            except Exception as e:
                # Return any other errors
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=500)
        
        # Handle regular form submission (non-AJAX)
        else:
            form = WoodForm(request.POST, request.FILES, instance=wood)
            if form.is_valid():
                wood = form.save(commit=False)
                
                # Combine supplier name and address into supplier_info
                supplier_name = request.POST.get('supplier_name', '')
                supplier_address = request.POST.get('supplier_address', '')
                
                if supplier_name or supplier_address:
                    wood.supplier_info = f"{supplier_name}{', ' + supplier_address if supplier_address else ''}"
                
                wood.save()
                messages.success(request, 'Wood processing plant record updated successfully')
                return redirect('wood_records')
            else:
                messages.error(request, 'Please correct the errors below')
    else:
        form = WoodForm(instance=wood)
    
    context = {
        'form': form,
        'wood': wood,
        'title': 'Edit Wood Processing Plant',
    }
    
    return render(request, 'edit_wood.html', context)

@login_required
def wood_records(request):
    # Get status filter from URL
    status = request.GET.get('status')
    
    # Get current date for filtering
    current_date = timezone.now().date()
    thirty_days_from_now = current_date + timedelta(days=30)
    
    # Apply filters based on status
    if status == 'expired':
        wood_records = Wood.objects.filter(expiry_date__lt=current_date).order_by('-date_issued')
    elif status == 'active':
        wood_records = Wood.objects.filter(expiry_date__gte=current_date).order_by('-date_issued')
    elif status == 'expiring_soon':
        wood_records = Wood.objects.filter(
            expiry_date__gte=current_date,
            expiry_date__lte=thirty_days_from_now
        ).order_by('-date_issued')
    else:
        # Default: show all records
        wood_records = Wood.objects.all().order_by('-date_issued')
    
    # Set up pagination
    paginator = Paginator(wood_records, 10)  # Show 10 records per page
    page = request.GET.get('page')
    
    try:
        wood_records = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        wood_records = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        wood_records = paginator.page(paginator.num_pages)
    
    # Count expired and expiring soon records for the filter buttons
    expired_count = Wood.objects.filter(expiry_date__lt=current_date).count()
    active_count = Wood.objects.filter(expiry_date__gte=current_date).count()
    expiring_soon_count = Wood.objects.filter(
        expiry_date__gte=current_date,
        expiry_date__lte=thirty_days_from_now
    ).count()
    
    context = {
        'wood_records': wood_records,
        'expired_count': expired_count,
        'active_count': active_count,
        'expiring_soon_count': expiring_soon_count,
        'current_status': status,  # Pass the current status to highlight the active filter
    }
    
    return render(request, 'wood_record.html', context)

@login_required
def wood_detail(request, pk):
    """
    View for displaying details of a specific wood processing plant
    """
    wood = get_object_or_404(Wood, pk=pk)
    
    # Calculate if the permit is expired or expiring soon
    today = timezone.now().date()
    is_expired = False
    is_expiring_soon = False
    
    if wood.expiry_date:
        days_until_expiry = (wood.expiry_date - today).days
        is_expired = days_until_expiry < 0
        is_expiring_soon = 0 <= days_until_expiry <= 30
    
    context = {
        'wood': wood,
        'is_expired': is_expired,
        'is_expiring_soon': is_expiring_soon,
    }
    
    return render(request, 'view_wood.html', context)

@login_required
def delete_wood(request, pk):
    wood = get_object_or_404(Wood, pk=pk)
    if request.method == 'POST':
        wood.delete()
        messages.success(request, 'Wood record deleted successfully!')
        return redirect('wood_records')
    return render(request, 'wood_confirm_delete.html', {'wood': wood})

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
    status = request.GET.get('status')
    today = date.today()
    
    if status == 'expired':
        # Filter only expired permits
        cuttings = Cutting.objects.filter(expiry_date__lt=today).order_by('-created_at')
    elif status == 'active':
        # Filter only active permits
        cuttings = Cutting.objects.filter(expiry_date__gte=today).order_by('-created_at')
    elif status == 'pending':
        # Filter only pending permits (no cutting records)
        cuttings = Cutting.objects.filter(cutting_records__isnull=True).order_by('-created_at')
    else:
        # Show all permits if no status filter
        cuttings = Cutting.objects.all().order_by('-created_at')
    
    context = {
        'cuttings': cuttings,
        'today': today,
    }
    return render(request, 'CuttingRecord.html', context)

def check_permit_exists(request):
    permit_number = request.GET.get('permit_number')
    permit_type = request.GET.get('permit_type')
    
    exists = Cutting.objects.filter(
        permit_type=permit_type,
        permit_number=permit_number
    ).exists()
    
    return JsonResponse({'exists': exists})

@login_required
def volumes(request):
    # Get all volume records with their related cutting information
    volume_records = VolumeRecord.objects.select_related('cutting').all().order_by(
        'cutting__permit_type', 
        'cutting__permit_number', 
        '-date'
    )
    
    # Group records by permit
    grouped_records = {}
    
    for record in volume_records:
        permit_key = f"{record.cutting.permit_type} {record.cutting.permit_number}"
        
        if permit_key not in grouped_records:
            grouped_records[permit_key] = {
                'permit_type': record.cutting.permit_type,
                'permit_number': record.cutting.permit_number,
                'permittee': record.cutting.permittee,
                'total_volume_granted': record.cutting.total_volume_granted,
                'total_volume_used': 0,
                'remaining_balance': record.cutting.total_volume_granted,
                'records': []
            }
        
        # Add the record to the list
        grouped_records[permit_key]['records'].append({
            'date': record.date,
            'volume_type': record.volume_type,
            'volume': record.volume,
            'remarks': record.remarks
        })
        
        # Update totals
        grouped_records[permit_key]['total_volume_used'] += record.volume
        grouped_records[permit_key]['remaining_balance'] = (
            grouped_records[permit_key]['total_volume_granted'] - 
            grouped_records[permit_key]['total_volume_used']
        )

    # Fetch cutting records to match with volume records
    cutting_records = CuttingRecord.objects.all()

    context = {
        'grouped_records': grouped_records,
        'cutting_records': cutting_records,
    }
    
    return render(request, 'cutting_volrecords.html', context)

def get_permit_status(cutting, remaining_balance, today):
    # Calculate expiry date (50 days from issue date)
    expiry_date = cutting.date_issued + timedelta(days=50)
    
    if today > expiry_date:
        return "EXPIRED"
    elif remaining_balance <= 0:
        return "CONSUMED"
    elif remaining_balance == cutting.total_volume_granted:
        return "PENDING"
    else:
        return "ACTIVE"

@login_required
def volume_records_list(request):
    today = date.today()
    cuttings = Cutting.objects.all()
    grouped_records = {}
    
    # Get search parameter and validate
    search_permit = request.GET.get('permit', '').strip()
    search_performed = 'permit' in request.GET
    no_results = False
    
    for cutting in cuttings:
        # Skip this cutting if it doesn't match the search query
        permit_key = f"{cutting.permit_type}-{cutting.permit_number}"
        if search_permit and search_permit.lower() not in permit_key.lower():
            continue
            
        records = CuttingRecord.objects.filter(parent_tcp=cutting).order_by('-date_added')
        total_volume_used = sum(record.calculated_volume for record in records) if records else 0
        latest_record = records.first()
        remaining_balance = latest_record.remaining_balance if latest_record else cutting.total_volume_granted
        
        status = get_permit_status(cutting, remaining_balance, today)
        
        grouped_records[permit_key] = {
            'cutting': cutting,
            'records': records,
            'total_volume_used': total_volume_used,
            'remaining_balance': remaining_balance,
            'status': status
        }
    
    # Check if search was performed but no results found
    if search_performed and search_permit and not grouped_records:
        no_results = True
    
    context = {
        'grouped_records': grouped_records,
        'today': today,
        'search_permit': search_permit,
        'no_results': no_results,
        'search_performed': search_performed
    }
    
    return render(request, 'volume_records_list.html', context)

@login_required
def lumber_records(request):
    current_date = timezone.now().date()
    
    # Get status filter from URL
    status = request.GET.get('status')
    
    # Apply filters based on status
    if status == 'expired':
        lumber_records = Lumber.objects.filter(expiry_date__lt=current_date).order_by('-date_issued')
    elif status == 'active':
        lumber_records = Lumber.objects.filter(expiry_date__gte=current_date).order_by('-date_issued')
    elif status == 'expiring_soon':  # New filter for expiring soon records
        thirty_days_from_now = current_date + timedelta(days=30)
        lumber_records = Lumber.objects.filter(
            expiry_date__gte=current_date,
            expiry_date__lte=thirty_days_from_now
        ).order_by('-date_issued')
    else:
        lumber_records = Lumber.objects.all().order_by('-date_issued')
    
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
    
    return render(request, 'lumber_records.html', context)

@login_required
def view_lumber_details(request, pk):
    """View detailed information about a specific lumber record."""
    lumber = get_object_or_404(Lumber, pk=pk)
    
    # Calculate days until expiry
    if lumber.expiry_date:
        today = timezone.now().date()
        days_until_expiry = (lumber.expiry_date - today).days
    else:
        days_until_expiry = None
    
    context = {
        'lumber': lumber,
        'days_until_expiry': days_until_expiry,
    }
    
    return render(request, 'view_lumber_details.html', context)

@login_required(login_url='login')
def chainsaw_records(request):
    current_date = timezone.now().date()
    
    # Get status filter from URL if provided
    status = request.GET.get('status')
    
    # Apply filters based on status
    if status == 'expired':
        chainsaw_records = Chainsaw.objects.filter(expiry_date__lt=current_date).order_by('-date_issued')
    elif status == 'active':
        chainsaw_records = Chainsaw.objects.filter(expiry_date__gte=current_date).order_by('-date_issued')
    elif status == 'expiring_soon':
        # For chainsaws expiring soon (within 3 months but not expired)
        three_months_from_now = current_date + timedelta(days=90)  # 90 days = ~3 months
        chainsaw_records = Chainsaw.objects.filter(
            expiry_date__gt=current_date,  # Not expired yet
            expiry_date__lte=three_months_from_now  # But will expire within 3 months
        ).order_by('-date_issued')
        
        # Debug output to check if any records match this filter
        print(f"Current date: {current_date}")
        print(f"Three months from now: {three_months_from_now}")
        print(f"Expiring soon records count: {chainsaw_records.count()}")
        for record in chainsaw_records:
            print(f"Record ID: {record.id}, Expiry date: {record.expiry_date}")
    else:
        # Default: show all records
        chainsaw_records = Chainsaw.objects.all().order_by('-date_issued')
    
    # Make sure we're passing the records to the template
    context = {
        'chainsaw_records': chainsaw_records,
        'current_date': current_date,
        'status': status,  # Pass the current status to highlight the active filter
    }
    
    return render(request, 'chainsaw_record.html', context)

@login_required
def view_chainsaw(request, pk):
    """View detailed information about a specific chainsaw record."""
    chainsaw = get_object_or_404(Chainsaw, pk=pk)
    
    context = {
        'chainsaw': chainsaw,
        'days_remaining': chainsaw.days_remaining,
    }
    
    return render(request, 'view_chainsaw.html', context)

@login_required
def renew_chainsaw(request, pk):
    """Renew a chainsaw registration."""
    chainsaw = get_object_or_404(Chainsaw, pk=pk)
    
    if request.method == 'POST':
        form = ChainsawForm(request.POST, request.FILES, instance=chainsaw)
        if form.is_valid():
            chainsaw = form.save(commit=False)
            # Update renewal date to today
            chainsaw.date_renewal = timezone.now().date()
            # Update registration status
            chainsaw.registration_status = 'RENEWED'
            # Update date issued to today
            chainsaw.date_issued = timezone.now().date()
            # Expiry date will be automatically calculated in the save method
            chainsaw.save()
            messages.success(request, f'Successfully renewed chainsaw registration for {chainsaw.name}')
            return redirect('chainsaw_record')
    else:
        form = ChainsawForm(instance=chainsaw)
    
    context = {
        'form': form,
        'chainsaw': chainsaw,
        'is_renewal': True,
    }
    
    return render(request, 'chainsaw.html', context)

register = template.Library()

@register.filter
def split_species_data(species_string):
    if not species_string:
        return [{'name': '', 'quantity': ''}]
    
    species_list = []
    items = species_string.split(',')
    
    for item in items:
        item = item.strip()
        if '(' in item and ')' in item:
            name = item[:item.rfind('(')].strip()
            quantity = item[item.rfind('(')+1:item.rfind(')')].strip()
            species_list.append({
                'name': name,
                'quantity': quantity
            })
    
    return species_list if species_list else [{'name': '', 'quantity': ''}]