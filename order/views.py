from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from cart.cart import Cart
from .models import OrderItem
from .forms import OrderCreateForm


def order_create(request):
    cart = Cart(request)
    if not cart:
        return redirect('shop:product_list')
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, initial={
            'value': cart.get_total_price_after_discount(),
            'usd_value': round(cart.get_total_price_after_discount() / 700, 2),
        })
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])
            article_detail = '\n'.join([f'Producto:{x.product}. Precio unitario: {x.price}. Cantidad: {x.quantity}' for x in order.items.all()])
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
    else:
        form = OrderCreateForm(initial={
            'value': int(cart.get_total_price_after_discount()),
            'usd_value': round(cart.get_total_price_after_discount() / 700, 2),
        })
    return render(request, 'order/create.html', {'cart': cart, 'form': form})
