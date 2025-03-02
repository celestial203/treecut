from django import template
from datetime import date, timedelta

register = template.Library()

@register.filter
def expired_records(records):
    today = date.today()
    return [record for record in records if record.expiry_date < today]

@register.filter
def expiring_records(records):
    today = date.today()
    soon = today + timedelta(days=30)  # Records expiring in the next 30 days
    return [record for record in records if record.expiry_date >= today and record.expiry_date <= soon] 