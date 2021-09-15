from django.urls import path, include


from . import views


urlpatterns = [
    path('', views.CartView.as_view(), name='cart_view'),
    path('add/', views.CartAdd.as_view(), name='cart_add'),
    path('remove/', views.CartRemove.as_view(), name='cart_remove'),
    #path('', views.LogIn.as_view(), name='loginview'),
]

