from django import template

register = template.Library()

@register.filter
def expired_records(wood_records):
    """Filter to return only expired wood records"""
    return [record for record in wood_records if record.is_expired]

@register.filter
def expiring_records(wood_records):
    """Filter to return only wood records that are expiring soon"""
    return [record for record in wood_records if record.is_expiring_soon and not record.is_expired] 