from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Cutting, CuttingRecord
from .forms import CuttingRecordForm  # You'll need to create this form
from django.db import models

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