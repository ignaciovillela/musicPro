from decimal import Decimal
from django.conf import settings
from result import Ok, Result

from api_consumer.consumer import clp_to_usd
from coupons.models import Coupon
from shop.models import Product


class Cart:

    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # store current applied coupon
        self.coupon_id = self.session.get('coupon_id')

    def add(self, product, quantity=1, update_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        """
        mark the session as "modified" to make sure it gets saved
        """
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        product_ids = self.cart.keys()
        # get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def __bool__(self):
        return len(self) != 0

    def get_total_price(self, usd=False) -> Result:
        """
        calculate the total cost of the items in the cart
        """
        value = sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
        if usd:
            result = clp_to_usd(value)
            if result.is_ok():
                return Ok(Decimal(result.ok()))
            return result
        return Ok(value)

    def clear(self):
        """
        remove cart from session
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()

    @property
    def coupon(self):
        if self.coupon_id:
            return Coupon.objects.get(id=self.coupon_id)
        return None

    def get_discount(self, usd=False) -> Result:
        if self.coupon:
            result = self.get_total_price(usd=usd)
            if result.is_ok():
                discount = self.coupon.apply_discount(result.ok())
                if not usd:
                    discount = round(discount)
                return Ok(discount)
            return result
        return Ok(Decimal('0'))

    def get_total_price_after_discount(self, usd=False) -> Result:
        result_total_price = self.get_total_price(usd)
        result_discount = self.get_discount(usd)
        if result_total_price.is_ok() and result_discount.is_ok():
            return Ok(round(result_total_price.ok() - result_discount.ok(), 2))
        return result_total_price
