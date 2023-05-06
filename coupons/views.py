from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import CouponApplyForm
from .models import Coupon


@require_POST
def coupon_apply(request):
    now = timezone.now()
    form = CouponApplyForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['code']
        msg = None
        try:
            coupon = Coupon.objects.get(code__iexact=code,
                                        active=True)
            if now < coupon.valid_from:
                msg = 'Cupón no encontrado'
            if now > coupon.valid_to:
                msg = 'Cupón expirado'
                raise Coupon.DoesNotExist
            request.session['coupon_id'] = coupon.id
        except Coupon.DoesNotExist:
            msg = msg or 'Cupón no encontrado'
            request.session['coupon_id'] = None
        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, 'Cupón aplicado')
    return redirect('cart:cart_detail')


@require_GET
def coupon_remove(request):
    request.session['coupon_id'] = None
    return redirect('cart:cart_detail')
