from django import template
from datetime import datetime

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return None

@register.filter
def expiry_status(expiry_date, today):
    """
    Returns the status of a permit based on its expiry date
    """
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
    if isinstance(today, str):
        today = datetime.strptime(today, '%Y-%m-%d').date()
        
    if expiry_date < today:
        return 'Expired'
    else:
        return 'Active'

@register.filter
def sum_volume(records):
    """
    Returns the sum of volumes from volume records
    """
    return sum(record.volume for record in records)