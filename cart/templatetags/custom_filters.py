from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def formatnumber(value, decimal_places=2):
    numero_redondeado = round(value, decimal_places)
    numero_formateado = format(numero_redondeado, ',.2f').replace(',', ';').replace('.', ',').replace(';', '.')
    return numero_formateado.rstrip('0').rstrip(',')
