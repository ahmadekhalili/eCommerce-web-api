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
    path('postsmap/', views.PostMap.as_view(), name='posts-map'),
    path('products/', views.ProductList.as_view(), name='products'),
    path('posts/', views.PostList.as_view(), name='posts'),
    # 'posts/categories' and 'product/categories' must not put below posts/<page>/... raise error.
    path('posts/categories/', views.PostCategoryList.as_view(), name='post_category_list'),
    path('products/categories/', views.ProductCategoryList.as_view(), name='product_category_list'),
    path('posts/<page>/', views.PostList.as_view(), name='posts'),
    path('posts/<page>/<category>/', views.PostList.as_view(), name='post_list'),
    path('products/<category>/', views.ProductList.as_view(), name='product_list'),
    path('posts/detail/<pk>/<slug>/', views.PostDetail.as_view(), name='post_detail'),   #slug here dont affect class PostDetail for query(only query on pk for retriving posts)    
    path('products/detail/<pk>/<slug>/', views.ProductDetail.as_view(), name='product_detail'),
    path('supporter_datas/<datas_selector>/', views.SupporterDatasSerializer.as_view(), name='support_datas_serialized'),
    path('comments/posts/<pk>/create/', views.PostCommentCreate.as_view(), name='comments_posts_create'),
    path('comments/products/create/', views.ProductCommentCreate.as_view(), name='comments_products_create'),
    path('states/', views.States.as_view(), name='states'),
    path('states/<key>/', views.TownsByState.as_view(), name='towns-by-state'),
    path('upload/', views.UploadImage.as_view(), name='upload-image'),
]
