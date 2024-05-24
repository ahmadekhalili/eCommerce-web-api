from django.db.models import Sum, F, Case, When, Q
from django.db.models.functions import Coalesce
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.middleware.csrf import get_token

from rest_framework.response import Response
from rest_framework import views
from rest_framework import mixins
from rest_framework import generics

import os
import pymongo
import environ
from pathlib import Path
from urllib.parse import quote_plus
from bson import ObjectId

from customed_files.rest_framework.classes.response import ResponseMongo
from . import serializers as my_serializers
from . import forms as my_forms
from .methods import get_products, get_posts, get_posts_products_by_category, ImageCreationSizes, get_parsed_data, \
    get_page_count, get_unique_list, DictToObject
from .models import *
from users.serializers import UserSerializer

env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))
username, password, db_name = quote_plus(env('MONGO_USERNAME')), quote_plus(env('MONGO_USERPASS')), env('MONGO_DBNAME')
host = env('MONGO_HOST')
uri = f"mongodb://{username}:{password}@{host}:27017/{db_name}?authSource={db_name}"
mongo_db = pymongo.MongoClient(uri)['akh_db']

def index(request):
    if request.method == 'GET':
        # cache.set('name', ['mkh is my name', 'akh is my name'])
        # str(request.META.get('HTTP_COOKIE'))id=14   field_1=s2
        a = ''
        #f = my_serializers.CommentSerializer(DictToObject({"content": "dsadasd", 'author': User.objects.get(id=1)}), mongo=True).data

        a = ''
        b = ''

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
        posts = list(get_posts(mongo_db.post, first_index=0, last_index=4))
        # supporter_datas = supporter_datas_serializer(request, mode='read')
        products_serialized = {'products': my_serializers.ProductListSerializer(products, many=True, context={'request': request}).data}       #my_serializers.ProductListSerializer(posts, many=True).data  is list not dict so cant use ** before it (like {**serialized})
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **products_serialized, 'posts': posts})




class PostList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output 12 last created posts(visible=True)
        '''
        category_slug = kwargs.get('category')
        page = kwargs.get('page', 1)
        step = settings.POST_STEP
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            posts = get_posts_products_by_category(category)

        else:
            posts = None

        post_col = mongo_db.post
        posts_count = len(posts) if posts else post_col.count_documents({})     # posts_count type is int
        page_count = get_page_count(posts_count, step)
        rang = (page * step - step, page * step)
        posts = get_posts(post_col, first_index=rang[0], last_index=rang[1]) if not posts else posts[rang[0], rang[1]]
        data = my_serializers.PostListSerializer(DictToObject(posts, many=True), many=True).data
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, 'posts': data, 'pages': page_count})

    def post(self, request, *args, **kwargs):
        serializer = my_serializers.PostMongoSerializer(data=request.data, request=request)
        if serializer.is_valid():
            serializer.save()
            return Response('successfully created in mongo!')
        return Response(serializer.errors)




class ProductList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output shown 24 last created product and 4 last created post(visible=True, and select products with available=True in first).
        '''
        category_slug = kwargs.get('category')
        page = int(kwargs.get('page', 1))
        step = settings.PRODUCT_STEP
        if category_slug:
            ## 1- category. url example:  /products/category=sumsung (or  /products/?category=samsung dont differrent) just dont put '/' in end of url!!!!
            category = get_object_or_404(Category, slug=category_slug)
            products = get_posts_products_by_category(category)
            category_and_allitschiles = list(Category.objects.filter(id__in=list(filter(None, category.all_childes_id.split(',')))+[category.id]).prefetch_related('filters__filter_attributes', 'brands'))
            if category.levels_afterthis == 1:            
                sidebarcategory_checkbox, sidebarcategory_link = [cat for cat in category_and_allitschiles if cat.level == category.level or cat.level == category.level + 1], None
            if category.levels_afterthis > 1:
                sidebarcategory_link, sidebarcategory_checkbox = [cat for cat in category_and_allitschiles if cat.level == category.level or cat.level == category.level + 1], None
            brands = get_unique_list([child for cat in category_and_allitschiles for child in cat.brands.all()])
            filters = get_unique_list([child for cat in category_and_allitschiles for child in cat.filters.all()])
            brands_serialized = my_serializers.BrandSerializer(brands, many=True).data
            filters_serialized = my_serializers.FilterSerializer(filters, many=True).data       # in FilterSerializer has field 'filter_attributes' so if we dont put this prefetch, program will run 1+len(filters) queries (for example supose we have this filters:  <object(1) Filter>, <object(2) Filter> queries number was run for serializing filters: our program run one query for this two object and second for: <object(1) Filter>.filter_attributes.all() and third for <object(2) Filter>.filter_attributes.all() so run 3 query for this 2 filter object! but now just run 2 for eny filter objects.

        else:                                      #none category.   url example:  /products/
            products = Product.objects.filter()
            sidebarcategory_checkbox = None
            sidebarcategory_link = Category.objects.filter(level=1)
            brands_serialized = my_serializers.BrandSerializer(Brand.objects.all(), many=True).data
            filters_serialized = my_serializers.FilterSerializer(Filter.objects.all().prefetch_related('filter_attributes'), many=True).data

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

        page_count = get_page_count(products, step)
        rang = (page * step - step, page * step)
        products = get_products(*rang, products, orders)                                         #note(just for remembering): in nested order_by like: products.order_by('-ordered_quantity').order_by('-available')   ordering start from last order_by here: -available but in one order_by start from first element like:  products..order_by('-available', '-id')  ordering start from "-available"
        products_serialized = {'products': my_serializers.ProductListSerializer(products, many=True, context={'request': request}).data}
        sidebarcategory_checkbox_serialized = my_serializers.CategoryChainedSerializer(sidebarcategory_checkbox, many=True).data
        sidebarcategory_link_serialized = my_serializers.CategoryChainedSerializer(sidebarcategory_link, many=True).data
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **products_serialized, **{'sidebarcategory_checkbox': sidebarcategory_checkbox_serialized}, **{'sidebarcategory_link': sidebarcategory_link_serialized}, 'brands': brands_serialized, 'filters': filters_serialized, 'pages': page_count})

    def post(self, request, *args, **kwargs):
        serializer = my_serializers.ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return Response(my_serializers.ProductDetailSerializer(instance, context={'request': request}).data)
        return Response(serializer.errors)



