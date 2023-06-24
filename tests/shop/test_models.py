from django.test import TestCase
from django.utils import timezone

from shop.models import Category, Product


class CategoryTest(TestCase):

    @staticmethod
    def create_category(name="test"):
        return Category.objects.create(name=name)

    def test_category_creation(self):
        c = self.create_category()
        self.assertIsInstance(c, Category)
        self.assertEqual(str(c), c.name)


class ProductTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name='fastfood',
            slug='fastfood',
        )

    def create_product(self, name="product", price=20):
        return Product.objects.create(
            category=self.category,
            name=name,
            price=price,
            created=timezone.now(),
            updated=timezone.now(),
        )

    def test_product_creation(self):
        p = self.create_product()
        self.assertIsInstance(p, Product)
        self.assertEqual(str(p), p.name)
