from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Cutting, CuttingRecord, LumberDealer, Lumber
from .forms import CuttingRecordForm  # You'll need to create this form
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.conf import settings

@login_required
def add_cutting_record(request, cutting_id):
    cutting = get_object_or_404(Cutting, id=cutting_id)
    
    # Calculate remaining balance
    def calculate_remaining_balance(cutting):
        total_granted = cutting.total_volume_granted
        total_used = CuttingRecord.objects.filter(parent_tcp=cutting).aggregate(
            total=models.Sum('volume'))['total'] or 0
        return total_granted - total_used
    
    if request.method == 'POST':
        form = CuttingRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.parent_tcp = cutting
            record.save()
            return redirect('cutting_records')
    else:
        form = CuttingRecordForm()
    
    context = {
        'form': form,
        'cutting': cutting,
        'remaining_balance': calculate_remaining_balance(cutting),
        'volume_records': CuttingRecord.objects.filter(parent_tcp=cutting).order_by('-date_added'),
        'is_first_entry': not CuttingRecord.objects.filter(parent_tcp=cutting).exists()
    }
    return render(request, 'base/add_cutting_record.html', context)

@login_required
def lumber_dash(request):
    current_date = timezone.now().date()
    
    # Get all records and immediately print their count
    all_records = Lumber.objects.all()
    print("\nDEBUG: Raw SQL Query:")
    print(all_records.query)
    print(f"\nDEBUG: All Records Count: {all_records.count()}")
    print("DEBUG: First few records:")
    for record in all_records[:5]:
        print(f"ID: {record.id}, Trade Name: {record.trade_name}, Expiry: {record.expiry_date}")
    
    # Active records - records that haven't expired yet
    active_records = all_records.filter(
        expiry_date__gt=current_date
    )
    print(f"\nDEBUG: Active Records Count: {active_records.count()}")
    print("DEBUG: Active Records Query:")
    print(active_records.query)
    
    # Expiring records - will expire within next 3 months
    three_months_from_now = current_date + timedelta(days=90)
    expiring_records = active_records.filter(
        expiry_date__lte=three_months_from_now
    )
    print(f"\nDEBUG: Expiring Records Count: {expiring_records.count()}")
    
    # Expired records - already passed expiry date
    expired_records = all_records.filter(
        expiry_date__lte=current_date
    )
    print(f"\nDEBUG: Expired Records Count: {expired_records.count()}")
    
    # Get counts
    total_count = all_records.count()
    active_count = active_records.count()
    expiring_soon_count = expiring_records.count()
    expired_count = expired_records.count()
    
    print(f"""
DETAILED DEBUG INFO:
Current Date: {current_date}
Three Months From Now: {three_months_from_now}
Database being used: {settings.DATABASES['default']['NAME']}
Model being queried: {Lumber._meta.db_table}
Total Records: {total_count}
Active Records: {active_count}
Expiring Soon: {expiring_soon_count}
Expired: {expired_count}
    """)
    
    context = {
        'total_count': total_count,
        'active_count': active_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
    }
    
    return render(request, 'lumber-dash.html', context) 