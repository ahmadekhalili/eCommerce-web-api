from django.urls import path, include

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartPageView.as_view(), name='cart_page'),
    path('category/', views.CartCategoryView.as_view(), name='cart_category'),
    path('add/', views.CartAdd.as_view(), name='cart_add'),
    path('minus/', views.CartMinus.as_view(), name='cart_minus'),
    path('remove/', views.CartRemove.as_view(), name='cart_remove'),
    #path('', views.LogIn.as_view(), name='loginview'),
]

