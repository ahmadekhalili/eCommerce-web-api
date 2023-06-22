import json

from django.db.models import Sum, F, Case, When, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.utils.translation import gettext_lazy as _
#from django.template.defaultfilters import slugify
from django.utils.text import slugify
from django.middleware.csrf import get_token

from rest_framework import viewsets
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import views

import io
import os
import uuid
import jdatetime
from pathlib import Path
from PIL import Image as PilImage
from math import ceil

from . import myserializers, myforms
from .mymethods import get_products, get_posts, get_posts_products_by_category, make_next, ImageCreation
from .models import *
from users.myserializers import UserSerializer, UserChangeSerializer
from cart.myserializers import CartProductSerializer
from customed_files.states_towns import list_states_towns


def index(request):
    if request.method == 'GET':
        #cache.set('name', ['mkh is my name', 'akh is my name'])
        #str(request.META.get('HTTP_COOKIE'))id=14   fied_1=s2
        #Category._meta.get_field('level').validators[0].limit_value
        #user_language = 'fa'
        #translation.activate(user_language)
        #request.session[translation.LANGUAGE_SESSION_KEY] = user_language
        #Accept-Language

        a = myforms.PostForm(instance=Post.objects.get(id=20))
        from rest_framework.serializers import ModelSerializer, Serializer
        b = Post.objects.get(id=20)

        #formset_factory(myforms.ImageForm)()
        #formset = formset_factory(myforms.CategoryForm, extra=2)
        #posts = f(initial=[{'name': 'asdasd', 'slug':'eqwe', 'level': 1, 'father_category': 26, 'post_product': 'product',}])#inlineformset_factory(Product, Category, fields=('name', 'slug', 'level', 'father_category', 'post_product'))(instance=p)
        rend = render(request, 'main/index.html', {'a': a, 'b': b})
        #rend.set_cookie('cart_products', {'1': {'q': 23, 'p': 33}, '2': {'q': 230, 'p': 330}})
        return rend

    else:
        a = ''
        b = ''
        return render(request, 'main/index.html', {'a': a, 'b': b})




class SupporterDatasSerializer(views.APIView):     #important: you can use class SupporterDatasSerializer in view like: SupporterDatasSerializer().get(request, datas_selector='csrf_products_user') (returned value is Response type, you need .data to convert it as python dict(json)     
    '''
    /supporter_datas/products/ __________
    output = {"cart_products": [...]}__________
    /supporter_datas/favorites/ __________
    output = {"favorite_products": [...]}__________
    /supporter_datas/user/__________
    output = {"user": ...}__________
    /supporter_datas/csrf/__________
    output = {"csrfmiddlewaretoken":"...", "csrftoken": "..."}__________
    /supporter_datas/products_user_csrf/__________
    output = {"cart_products": [...], favorite_products": [...], "user": ..., "csrfmiddlewaretoken":"...", "csrftoken": "..."}
    '''
    def all_datas(self, request, **kwargs):
        datas = {}
        datas_selector = kwargs.get('datas_selector') if kwargs.get('datas_selector') else ''
        if 'favorites' in datas_selector:
            pass
            #datas = {**datas, **{'favorites': Cart(request).get_favorite_products()}}
        if 'user' in datas_selector:                                                    #if datas_selector was None it will raise error in here.
            userserializer = UserSerializer(request.user, context={'request': request}) if request.user.is_authenticated else None
            datas = {'user': userserializer.data} if userserializer else {'user': None}            #calling UserSerializer(request.user).data for unauthenticated user  (anomouse user) will raise error

        if 'csrf' in datas_selector:
            request_csrf_token, csrf_token= get_token(request), get_token(request) if "CSRF_COOKIE" not in request.META else ''
            datas = {**datas, **{'csrfmiddlewaretoken': get_token(request), 'csrftoken': get_token(request)}}

        if 'sessionid' in datas_selector:
            datas = {**datas, 'sessionid': request.session.session_key}
        return datas
    
    def get(self, request, *args, **kwargs):        
        return Response(self.all_datas(request, **kwargs))
    
    def post(self, request, *args, **kwargs):
        return Response(self.all_datas(request, **kwargs))




class HomePage(views.APIView):
    #permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        '''
        output 6 last created product and 4 last created post(visible=True, and select products with available=True in first).
        '''
        products = get_products(0, 6)
        posts = get_posts(0, 4).select_related('category')
        posts = posts if posts else []
        #supporter_datas = supporter_datas_serializer(request, mode='read')
        products_serialized = {'products': myserializers.ProductListSerializer(products, many=True, context={'request': request}).data}       #myserializers.ProductListSerializer(posts, many=True).data  is list not dict so cant use ** before it (like {**serialized})
        posts_serialized = {'posts': myserializers.PostListSerializer(posts, many=True, context={'request': request}).data}
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **products_serialized, **posts_serialized})

    def post(self, request, *args, **kwargs):
        return Response({'loooooooooool': request.session['name']})




class PostMap(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output 12 last created posts(visible=True)
        '''
        posts = Post.objects.values('id', 'slug')
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, 'posts': list(posts)})




