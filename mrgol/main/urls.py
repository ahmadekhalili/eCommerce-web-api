from django.urls import path, include
from rest_framework import routers


from . import views

'''            
router = routers.DefaultRouter()
router.register(r'', views.ProductViewSet)
    path('viewset/', include(router.urls), name='product_viewset'),'''

app_name = 'main'

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('index/', views.index, name='index'),
    path('posts/', views.PostList.as_view(), name='posts'),
    path('products/', views.ProductList.as_view(), name='products'),
    path('posts/roots/', views.PostRootList.as_view(), name='post_root_list'),
    path('products/roots/', views.ProductRootList.as_view(), name='product_root_list'),
    path('posts/<menu>/', views.PostList.as_view(), name='post_list'),
    path('products/<menu>/', views.ProductList.as_view(), name='product_list'),
    path('posts/detail/<pk>/<slug>/', views.PostDetail.as_view(), name='post_detail'),   #slug here dont affect class PostDetail for query(only query on pk for retriving posts)    
    path('products/detail/<pk>/<slug>/', views.ProductDetail.as_view(), name='product_detail'),
    path('supporter_datas/<datas_selector>/', views.SupporterDatasSerializer.as_view(), name='support_datas_serialized'),
    path('comments/products/create/', views.ProductCommentCreate.as_view(), name='comments_products_create'),
    path('states/', views.States.as_view(), name='states'),
    path('states/<id>/', views.TownsByState.as_view(), name='towns-by-state'),
]

