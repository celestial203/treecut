from django import template
from datetime import datetime
import re

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

@register.filter
def split_species(species_string):
    """
    Parse a species string like "Molave (5), Mahogany (3)" into a list of dictionaries
    with name and quantity keys.
    """
    if not species_string:
        return []
    
    result = []
    # Split by comma and process each species entry
    species_entries = species_string.split(',')
    
    for entry in species_entries:
        entry = entry.strip()
        # Use regex to extract species name and quantity
        match = re.match(r'(.*?)\s*\((\d+)\)', entry)
        if match:
            species_name = match.group(1).strip()
            quantity = match.group(2)
            result.append({'name': species_name, 'quantity': quantity})
    
    return result