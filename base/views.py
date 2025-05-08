from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from base.forms import LoginForm, LumberForm, CuttingForm, ChainsawForm, WoodForm, CuttingRecordForm, VolumeRecordForm
from base.models import Lumber, Cutting, Chainsaw, Wood, CuttingRecord, CuttingPermit, VolumeRecord, WoodProcessingPlant, TreeSpecies
from datetime import datetime, timedelta, date
from django.utils import timezone
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from decimal import Decimal
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django import template
from django.views.decorators.http import require_POST
from django.db import transaction
import json

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
            return redirect('homepage')
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
        Q(permit_type__in=['TCP', 'PLTP', 'SPLTP'], expiry_date__gte=current_date) |
        Q(permit_type='STCP', situation='Good')
    ).count()
    
    # Calculate pending cutting permits (only for STCP with no volume records)
    pending_cutting_count = Cutting.objects.filter(
        permit_type='STCP',
        situation='Pending'
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

    # Update the total trees calculation to use VolumeRecord
    total_trees = VolumeRecord.objects.aggregate(
        total=Sum('number_of_trees')
    )['total'] or 0

    # Calculate unique species count from VolumeRecord
    total_species = VolumeRecord.objects.values('species').distinct().count()

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
        'total_trees': total_trees,
        'total_species': total_species,
    }

    return render(request, 'homepage.html', context)