class ProductList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output shown 24 last created product and 4 last created post(visible=True, and select products with available=True in first).
        '''
        category_slug = kwargs.get('category')
        if category_slug:
            ## 1- category. url example:  /products/category=sumsung (or  /products/?category=sumsung dont differrent) just dont put '/' in end of url!!!!
            category = get_object_or_404(Category, slug=category_slug)
            products = get_posts_products_by_category(category)
            category_and_allitschiles = Category.objects.filter(id__in=list(filter(None, category.all_childes_id.split(',')))+[category.id])   #why we used filter? category.all_childes_id.split(',') may return: [''] that raise error in statements like  filter(in__in=['']) so we ez remove blank str of list by filter.
            sidebarcategory_checkbox = category_and_allitschiles.filter(level__in=[category.level, category.level+1]) if category.levels_afterthis == 1 else None
            sidebarcategory_link = category_and_allitschiles.filter(level__in=[category.level, category.level+1]) if category.levels_afterthis > 1 else None
            category_ids = category_and_allitschiles.values_list('id', flat=True)
            brands_serialized = myserializers.BrandSerializer(Brand.objects.filter(category__in=category_ids), many=True).data
            filters_serialized = myserializers.FilterSerializer(Filter.objects.filter(category__in=category_ids).prefetch_related('filter_attributes'), many=True).data       # in FilterSerializer has field 'filter_attributes' so if we dont put this prefetch, program will run 1+len(filters) queries (for example supose we have this filters:  <object(1) Filter>, <object(2) Filter> queries number was run for serializing filters: our program run one query for this two object and second for: <object(1) Filter>.filter_attributes.all() and third for <object(2) Filter>.filter_attributes.all() so run 3 query for this 2 filter object! but now just run 2 for eny filter objects.

        else:                                      #none category.   url example:  /products/
            products = Product.objects.filter()
            sidebarcategory_checkbox = None
            sidebarcategory_link = Category.objects.filter(level=1)
            brands_serialized = myserializers.BrandSerializer(Brand.objects.all(), many=True).data
            filters_serialized = myserializers.FilterSerializer(Filter.objects.all().prefetch_related('filter_attributes'), many=True).data

        ## 2 sidebar filter.   url example: /products?zard=1/      filter_attributeslug_id_list is like: [{'meshki': '1'}, {'sefid': '2'}, ..]. why we choiced  slug+id?  answer: slug must be unique and with slug+id it is unique. so front must add id to every slug before sending like: filter_attribute.slug+filter_attribute.id
        filter_attributeslug_id_list = [{filter_attribute['slug']+str(filter_attribute['id']): str(filter_attribute['id'])} for filter in filters_serialized for filter_attribute in filter['filter_attributes']]
        selected_filter_attributes_ids = [int(request.GET[key]) for key in request.GET if {key: request.GET[key]} in filter_attributeslug_id_list]
        if selected_filter_attributes_ids:
            products = products.filter(Q(filter_attributes__in=selected_filter_attributes_ids) | Q(shopfilteritems__filter_attribute__in=selected_filter_attributes_ids))
        if request.GET.get('mx'):                                                                         #sidebar filder price
            products = products.filter(price__gte=request.GET.get('mn'), price__lte=request.GET.get('mx'))           #request.GET.get('mn') and request.GET.get('mx') can be int or str dont raise eny problem.

        ## 3 sort, url example:  /products/کالای-دیجیتال/?sort=bestselling
        sort, orders = request.GET.get('sort'), None
        if sort:
            orders = ['-price'] if sort == 'expensivest' else ['price'] if sort == 'cheapest' else ['-ordered_quantity'] if sort == 'bestselling' else ['-id'] if sort == 'newest' else None
            products = products.annotate(ordered_quantity=Coalesce(Sum(Case(When(order_items__order__paid=True, then=F('order_items__quantity')))), 0)) if 'bestselling' in sort else products    #Coalesce duty? answer: when Sum has not resualt, return None(and it makes raise problem in ordering), now return 0 instead None if dont find eny quantity for specefic product.

        products = get_products(0, 24, products, orders)                                         #note(just for remembering): in nested order_by like: products.order_by('-ordered_quantity').order_by('-available')   ordering start from last order_by here: -available but in one order_by start from first element like:  products..order_by('-available', '-id')  ordering start from "-available" 
        products_serialized = {'products': myserializers.ProductListSerializer(products, many=True, context={'request': request}).data}
        sidebarcategory_checkbox_serialized = myserializers.CategoryChainedSerializer(sidebarcategory_checkbox, many=True).data
        sidebarcategory_link_serialized = myserializers.CategoryChainedSerializer(sidebarcategory_link, many=True).data
        sessionid = request.session.session_key
        
        return Response({'sessionid': sessionid, **products_serialized, **{'sidebarcategory_checkbox': sidebarcategory_checkbox_serialized}, **{'sidebarcategory_link': sidebarcategory_link_serialized}, 'brands': brands_serialized, 'filters': filters_serialized})




class PostList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output 12 last created posts(visible=True)
        '''
        category_slug = kwargs.get('category')
        page = int(kwargs.get('page', 1))
        step = 6               # 6 means you will see 6 post in every page, used in page_count in rang
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            posts = get_posts_products_by_category(category)
            sessionid = request.session.session_key
            serializers = {'posts': myserializers.PostListSerializer(posts, many=True, context={'request': request}).data}             #you must put context={'request': request} in PostListSerializer argument for working request.build_absolute_uri  in PostListSerializer, otherwise request will be None in PostListSerializer and raise error
            return Response({'sessionid': sessionid, **serializers})
        rang = (page * step - step, page * step)
        posts = get_posts(*rang).select_related('category')
        serializers = {'posts': myserializers.PostListSerializer(posts, many=True, context={'request': request}).data}             #you must put context={'request': request} in PostListSerializer argument for working request.build_absolute_uri  in PostListSerializer, otherwise request will be None in PostListSerializer and raise error
        sessionid = request.session.session_key
        page_count = ceil(Post.objects.count() / step)        # round up number, like: ceil(2.2)==3 ceil(3)==3
        return Response({'sessionid': sessionid, **serializers, 'pages': page_count})

    def post(self, request, *args, **kwargs):
        form = myforms.PostForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            instance = form.save()
            return Response(myserializers.PostDetailSerializer(instance, context={'request': request}).data)
        return Response(form.errors)
