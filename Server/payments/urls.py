# urls.py
from django.urls import path
from .views import (
    PricingPlansView,
    InitiatePaymentView,
    PaymentStatusView,
    MpesaCallbackView,
    UserAccessView,
)

app_name = 'payments'

urlpatterns = [
    # Pricing plans
    path('plans/', PricingPlansView.as_view(), name='pricing-plans'),

    # Initiate payment
    path('initiate/', InitiatePaymentView.as_view(), name='initiate-payment'),

    # Payment status check
    path('status/<uuid:transaction_id>/', PaymentStatusView.as_view(), name='payment-status'),

    # M-Pesa callback (no authentication required)
    path('mpesa/callback/', MpesaCallbackView.as_view(), name='mpesa-callback'),

    # User access and payment history
    path('access/', UserAccessView.as_view(), name='user-access'),
]
