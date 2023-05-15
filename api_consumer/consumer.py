import os

import requests
from django.shortcuts import redirect
from django.urls import reverse

from comun.decoradores import music_ttl_cache
from order.models import Order
from result import Err, Ok, Result


@music_ttl_cache(ttl=600)
def get_exchange_data(value, from_currency, to_currency) -> Result:
    url = os.environ.get('API_USD_URL').format(value=value, from_currency=from_currency, to_currency=to_currency)
    try:
        return Ok(requests.get(url).json())
    except requests.exceptions.ConnectionError:
        return Err('No fue posible conectar con la api de conversión')


def usd_to_clp(value):
    result = get_exchange_data(value, 'usd', 'clp')
    if result.is_ok():
        return Ok(result.ok()['value'])
    return result


def clp_to_usd(value):
    result = get_exchange_data(value, 'clp', 'usd')
    if result.is_ok():
        return Ok(result.ok()['value'])
    return result


def tom_bank_create_pay(order: Order, request):
    value = order.value
    if order.currency == Order.CurrencyExchangeType.USD and order.usd_value:
        value = order.usd_value
    url = os.environ.get('API_TOM_BANK_URL')
    try:
        response = requests.get(url, {
            'monto': value,
            'moneda': order.currency,
            'detalle': 'MusicPro',
            'redireccion_url': request.build_absolute_uri(reverse('order:order_created', args=[order.id])),
            'success_url': request.build_absolute_uri(reverse('order:order_approve', args=[order.id])),
            'error_url': request.build_absolute_uri(reverse('order:order_reject', args=[order.id])),
        })
    except requests.exceptions.ConnectionError:
        return Err('No se pudo realizar la transacción con TomBank')
    if response.status_code == 200:
        data = response.json()
        order.tom_bank_id = data['id']
        order.save()
        return Ok(data['url_pago'])
    else:
        return Err('No se pudo realizar la transacción con TomBank')


_ = {
    "id": "f7c3a9c1-626d-46d4-bf67-d76b50a81a93",
    "monto": "1000",
    "detalle": "music pro",
    "fecha": "07/05/2023",
    "hora": "17:15",
    "estado": "P",
    "estado_display": "Pendiente",
    "success_url": "",
    "error_url": "",
    "redireccion_url": "google.com",
    "url_pago": "http://127.0.0.1:8002/realizar_pago/f7c3a9c1-626d-46d4-bf67-d76b50a81a93/",
    "url_estado": "http://127.0.0.1:8002/api/verificar_pago/?id=f7c3a9c1-626d-46d4-bf67-d76b50a81a93"
}


def tom_bank_check_pay(order: Order):
    url = os.environ.get('API_TOM_BANK_CHECK_PAY_URL')
    try:
        response = requests.get(url, {'id': order.tom_bank_id})
    except requests.exceptions.ConnectionError:
        return Err(None)
    if response.status_code == 200:
        data = response.json()
        return Ok(data)
    return Err(None)
