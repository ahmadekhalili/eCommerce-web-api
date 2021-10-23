from django.urls import path
from . import views

app_name = 'orders'

#best and standar structe of urls names and views name is here (i optaine thats from this liks: https://www.django-rest-framework.org/api-guide/routers/     https://www.django-rest-framework.org/api-guide/generic-views/

urlpatterns = [
    path('', views.ListCreateProfileOrder.as_view(), name='profileorder-list'),
    path('orderitems/', views.ListCreateOrderItem.as_view(), name='orderitem-list'),
    path('<pk>/', views.ProfileOrderDetail.as_view(), name='profileorder-detail'),
    
]
