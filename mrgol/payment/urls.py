from django.urls import path, include

from . import views

app_name = 'payment'

urlpatterns = [
    path('', views.PaymentStart.as_view(), name='payment-start'),
    path('verify/', views.paymentVerify.as_view(), name='payment-verify'),
    path('request/', views.send_request, name='send-request'),    #this two last url is for just testing
    path('vverify/', views.verify, name='vverify'),
]