'''
output is same like ProductList(views.APIView) but can work without context={'request': request} initializing in serializer(ListAPIView put request auto).
class ProductList(generics.ListAPIView):
    queryset = Product.objects.filter(id__lt=100).select_related('rating')
    serializer_class = myserializers.ProductListSerializer
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True).data      
        return Response(serializer)
'''




class PostDetail(views.APIView):
    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': myserializers.PostDetailSerializer(product_categories).data} because myserializers.PostDetailSerializer(product_categories).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        '''
        input receive from /posts/ like posts0.url = "3/یسشی/"__________
        output a post depend on pk you specify.
        '''
        #permission_classes = [IsAuthenticated]
        post = Post.objects.filter(id=kwargs['pk']).select_related('author', 'category').prefetch_related('comment_set')
        serializer = myserializers.PostDetailSerializer(post, many=True).data
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializer[0]})               #serializer is list (because of many=True)    serializer[0] is dict

    def post(self, request, *args, **kwargs):               # you have to submit data by form not json.
        post = get_object_or_404(Post, id=kwargs['pk'])
        form = myforms.PostForm(request.POST, request.FILES, instance=post, request=request)
        if form.is_valid():
            instance = form.save()
            return Response(myserializers.PostDetailSerializer(instance, context={'request': request}).data)
        return Response(form.errors)





class ProductDetail(views.APIView):
    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': myserializers.PostDetailSerializer(product_categories).data} because myserializers.PostDetailSerializer(product_categories).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        '''
        input receive from /products/ like products0.url = "1/گل-زر/"__________
        output a product depend on pk you specify.
        '''
        select_related_father_category = 'category'
        for i in range(Category._meta.get_field('level').validators[1].limit_value-1):
            select_related_father_category += '__father_category'
        product = Product.objects.filter(id=kwargs['pk']).select_related(select_related_father_category, 'brand', 'rating').prefetch_related('comment_set', 'image_set')
        for p in product:                                                         #using like product[0].comment_set revalute and use extra queries
            if request.user.is_authenticated:
                comment_of_user = p.comment_set.filter(author=request.user, product=p)        #this line dont affect select_related and prefetch_related on product and they steal work perfect.                           
                comment_of_user_serialized = myserializers.CommentSerializer(comment_of_user, many=True).data
                comment_of_user_serialized = comment_of_user_serialized[0] if comment_of_user_serialized else {}  #comment_of_user_serialized is list and need removing list but if comment was blank so comment_of_user_serialized == [] and [][0] will raise error.
            else:
                comment_of_user_serialized = {}
            comments = p.comment_set.all()
        comments_serialized = myserializers.CommentSerializer(comments, many=True).data
        product_serializer = myserializers.ProductDetailSerializer(product, many=True, context={'request': request}).data    #product is query set so we need pu like product[0] or put product with many=True (product[0] make revaluate
        product_serializer = product_serializer[0] if product_serializer else {}
        sessionid = request.session.session_key
        
        return Response({**product_serializer, 'comment_of_user': comment_of_user_serialized, 'comments': comments_serialized})




class PostCategoryList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output all posts categories objects.
        '''
        post_categories = Category.objects.filter(post_product='post', level=1)
        serializers = {'post_categories': myserializers.CategoryListSerializer(post_categories, many=True).data}
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializers})




