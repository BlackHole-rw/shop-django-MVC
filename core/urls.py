from django.urls import path
from .views import (
    HomeView,
    ItemDetailView,
    CheckoutView,
    add_to_cart,
    OrderSummaryView,
    remove_from_cart,
    remove_single_from_cart,
    add_single_to_cart,
    PaymentView,
    RefundView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove_single_from_cart/<slug>/', remove_single_from_cart, name='remove_single_from_cart'),
    path('add_single_to_cart/<slug>/', add_single_to_cart, name='add_single_to_cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('refund/', RefundView.as_view(), name='refund')
]