@login_required
def cutting(request):
    if request.method == 'POST':
        form = CuttingForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save the form first to create the cutting record
                cutting = form.save(commit=False)
                
                # Process species data from the form
                species_data = []
                species_names = request.POST.getlist('species_name[]')
                species_quantities = request.POST.getlist('species_quantity_value[]')
                species_volumes = request.POST.getlist('species_volume_value[]')
                
                # Combine the species names, quantities, and volumes
                for name, quantity, volume in zip(species_names, species_quantities, species_volumes):
                    if name and quantity:
                        species_data.append({
                            'species': name,
                            'quantity': int(quantity),
                            'volume': float(volume) if volume else 0
                        })
                
                # Build species string and calculate total trees
                species_list = []
                total_trees = 0
                
                for item in species_data:
                    species_name = item['species']
                    quantity = item['quantity']
                    volume = item.get('volume', 0)
                    
                    if species_name and quantity > 0:
                        species_list.append(f"{species_name} ({quantity})")
                        total_trees += quantity
                
                # Update the cutting record with species info and total trees
                if species_list:
                    cutting.species = ", ".join(species_list)
                cutting.no_of_trees = total_trees
                
                # Save the cutting record with updated fields
                cutting.save()
                
                # Now create the TreeSpecies records
                for item in species_data:
                    species_name = item['species']
                    quantity = item['quantity']
                    volume = item.get('volume', 0)
                    
                    if species_name and quantity > 0:
                        TreeSpecies.objects.create(
                            cutting=cutting,
                            species=species_name,
                            quantity=quantity,
                            volume=volume
                        )
                
                messages.success(request, 'Cutting record created successfully.')
                return redirect('view_cutting', cutting.id)
            except Exception as e:
                messages.error(request, f'Error creating cutting record: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CuttingForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'cutting.html', context)

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
    if request.method == 'POST':
        form = LumberForm(request.POST, request.FILES)
        if form.is_valid():
            lumber = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'message': 'Lumber record added successfully!'})
            messages.success(request, 'Lumber record added successfully!')
            return redirect('lumber_records')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'errors': form.errors
                }, status=400)
            messages.error(request, 'Error adding lumber record. Please check the form.')
    else:
        form = LumberForm()

    context = {
        'form': form,
        'next_number': Lumber.objects.count() + 1  # For auto-incrementing number
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
    cutting = get_object_or_404(Cutting, id=pk)
    
    if request.method == 'POST':
        form = CuttingForm(request.POST, request.FILES, instance=cutting)
        if form.is_valid():
            try:
                cutting = form.save(commit=False)
                
                # Handle contact number formatting if needed
                contact_number = form.cleaned_data.get('contact_number')
                if contact_number:
                    # Ensure it's properly formatted (you can add additional formatting if needed)
                    cutting.contact_number = contact_number.strip()
                
                # Handle payment date
                payment_date = form.cleaned_data.get('payment_date')
                if payment_date:
                    cutting.payment_date = payment_date
                
                # Process species data from the form
                species_data = []
                species_names = request.POST.getlist('species_name[]')
                species_quantities = request.POST.getlist('species_quantity_value[]')
                species_volumes = request.POST.getlist('species_volume_value[]')
                
                # Combine the species names, quantities, and volumes
                for name, quantity, volume in zip(species_names, species_quantities, species_volumes):
                    if name and quantity:
                        species_data.append({
                            'species': name,
                            'quantity': int(quantity),
                            'volume': float(volume) if volume else 0
                        })
                
                # Build species string and calculate total trees
                species_list = []
                total_trees = 0
                
                for item in species_data:
                    species_name = item['species']
                    quantity = item['quantity']
                    volume = item.get('volume', 0)
                    
                    if species_name and quantity > 0:
                        species_list.append(f"{species_name} ({quantity})")
                        total_trees += quantity
                
                # Update the cutting record with species info and total trees
                if species_list:
                    cutting.species = ", ".join(species_list)
                cutting.no_of_trees = total_trees
                
                # Save the cutting record with updated fields
                cutting.save()
                
                # Now create the TreeSpecies records
                for item in species_data:
                    species_name = item['species']
                    quantity = item['quantity']
                    volume = item.get('volume', 0)
                    
                    if species_name and quantity > 0:
                        TreeSpecies.objects.create(
                            cutting=cutting,
                            species=species_name,
                            quantity=quantity,
                            volume=volume
                        )
                
                messages.success(request, 'Cutting record updated successfully.')
                return redirect('view_cutting', cutting.id)
            except Exception as e:
                messages.error(request, f'Error updating cutting record: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CuttingForm(instance=cutting)
    
    context = {
        'form': form,
        'cutting': cutting,
    }
    
    return render(request, 'edit_cutting.html', context)

@login_required
def view_cutting(request, cutting_id):
    try:
        cutting = get_object_or_404(Cutting, id=cutting_id)
        volume_records = VolumeRecord.objects.filter(cutting=cutting).order_by('-date')
        
        context = {
            'cutting': cutting,
            'volume_records': volume_records,
        }
        return render(request, 'view_cutting.html', context)
    except Cutting.DoesNotExist:
        messages.error(request, 'Cutting record not found.')
        return redirect('cutting_records')

@login_required
def add_cutting_record(request, cutting_id):
    cutting = get_object_or_404(Cutting, pk=cutting_id)
    volume_records = VolumeRecord.objects.filter(cutting=cutting).order_by('-date_added')
    
    # Get current remaining balance
    latest_record = volume_records.first()
    current_balance = latest_record.remaining_balance if latest_record else cutting.gross_volume

    if request.method == 'POST':
        try:
            # Check if permit is already consumed
            if current_balance <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Permit is already consumed. No more volume can be added.'
                })

            # Add debug logging
            print("POST data received:", request.POST)
            print("Files received:", request.FILES)
            
            date_str = request.POST.get('date')
            species = request.POST.get('species')
            other_species = request.POST.get('other_species')  # Get other_species value
            volume = request.POST.get('volume')
            number_of_trees = request.POST.get('number_of_trees')
            remarks = request.POST.get('remarks', '')
            calculated_volume = request.POST.get('calculated_volume') or volume
            
            # Handle "Others" species
            if species == 'Others':
                if not other_species:
                    return JsonResponse({
                        'success': False,
                        'message': 'Please specify the species name'
                    })
                species = other_species  # Use the custom species name
            
            # Validate required fields
            if not all([date_str, species, volume, number_of_trees]):
                return JsonResponse({
                    'success': False,
                    'message': 'Please fill in all required fields'
                })
            
            # Convert date string to datetime object
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid date format'
                })
            
            # Convert string values to Decimal for consistent decimal arithmetic
            from decimal import Decimal
            try:
                volume_decimal = Decimal(str(volume))
                calc_volume_decimal = Decimal(str(calculated_volume))
                trees_int = int(number_of_trees)
                
                # For Sawn Lumber, add 40% to the volume
                if species == 'Sawn Lumber':
                    calc_volume_decimal = volume_decimal + (volume_decimal * Decimal('0.40'))
                # For Fuelwood and Teabolts, use volume directly without modification
                elif species in ['Fuel Wood', 'Teabolts']:
                    calc_volume_decimal = volume_decimal
                
                # Ensure current_balance is Decimal
                current_balance = Decimal(str(current_balance))
                
                # Calculate new remaining balance
                new_remaining_balance = (current_balance - calc_volume_decimal).quantize(Decimal('0.01'))
                
                # Create new volume record
                new_record = VolumeRecord.objects.create(
                    cutting=cutting,
                    date=date_obj,
                    species=species,  # This will now be either the selected species or the custom one
                    volume=volume_decimal,
                    calculated_volume=calc_volume_decimal,
                    number_of_trees=trees_int,
                    remarks=remarks,
                    remaining_balance=new_remaining_balance
                )
                
                if 'attachment' in request.FILES:
                    new_record.attachment = request.FILES['attachment']
                    new_record.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Volume record added successfully',
                    'new_record': {
                        'id': new_record.id,
                        'date': new_record.date.strftime('%b %d, %Y'),
                        'species': new_record.species,
                        'number_of_trees': new_record.number_of_trees,
                        'volume': str(new_record.volume),
                        'calculated_volume': str(new_record.calculated_volume),
                        'remaining_balance': str(new_record.remaining_balance),
                        'remarks': new_record.remarks or '-',
                        'attachment': new_record.attachment.url if new_record.attachment else None
                    }
                })
                
            except (ValueError, TypeError) as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid number format: {str(e)}'
                })
            
        except Exception as e:
            print("Error adding record:", str(e))
            return JsonResponse({
                'success': False,
                'message': f'Error adding record: {str(e)}'
            })
    
    context = {
        'cutting': cutting,
        'volume_records': volume_records,
        'latest_record': latest_record,
        'current_balance': current_balance
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
            return redirect('chainsaw_record')
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
                wood.wood_status = request.POST.get('wood_status')
                
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
    status = request.GET.get('status')
    today = timezone.now().date()
    
    # Base queryset
    wood_records = Wood.objects.all()
    
    # Apply filters based on status parameter
    if status == 'active_new':
        wood_records = wood_records.filter(wood_status='ACTIVE (NEW)')
    elif status == 'active_renewed':
        wood_records = wood_records.filter(wood_status='ACTIVE (RENEWED)')
    elif status == 'expired':
        wood_records = wood_records.filter(wood_status='EXPIRED')
    elif status == 'suspended':
        wood_records = wood_records.filter(wood_status='SUSPENDED')
    elif status == 'cancelled':
        wood_records = wood_records.filter(wood_status='CANCELLED')
    elif status == 'expiring_soon':
        expiry_threshold = today + timedelta(days=90)
        wood_records = wood_records.filter(
            expiry_date__gt=today,
            expiry_date__lte=expiry_threshold
        )
    
    context = {
        'wood_records': wood_records,
        'current_status': status,
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
            return redirect('cutting_records')
    else:
        form = CuttingRecordForm(instance=record)
    
    return render(request, 'edit_cutting_record.html', {
        'form': form,
        'record': record
    })

@login_required
def cutting_records(request):
    filter_type = request.GET.get('filter')
    current_date = timezone.now().date()

    # Base queryset with prefetch_related
    base_queryset = Cutting.objects.prefetch_related('volume_records')

    # Apply filters based on request
    if filter_type == 'active_only':
        cuttings = base_queryset.filter(
            Q(permit_type__in=['TCP', 'PLTP', 'SPLTP'], expiry_date__gte=current_date) |
            Q(permit_type='STCP', situation='Good')
        )
    elif filter_type == 'pending_volume':
        cuttings = base_queryset.filter(
            permit_type='STCP',
            situation='Pending'
        )
    else:
        cuttings = base_queryset.all()
    
    # Update remaining balance for each cutting based on latest volume record
    for cutting in cuttings:
        latest_volume = cutting.volume_records.order_by('-date_added').first()
        if latest_volume:
            cutting.remaining_balance = latest_volume.remaining_balance
    
    context = {
        'cuttings': cuttings,
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
    volume_records = VolumeRecord.objects.select_related('cutting').all().order_by(
        'cutting__permit_type', 
        'cutting__permit_number', 
        '-date'
    )
    
    grouped_records = {}
    
    for record in volume_records:
        permit_key = f"{record.cutting.permit_type} {record.cutting.permit_number}"
        
        if permit_key not in grouped_records:
            grouped_records[permit_key] = {
                'permit_type': record.cutting.permit_type,
                'permit_number': record.cutting.permit_number,
                'permittee': record.cutting.permittee,
                'gross_volume': record.cutting.gross_volume,  # Changed from total_volume_granted
                'total_volume_used': 0,
                'remaining_balance': record.cutting.gross_volume,  # Changed from total_volume_granted
                'records': []
            }
        
        grouped_records[permit_key]['records'].append({
            'date': record.date,
            'volume_type': record.volume_type,
            'volume': record.volume,
            'remarks': record.remarks
        })
        
        grouped_records[permit_key]['total_volume_used'] += record.volume
        grouped_records[permit_key]['remaining_balance'] = (
            grouped_records[permit_key]['gross_volume'] -  # Changed from total_volume_granted
            grouped_records[permit_key]['total_volume_used']
        )

    context = {
        'grouped_records': grouped_records,
        'cutting_records': CuttingRecord.objects.all(),
    }
    
    return render(request, 'cutting_volrecords.html', context)

def get_permit_status(cutting, remaining_balance, today):
    # Calculate expiry date (50 days from issue date)
    expiry_date = cutting.date_issued + timedelta(days=50)
    
    if today > expiry_date:
        return "EXPIRED"
    elif remaining_balance <= 0:
        return "CONSUMED"
    elif remaining_balance == cutting.gross_volume:
        return "PENDING"
    else:
        return "ACTIVE"

@login_required
def volume_records_list(request):
    today = date.today()
    cuttings = Cutting.objects.all()
    grouped_records = {}
    
    search_permit = request.GET.get('permit', '').strip()
    search_performed = 'permit' in request.GET
    no_results = False
    
    for cutting in cuttings:
        permit_key = f"{cutting.permit_type}-{cutting.permit_number}"
        if search_permit and search_permit.lower() not in permit_key.lower():
            continue
            
        records = CuttingRecord.objects.filter(parent_tcp=cutting).order_by('-date_added')
        total_volume_used = sum(record.calculated_volume for record in records) if records else 0
        latest_record = records.first()
        remaining_balance = latest_record.remaining_balance if latest_record else cutting.gross_volume  # Changed from total_volume_granted
        
        status = get_permit_status(cutting, remaining_balance, today)
        
        grouped_records[permit_key] = {
            'cutting': cutting,
            'records': records,
            'total_volume_used': total_volume_used,
            'remaining_balance': remaining_balance,
            'status': status
        }
    
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
    elif status == 'expiring_soon':  # Update this filter to match dashboard
        three_months_from_now = current_date + timedelta(days=90)  # Changed from 30 to 90 days
        lumber_records = Lumber.objects.filter(
            expiry_date__gt=current_date,
            expiry_date__lte=three_months_from_now
        ).order_by('-date_issued')
    else:
        lumber_records = Lumber.objects.all().order_by('-date_issued')
    
    # Count expired records
    expired_count = Lumber.objects.filter(expiry_date__lt=current_date).count()
    
    # Count records expiring in next 90 days but not expired yet
    three_months_from_now = current_date + timedelta(days=90)  # Changed from 30 to 90 days
    expiring_soon_count = Lumber.objects.filter(
        expiry_date__gt=current_date,
        expiry_date__lte=three_months_from_now
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
        # For chainsaws expiring within 3 months but not expired
        three_months_from_now = current_date + timedelta(days=90)  # 90 days = 3 months
        chainsaw_records = Chainsaw.objects.filter(
            expiry_date__gt=current_date,  # Not expired yet
            expiry_date__lte=three_months_from_now  # Will expire within 3 months
        ).order_by('-date_issued')
    else:
        # Default: show all records
        chainsaw_records = Chainsaw.objects.all().order_by('-date_issued')
    
    # Count expired records
    expired_count = Chainsaw.objects.filter(
        expiry_date__lt=current_date
    ).count()
    
    # Count records expiring in next 3 months but not expired yet
    three_months_from_now = current_date + timedelta(days=90)
    expiring_soon_count = Chainsaw.objects.filter(
        expiry_date__gt=current_date,
        expiry_date__lte=three_months_from_now
    ).count()
    
    context = {
        'chainsaw_records': chainsaw_records,
        'current_date': current_date,
        'status': status,
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
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

@login_required
def calculate_volumes(request):
    if request.method == 'GET':
        try:
            # Convert input to Decimal and use Decimal for calculations
            total_volume = Decimal(str(request.GET.get('total_volume', '0')))
            gross_volume = total_volume  # Gross volume equals total volume
            net_volume = total_volume * Decimal('0.70')  # Net volume is 70% of total volume
            
            return JsonResponse({
                'success': True,
                'gross_volume': '{:.2f}'.format(float(gross_volume)),
                'net_volume': '{:.2f}'.format(float(net_volume))
            })
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    return JsonResponse({'success': False}, status=405)

@require_POST
@login_required
def edit_volume_record(request, record_id):
    try:
        record = VolumeRecord.objects.get(id=record_id)
        
        # Update record fields
        record.species = request.POST.get('species')
        record.number_of_trees = request.POST.get('number_of_trees')
        record.volume = Decimal(request.POST.get('volume'))
        record.remarks = request.POST.get('remarks')
        
        # Recalculate volumes
        if record.species == 'Sawn Lumber':
            record.calculated_volume = record.volume * Decimal('1.40')
        else:
            record.calculated_volume = record.volume
            
        # Update remaining balance for this and all subsequent records
        records_to_update = VolumeRecord.objects.filter(
            cutting=record.cutting,
            date_added__gte=record.date_added
        ).order_by('date_added')
        
        previous_balance = VolumeRecord.objects.filter(
            cutting=record.cutting,
            date_added__lt=record.date_added
        ).order_by('-date_added').first()
        
        current_balance = previous_balance.remaining_balance if previous_balance else record.cutting.gross_volume
        
        for rec in records_to_update:
            current_balance = current_balance - rec.calculated_volume
            rec.remaining_balance = current_balance
            rec.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def trees(request):
    # Get all cutting records
    cutting_records = Cutting.objects.all()
    
    # Calculate totals
    total_trees = sum(record.no_of_trees for record in cutting_records)
    
    # Calculate unique species
    unique_species = set()
    for record in cutting_records:
        # Split the species string and extract species names
        if record.species:
            species_items = record.species.split(',')
            for item in species_items:
                if '(' in item and ')' in item:
                    species_name = item[:item.rfind('(')].strip()
                    unique_species.add(species_name)
    
    # Process species data for each record
    for record in cutting_records:
        record.species_list = []
        if record.species:
            species_items = record.species.split(',')
            for item in species_items:
                item = item.strip()
                if '(' in item and ')' in item:
                    name = item[:item.rfind('(')].strip()
                    quantity = item[item.rfind('(')+1:item.rfind(')')].strip()
                    record.species_list.append({
                        'name': name,
                        'quantity': quantity
                    })
    
    context = {
        'cutting_records': cutting_records,
        'total_trees': total_trees,
        'total_species': len(unique_species),
    }
    
    return render(request, 'trees.html', context)

@login_required
def trees_view(request):
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Start with all records
    volume_records = VolumeRecord.objects.select_related('cutting')
    cutting_records = Cutting.objects.all()
    
    # Apply search if provided
    if search_query:
        volume_records = volume_records.filter(
            Q(cutting__permit_number__icontains=search_query) |
            Q(cutting__permit_type__icontains=search_query) |
            Q(species__icontains=search_query)
        )
        cutting_records = cutting_records.filter(
            Q(permit_number__icontains=search_query) |
            Q(permit_type__icontains=search_query) |
            Q(species__icontains=search_query)
        )
    
    # Calculate total trees from volume records
    volume_trees = volume_records.aggregate(
        total=Sum('number_of_trees')
    )['total'] or 0
    
    # Calculate total trees from initial permits (where no volume records exist)
    permit_trees = cutting_records.aggregate(
        total=Sum('no_of_trees')
    )['total'] or 0
    
    # Total trees is the sum of both
    total_trees = volume_trees + permit_trees
    
    # Calculate unique species from both sources
    species_set = set()
    
    # Get species from volume records
    for species in volume_records.values_list('species', flat=True).distinct():
        if species:
            species_set.add(species.strip())
    
    # Get species from cutting permits
    for cutting in cutting_records:
        if cutting.species:
            species_entries = cutting.species.split(',')
            for entry in species_entries:
                species_name = entry.strip().split('(')[0].strip()
                species_set.add(species_name)
    
    total_species = len(species_set)
    
    # Calculate total volume from volume records
    total_volume = volume_records.aggregate(
        total=Sum('calculated_volume')
    )['total'] or 0
    
    if total_volume:
        total_volume = Decimal(str(total_volume)).quantize(Decimal('0.01'))
    
    # Group records by permit
    permit_records = {}
    
    # Add volume records
    for record in volume_records:
        permit_key = record.cutting
        if permit_key not in permit_records:
            permit_records[permit_key] = {
                'permit_type': record.cutting.permit_type,
                'permit_number': record.cutting.permit_number,
                'species': [],
                'total_trees': 0,
                'total_volume': Decimal('0.00')
            }
        
        permit_records[permit_key]['species'].append({
            'name': record.species,
            'trees': record.number_of_trees
        })
        permit_records[permit_key]['total_trees'] += record.number_of_trees
        permit_records[permit_key]['total_volume'] += Decimal(str(record.calculated_volume))
    
    # Add permits without volume records
    for cutting in cutting_records:
        if cutting not in permit_records:
            species_list = []
            if cutting.species:
                species_entries = cutting.species.split(',')
                for item in species_entries:
                    if '(' in item and ')' in item:
                        name = item[:item.rfind('(')].strip()
                        qty = item[item.rfind('(')+1:item.rfind(')')].strip()
                        species_list.append({
                            'name': name,
                            'trees': qty
                        })
            
            permit_records[cutting] = {
                'permit_type': cutting.permit_type,
                'permit_number': cutting.permit_number,
                'species': species_list,
                'total_trees': cutting.no_of_trees,
                'total_volume': Decimal('0.00')  # No volume yet
            }
    
    context = {
        'permit_records': permit_records.items(),
        'total_trees': total_trees,
        'total_species': total_species,
        'total_volume': total_volume,
        'search_query': search_query,
    }
    
    return render(request, 'trees.html', context)

def homepage(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'homepage.html')

def treecut_dash(request):
    current_date = timezone.now().date()

    # Basic counts
    cutting_count = Cutting.objects.count()
    
    # Expired permits
    expired_cutting_count = Cutting.objects.filter(
        expiry_date__lt=current_date
    ).count()
    
    # Active cutting permits (not expired)
    active_cutting_count = Cutting.objects.filter(
        Q(permit_type__in=['TCP', 'PLTP', 'SPLTP'], expiry_date__gte=current_date) |
        Q(permit_type='STCP', situation='Good')
    ).count()
    
    # Calculate pending cutting permits (STCP with no volume records)
    pending_cutting_count = Cutting.objects.filter(
        permit_type='STCP',
        situation='Pending'
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

    # Update the total trees calculation to use VolumeRecord
    total_trees = VolumeRecord.objects.aggregate(
        total=Sum('number_of_trees')
    )['total'] or 0

    # Calculate unique species count from VolumeRecord
    total_species = VolumeRecord.objects.values('species').distinct().count()

    # Calculate total trees from volume records
    volume_trees = VolumeRecord.objects.aggregate(
        total=Sum('number_of_trees')
    )['total'] or 0

    # Calculate total trees from initial permits (where no volume records exist)
    permit_trees = Cutting.objects.aggregate(
        total=Sum('no_of_trees')
    )['total'] or 0

    # Total trees is the sum of both
    total_trees = volume_trees + permit_trees

    # Calculate unique species from both sources
    species_set = set()
    
    # Get species from volume records
    for species in VolumeRecord.objects.values_list('species', flat=True).distinct():
        if species:
            species_set.add(species.strip())
    
    # Get species from cutting permits
    for cutting in Cutting.objects.all():
        if cutting.species:
            species_entries = cutting.species.split(',')
            for entry in species_entries:
                species_name = entry.strip().split('(')[0].strip()
                species_set.add(species_name)
    
    total_species = len(species_set)

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
        'total_trees': total_trees,
        'total_species': total_species,
    }

    return render(request, 'treecut-dash.html', context)

def developers(request):
    return render(request, 'developers.html')

def chainsaw_dash(request):
    current_date = timezone.now().date()
    
    # Chainsaw counts
    chainsaw_count = Chainsaw.objects.count()
    
    # For expired chainsaw records
    expired_chainsaw_count = Chainsaw.objects.filter(
        expiry_date__lt=current_date
    ).count()
    
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
        'chainsaw_count': chainsaw_count,
        'expired_chainsaw_count': expired_chainsaw_count,
        'active_chainsaw_count': active_chainsaw_count,
        'expiring_soon_chainsaw_count': expiring_soon_chainsaw_count,
    }
    
    return render(request, 'chainsaw-dash.html', context)

def get_last_chainsaw_number(request):
    try:
        # Get the last chainsaw record
        last_chainsaw = Chainsaw.objects.order_by('-no').first()
        if last_chainsaw:
            # Extract the numeric part and convert to integer
            last_number = int(last_chainsaw.no)
        else:
            last_number = 0
        
        return JsonResponse({'last_number': last_number})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def lumber_dash(request):
    current_date = timezone.now().date()
    
    # Get all lumber records
    lumber_records = Lumber.objects.all()
    
    # Count total records
    total_count = lumber_records.count()
    
    # Count active records (not expired)
    active_count = lumber_records.filter(
        expiry_date__gte=current_date
    ).count()
    
    # Count expired records
    expired_count = lumber_records.filter(
        expiry_date__lt=current_date
    ).count()
    
    # Count records expiring soon (within next 3 months but not expired yet)
    expiring_soon_count = lumber_records.filter(
        expiry_date__gt=current_date,
        expiry_date__lte=current_date + timedelta(days=90)
    ).count()
    
    # Debug print
    print(f"""
DEBUG COUNTS:
Total Records: {total_count}
Active Records: {active_count}
Expiring Soon: {expiring_soon_count}
Expired: {expired_count}
Current Date: {current_date}
    """)
    
    context = {
        'total_count': total_count,
        'active_count': active_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
    }
    
    return render(request, 'lumber-dash.html', context)

@login_required
def lumber_form(request):
    latest_record = Lumber.objects.order_by('-no').first()
    next_number = 1 if not latest_record else latest_record.no + 1
    
    if request.method == 'POST':
        form = LumberForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                lumber = form.save(commit=False)
                lumber.created_by = request.user
                lumber.no = next_number
                lumber.save()
                form.save_m2m()
                messages.success(request, 'Lumber record created successfully!')
                return redirect('lumber_records')
            except Exception as e:
                print(f"Error saving lumber: {str(e)}")
                messages.error(request, f'Error saving record: {str(e)}')
        else:
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                messages.error(request, f"{field}: {', '.join(errors)}")
    else:
        form = LumberForm(initial={'no': next_number})

    context = {
        'form': form,
        'next_number': next_number,
        'lumber_records': Lumber.objects.filter(expiry_warning=True),
        'any_expiring_records': Lumber.objects.filter(expiry_warning=True).exists(),
    }
    return render(request, 'lumber.html', context)

@login_required
def wood_dashboard(request):
    today = timezone.now().date()
    expiry_threshold = today + timedelta(days=90)

    # Get all records
    wood_records = Wood.objects.all()

    # Filter for different statuses - using wood_status instead of status
    active_new_count = wood_records.filter(
        wood_status='ACTIVE (NEW)'
    ).count()

    active_renewed_count = wood_records.filter(
        wood_status='ACTIVE (RENEWED)'
    ).count()

    expired_count = wood_records.filter(
        wood_status='EXPIRED'
    ).count()

    suspended_count = wood_records.filter(
        wood_status='SUSPENDED'
    ).count()

    cancelled_count = wood_records.filter(
        wood_status='CANCELLED'
    ).count()

    # Calculate expiring soon
    expiring_soon_count = wood_records.filter(
        expiry_date__gt=today,
        expiry_date__lte=expiry_threshold
    ).count()

    context = {
        'wood_count': wood_records.count(),
        'expiring_soon_wood_count': expiring_soon_count,
        'active_new_count': active_new_count,
        'active_renewed_count': active_renewed_count,
        'expired_wood_count': expired_count,
        'suspended_count': suspended_count,
        'cancelled_count': cancelled_count,
    }
    
    return render(request, 'wood-dash.html', context)

@login_required
def wood_dash(request):
    current_date = timezone.now().date()
    three_months_from_now = current_date + timedelta(days=90)
    
    # Get all records
    all_records = Wood.objects.all()
    
    # Active records (not expired)
    active_count = all_records.filter(
        expiry_date__gte=current_date,
        wood_status__in=['ACTIVE (NEW)', 'ACTIVE (RENEWED)']
    ).exclude(
        wood_status__in=['EXPIRED', 'SUSPENDED', 'CANCELLED']
    ).count()
    
    # Records to expire within 3 months (but still active)
    expiring_soon_count = all_records.filter(
        expiry_date__gt=current_date,
        expiry_date__lte=three_months_from_now,
        wood_status__in=['ACTIVE (NEW)', 'ACTIVE (RENEWED)']
    ).exclude(
        wood_status__in=['EXPIRED', 'SUSPENDED', 'CANCELLED']
    ).count()
    
    # Expired records
    expired_count = all_records.filter(
        Q(expiry_date__lt=current_date) |
        Q(wood_status='EXPIRED')
    ).count()
    
    # Total records count (all records regardless of status)
    total_count = all_records.count()
    
    # Debug prints
    print(f"Debug - Current date: {current_date}")
    print(f"Debug - Active count: {active_count}")
    print(f"Debug - To Expire count: {expiring_soon_count}")
    print(f"Debug - Expired count: {expired_count}")
    print(f"Debug - Total count: {total_count}")
    
    context = {
        'total_count': total_count,
        'active_count': active_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
    }
    
    return render(request, 'wood-dash.html', context)

@login_required
def get_volume_details(request, cutting_id):
    try:
        cutting = Cutting.objects.get(id=cutting_id)
        volumes = VolumeRecord.objects.filter(cutting=cutting).order_by('date')
        
        volume_data = [{
            'date': volume.date.strftime('%Y-%m-%d'),
            'species': volume.species,
            'volume': str(volume.volume),
            'calculated_volume': str(volume.calculated_volume),
            'remaining_balance': str(volume.remaining_balance),
            'remarks': volume.remarks
        } for volume in volumes]
        
        return JsonResponse({
            'success': True,
            'volumes': volume_data
        })
    except Cutting.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cutting record not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

def get_expiring_chainsaws(request):
    # Calculate date 3 months from now
    three_months_from_now = timezone.now().date() + timedelta(days=90)
    today = timezone.now().date()
    
    # Get chainsaws expiring within the next 3 months
    expiring_chainsaws = Chainsaw.objects.filter(
        expiry_date__gt=today,
        expiry_date__lte=three_months_from_now
    ).values('id', 'owner', 'serial_number', 'expiry_date')
    
    # Convert QuerySet to list and format dates
    chainsaw_list = list(expiring_chainsaws)
    for chainsaw in chainsaw_list:
        chainsaw['expiry_date'] = chainsaw['expiry_date'].isoformat()
    
    return JsonResponse(chainsaw_list, safe=False)


