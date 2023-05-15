from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def formatnumber(value, decimal_places=2):
    rounded_value = f'{{:,.{decimal_places}f}}'.format(value)
    formatted_value = rounded_value.replace(',', ';').replace('.', ',').replace(';', '.')
    return formatted_value.rstrip('0').rstrip(',')
