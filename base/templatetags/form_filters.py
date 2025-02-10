from django import template
from django.forms.boundfield import BoundField
from datetime import date

register = template.Library()

@register.filter(name='addclass')
def addclass(field, css):
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={"class": css})
    return field

@register.filter(name='format_date')
def format_date(value):
    if hasattr(value, 'as_widget'):
        return value.as_widget(attrs={
            "type": "date",
            "class": "w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        })
    elif isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return value

@register.filter(name='format_decimal')
def format_decimal(value):
    if hasattr(value, 'as_widget'):
        return value.as_widget(attrs={
            "type": "number",
            "step": "0.01",
            "class": "w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        })
    return f"{value:.2f}" if value else ""

@register.filter(name='trim_whitespace')
def trim_whitespace(field):
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={
            "class": "w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        })
    return field 