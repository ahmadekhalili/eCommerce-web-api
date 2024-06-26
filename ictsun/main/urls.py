from django.urls import path

from . import views
# note1: update sitemap.py if changed here.


app_name = 'main'

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('index/', views.index, name='index'),
    path('posts/', views.PostList.as_view(), name='posts'),
    path('products/', views.ProductList.as_view(), name='products'),
    # 'posts/categories' and 'product/categories' must not put below posts/<page>/... raise error.
    path('posts/categories/', views.PostCategoryList.as_view(), name='post_category_list'),
    path('products/categories/', views.ProductCategoryList.as_view(), name='product_category_list'),
    path('posts/<int:page>/', views.PostList.as_view(), name='posts-page'),
    path('posts/<int:page>/<category>/', views.PostList.as_view(), name='posts-list-cat'),
    path('products/<page>/', views.ProductList.as_view(), name='products-list'),
    path('products/<page>/<category>/', views.ProductList.as_view(), name='products-list-cat'),
    path('post/detail/<pk>/<slug>/', views.PostDetail.as_view(), name='post_detail'),  # mongo pk can't be int
    path('products/detail/<int:pk>/<slug>/', views.ProductDetail.as_view(), name='product_detail'),
    path('supporter_datas/<datas_selector>/', views.SupporterDatasSerializer.as_view(), name='support_datas_serialized'),
    path('comments/', views.CommentList.as_view(), name='comments_list'),
    path('comment/<pk>/', views.CommentDetail.as_view(), name='comment_detail'),  # pk can be int(sql)/str(mongo)
    path('states/', views.States.as_view(), name='states'),
    path('states/<key>/', views.TownsByState.as_view(), name='towns-by-state'),
    path('upload/', views.UploadImage.as_view(), name='upload-image'),
]
