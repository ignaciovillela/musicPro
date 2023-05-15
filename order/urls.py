from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('created/<int:pk>', views.order_created, name='order_created'),
    path('approve/<int:pk>', views.order_approve, name='order_approve'),
    path('reject/<int:pk>', views.order_reject, name='order_reject'),
]
