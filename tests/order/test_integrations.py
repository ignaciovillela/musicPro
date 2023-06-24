from unittest.mock import patch

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from result import Err, Ok

from order.models import Order
from shop.models import Category, Product

FILE_PATH = 'order.views'
CONSUMER_PATH = 'api_consumer.consumer'


class IntegrationTestViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='fastfood',
            slug='fastfood1',
        )
        self.product = Product.objects.create(
            id=20,
            category=self.category,
            name='testproduct',
            slug='testproduct',
            description='my test product',
            image='static/core/img/logo.png',
            price=30,
        )
        self.session = self.client.session
        self.session[settings.CART_SESSION_ID] = {
            self.product.id: {'quantity': 2, 'price': str(self.product.price)},
        }
        self.session.save()
        self.valid_data = {
            'first_name': 'First',
            'last_name': 'Last',
            'email': 'email@email.com',
            'address': 'address 123',
            'postal_code': '123',
            'city': 'city',
            'currency': 'clp',
        }

    @patch(f'{CONSUMER_PATH}.get_exchange_data')
    def test_set_total_exchange_when_api_is_available(self, exchange_mock):
        exchange_mock.return_value = Ok({'value': 830})

        response = self.client.post(reverse('order:order_create'))
        response_json = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order/create.html')
        self.assertIn('value="830.00"', response_json['page'])

    @patch(f'{CONSUMER_PATH}.get_exchange_data')
    def test_not_raise_error_when_exchange_api_is_not_available(self, exchange_mock):
        error_text = 'A test error'
        exchange_mock.return_value = Err(error_text)

        response = self.client.post(reverse('order:order_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order/create.html')

    @patch(f'{CONSUMER_PATH}.get_exchange_data')
    @patch(f'{FILE_PATH}.tom_bank_create_pay')
    def test_return_pay_url_when_tombank_api_is_available(self, tombank_mock, exchange_mock):
        exchange_mock.return_value = Ok({'value': 830})
        test_url = 'a_test_url'
        tombank_mock.return_value = Ok(test_url)

        response = self.client.post(reverse('order:order_create'), self.valid_data)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertTrue(response_json['ok'])
        self.assertEqual(response_json['url_pago'], test_url)

    @patch(f'{CONSUMER_PATH}.get_exchange_data')
    @patch(f'{FILE_PATH}.tom_bank_create_pay')
    def test_not_raise_when_tombank_api_is_not_available(self, tombank_mock, exchange_mock):
        exchange_mock.return_value = Ok({'value': 830})
        error_text = 'A test error'
        tombank_mock.return_value = Err(error_text)

        response = self.client.post(reverse('order:order_create'), self.valid_data)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertFalse(response_json['ok'])
        self.assertEqual(response_json['msg'], error_text)

    @patch(f'{FILE_PATH}.tom_bank_check_pay')
    def test_set_paid_order_when_tombank_validate_that_is_paid(self, tombank_mock):
        # Status "F" means that the order is paid
        tombank_mock.return_value = Ok({'estado': 'F'})
        order = Order.objects.create(**self.valid_data, value=100)

        response = self.client.get(reverse('order:order_approve', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        # This view returns an empty json
        self.assertEqual(response_json, {})
        order.refresh_from_db()
        self.assertTrue(order.paid)

    @patch(f'{FILE_PATH}.tom_bank_check_pay')
    def test_not_set_paid_order_when_tombank_not_validate_that_is_paid(self, tombank_mock):
        tombank_mock.return_value = Ok({'estado': 'N'})
        order = Order.objects.create(**self.valid_data, value=100)

        response = self.client.get(reverse('order:order_approve', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json, {})
        order.refresh_from_db()
        self.assertFalse(order.paid)
