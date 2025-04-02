from django.urls import path
from .views import *

app_name = 'mpesa'

urlpatterns = [
    path("mpesa-payment/", MpesaPaymentView.as_view(), name="mpesa-payment"),
    path("payment-callback/", MpesaCallbackView.as_view(), name="mpesa-callback"),
    path("api-mpesa-payment/", APIMpesaPaymentView.as_view(), name="api-mpesa-payment")
]