class ProductCategoryList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output all Products categories objects.
        '''
        prefetch_query = 'child_categories'
        for i in range(Category._meta.get_field('level').validators[1].limit_value-2):
            prefetch_query += '__child_categories'
        product_prant_categories = Category.objects.filter(post_product='product', level=1).prefetch_related(prefetch_query)
        serializers = {'product_categories': myserializers.CategoryListSerializer(product_prant_categories, many=True).data}
        #sessionid = request.session.session_key
        return Response({'sessionid': '', **serializers})
'''
generics.RetrieveAPIView
queryset = Post_Category.objects.all()
serializer_class = myserializers.PostListSerializer
def retrieve(self, request, *args, **kwargs):
    instance = self.get_object()
    serializer = myserializers.PostListSerializer(instance.post_set.all(), many=True, context={'request': request})
    return Response(serializer.data)


class PostCategoryDetail(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': myserializers.PostDetailSerializer(product_categories).data} because myserializers.PostDetailSerializer(product_categories).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        #input: receive from  /posts/categories/  like product_categories0.url = "/1/زینتی/"__________
        #output: Category is choicen depend on pk you specify and next depend on post or product category, will be shown all products or posts related to category and category's children. {"sessionid": "...", "products": [...]} 
        category = Category.objects.get(id=kwargs['pk'])
        serializers = {'posts': myserializers.PostListSerializer(get_posts_products_by_category(category), many=True, context={'request': request}).data}            
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializers})

    
class ProductCategoryDetail(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': myserializers.PostDetailSerializer(product_categories).data} because myserializers.PostDetailSerializer(product_categories).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        #input: receive from /products/categories/   like product_categories0.url = "/1/زینتی/"__________
        #output: Category is choicen depend on pk you specify and next depend on post or product category, will be shown all products or posts related to category and category's children. {"sessionid": "...", "products": [...]}
        category = Category.objects.get(id=kwargs['pk'])
        serializers = {'products': myserializers.ProductListSerializer(get_posts_products_by_category(category), many=True, context={'request': request}).data}
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializers})
'''
class PostCommentCreate(views.APIView):
    def post(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        if Post.objects.filter(id=pk).exists():
            try:
                data = request.data
                user = None if not request.user.is_authenticated else request.user
                comment = Comment.objects.create(name=data.get('name', ''), email=data.get('email', ''), content=data['content'], author=user, post_id=pk)
                return Response({'status': 'نظر شما با موفقيت ثبت شد.'})
            except:
                return Response({'status': 'اطلاعات جهت ثبت نظر کافي نيست.'}, status=400)
        else:
            return Response({'user': request.user}, status=401)




class ProductCommentCreate(views.APIView):
    def post(self, request, *args, **kwargs):                
        if request.user.is_authenticated:
            try:
                data = request.data
                comment = Comment.objects.create(content=data['content'], author=request.user, product_id=data['product_id'])
                return Response({'status': 'نظر شما با موفقيت ثبت شد.'})
            except:
                return Response({'status': 'اطلاعات جهت ثبت نظر کافي نيست.'}, status=400)
        else:
            return Response({'user': request.user}, status=401)




class States(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response(myserializers.StateSerializer(State.objects.all(), many=True).data)#Response([L[0] for L in list_states_towns])

           
class TownsByState(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response(myserializers.TownSerializer(State.objects.get(key=kwargs.get('key')).towns.all() , many=True).data)
    '''
        for L in list_states_towns:
            if L[0][0] == kwargs.get('id'):
                return Response(L[1])
    '''

class UploadImage(views.APIView):
    #permission_classes = [IsAdminUser]
    def post(self, request, *args, **kwargs):
        # request.data['file'] sended by front is InMemoryUploadedFile object, like data sended by <input type="file"..>
        obj = ImageCreation(data=None, files=request.data, sizes=[240, 420, 640, 720, 960, 1280, 'default'])
        return Response(obj.create_images(path='/media/posts_images/')[0])
