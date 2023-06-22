import threading

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render

from api_consumer.consumer import tom_bank_check_pay, tom_bank_create_pay
from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem


def order_create(request):
    cart = Cart(request)
    if not cart:
        return redirect('shop:product_list')
    if request.method == 'POST':
        result_total_after_discount = cart.get_total_price_after_discount()
        result_total_after_discount_usd = cart.get_total_price_after_discount(usd=True)
        total_after_discount = result_total_after_discount.value
        total_after_discount_usd = result_total_after_discount_usd.value
        if result_total_after_discount.is_err():
            return JsonResponse({'ok': False, 'msg': total_after_discount})
        elif result_total_after_discount_usd.is_err():
            total_after_discount_usd = None
        initial = {
            'value': int(total_after_discount),
            'usd_value': total_after_discount_usd,
        }
        data = request.POST.copy()
        data.update(initial)
        form = OrderCreateForm(data, initial=initial)
        if form.is_valid():
            order: Order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])
            result = tom_bank_create_pay(order, request)
            if result.is_ok():
                return JsonResponse({'ok': True, 'url_pago': result.ok()})
            else:
                return JsonResponse({'ok': False, 'msg': result.err()})
        return JsonResponse({
            'ok': False,
            'page': render(request, 'order/create.html', {'cart': cart, 'form': form}).content.decode('utf-8'),
        })
    else:
        result_get_total_price_after_discount = cart.get_total_price_after_discount()
        result_get_total_price_after_discount_usd = cart.get_total_price_after_discount(usd=True)
        total_price_after_discount = result_get_total_price_after_discount.value
        total_price_after_discount_usd = result_get_total_price_after_discount_usd.value
        if result_get_total_price_after_discount_usd.is_err():
            total_price_after_discount_usd = None
        form = OrderCreateForm(initial={
            'value': int(total_price_after_discount),
            'usd_value': total_price_after_discount_usd,
        })
    return render(request, 'order/create.html', {'cart': cart, 'form': form})


def order_created(request, pk):
    cart = Cart(request)
    order = Order.objects.get(pk=pk)
    if order.paid:
        article_detail = '\n'.join([
            f'Producto: {x.product}. Precio unitario: {int(x.price)}. Cantidad: {x.quantity}'
            for x in order.items.all()])
        message = (
            f'Su compra N° {order.id} fue realizada correctamente\n'
            f'El total de la compra fue de {order.value}.\n'
            f'Los artículos comprados fueron\n'
            f'{article_detail}'
        )
        send_mail(
            f'Orden #{order.id}',
            message,
            settings.EMAIL_HOST_USER,
            [order.email],
            fail_silently=True,
        )

        # clear the cart
        cart.clear()
        request.session['coupon_id'] = None
    return render(request, 'order/created.html', {'order': order})


def order_approve(request, pk):
    order = Order.objects.get(pk=pk, paid=False)
    result = tom_bank_check_pay(order)
    if result.is_ok():
        data = result.ok()
        if data['estado'] == 'F':
            order.paid = True
            order.save()
    return JsonResponse({})


def order_reject(request, pk):
    order = Order.objects.get(pk=pk, paid=False)
    return JsonResponse({})
