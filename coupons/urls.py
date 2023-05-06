from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    path('apply/', views.coupon_apply, name='apply'),
    path('remove/', views.coupon_remove, name='remove'),
]