class PostDetail(views.APIView):
    serializer = my_serializers.PostMongoSerializer
    post_col = mongo_db.post

    def get(self, request, *args, **kwargs):
        '''
        url=/post/<mongo_pk>/<slug>/
        '''
        # permission_classes = [IsAuthenticated]
        # post = Post.objects.filter(id=kwargs['pk']).select_related('author', 'category').prefetch_related('comments')
        # data = my_serializers.PostDetailSerializer(post, many=True).data[0]
        post = self.post_col.find_one({"_id": ObjectId(kwargs['pk'])})
        sessionid = request.session.session_key
        return ResponseMongo({'sessionid': sessionid, **post})

    def put(self, request, *args, **kwargs):
        # for updating, url=/post/<mongo_pk>/<slug>/   data={"title": "some_title"}
        kwargs['update'] = True
        serializer = self.serializer(pk=kwargs['pk'], data=request.data, partial=True, request=request)
        validated_data = serializer.is_valid(raise_exception=True)
        data, sessionid = serializer.save(validated_data=validated_data), request.session.session_key
        return Response({'sessionid': sessionid, **data})

    def delete(self, request, *args, **kwargs):
        post_col = mongo_db.post
        if not settings.DEBUG:  # productions mode
            post_col.update_one({'_id': ObjectId(kwargs['pk'])}, {'$set': {'visible': True}})
        else:
            post_col.delete_one({'_id': ObjectId(kwargs['pk'])})
        return Response({'sessionid': request.session.session_key, 'status': 'deleted successfully!'})


class ProductDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = Product.objects.all()
    serializer_class = my_serializers.ProductDetailMongoSerializer

    def get(self, request, *args, **kwargs):
        select_related_father_category = 'category'
        for i in range(Category._meta.get_field('level').validators[1].limit_value-1):
            select_related_father_category += '__father_category'
        product = Product.objects.filter(id=kwargs['pk']).select_related(select_related_father_category, 'brand', 'rating').prefetch_related('comment_set', 'images')
        for p in product:                                                         #using like product[0].comment_set revalute and use extra queries
            if request.user.is_authenticated:
                comment_of_user = p.comment_set.filter(author=request.user, product=p)        #this line dont affect select_related and prefetch_related on product and they steal work perfect.
                comment_of_user_serialized = my_serializers.CommentSerializer(comment_of_user, many=True).data
                comment_of_user_serialized = comment_of_user_serialized[0] if comment_of_user_serialized else {}  #comment_of_user_serialized is list and need removing list but if comment was blank so comment_of_user_serialized == [] and [][0] will raise error.
            else:
                comment_of_user_serialized = {}
            comments = p.comment_set.all()
        comments_serialized = my_serializers.CommentSerializer(comments, many=True).data
        product_serializer = self.serializer_class(product, many=True, context={'request': request}).data    #product is query set so we need pu like product[0] or put product with many=True (product[0] make revaluate
        product_serializer = product_serializer[0] if product_serializer else {}
        request.session.session_key
        return Response({**product_serializer, 'comment_of_user': comment_of_user_serialized, 'comments': comments_serialized})

    def put(self, request, *args, **kwargs):
        # partial=True is for update product with any field want.
        # partial auto will set to serializer like: serializer(instance, data, partial=kwargs.pop('partial'))
        kwargs['partial'] = request.data.get('partial', True)
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.visible = False
        instance.save()



class PostCategoryList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output all posts categories objects.
        '''
        post_categories = Category.objects.filter(post_product='post', level=1)
        serializers = {'post_categories': my_serializers.CategoryListSerializer(post_categories, many=True).data}
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
        serializers = {'product_categories': my_serializers.CategoryListSerializer(product_prant_categories, many=True).data}
        #sessionid = request.session.session_key
        return Response({'sessionid': '', **serializers})




class CommentCreate(views.APIView):
    serializer = my_serializers.CommentSerializer

    def post(self, request, *args, **kwargs):
        # required data: 'content', 'post' or 'product_id', 'author'|request.user
        # unrequired: 'comment_id' (for add reply), ...
        data = dict(request.data)
        if data.get('post'):       # create comment of post
            post_id = data.pop('post')
            serializer = self.serializer(request=request, data=data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            serialized = self.serializer(DictToObject(validated_data), mongo=True).data  # don't touch 'data' variable
            data = self.serializer().set_id(data)
            if not data.get('comment_id'):        # create comment
                mongo_db.post.update_one({'_id': ObjectId(post_id)}, {'$push': {'comments': serialized}})
            else:                                 # create comment's reply
                mongo_db.post.update_one({'_id': ObjectId(post_id), 'comments._id': ObjectId(data['comment_id'])},
                                         {'$push': {'comments.$.replies': serialized}})
            return ResponseMongo(serialized)
        return Response({})



class States(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response(my_serializers.StateSerializer(State.objects.all(), many=True).data)#Response([L[0] for L in list_states_towns])

           
class TownsByState(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response(my_serializers.TownSerializer(State.objects.get(key=kwargs.get('key')).towns.all() , many=True).data)
    '''
        for L in list_states_towns:
            if L[0][0] == kwargs.get('id'):
                return Response(L[1])
    '''

class UploadImage(views.APIView):
    #permission_classes = [IsAdminUser]
    def post(self, request, *args, **kwargs):
        '''
        here we create different sizes of image has sent inside "request.data['file']" and save them to hard and
        return their urls, and also 'image_id', so front have to send back image_id in saving post or product like:
        {'default': '/media/../..7a0-default.JPEG', 240: '/media/../..7a0-240.JPEG', ..., 'image_id': 1}
        request.data['file'] sent by front is InMemoryUploadedFile object, like data sent by <input type="file"...>
        '''
        sizes = [240, 420, 640, 720, 960, 1280]
        img = Image(image=request.data['file'], alt=ImageCreationSizes.add_size_to_alt('default'), path='posts')
        obj = ImageCreationSizes(data={'image': request.data['file']}, sizes=sizes)
        instances = [ImageSizes(alt=ImageCreationSizes.add_size_to_alt(size), size=size, father=img) for size in sizes]
        instances = obj.update(instances=instances, upload_to='/media/posts_images/')
        img.save()
        ImageSizes.objects.bulk_create(instances)
        paths = {size: instance.image.url for size, instance in zip(sizes, instances)}
        paths['default'], paths['image_id'] = img.image.url, img.id
        return Response(paths)
