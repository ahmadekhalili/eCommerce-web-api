
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

from . import serializers as my_serializers
from . import forms as my_forms
from .methods import get_products, get_posts, get_posts_products_by_category, ImageCreationSizes, get_parsed_data, \
    get_page_count, get_unique_list
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
        #cache.set('name', ['mkh is my name', 'akh is my name'])
        #str(request.META.get('HTTP_COOKIE'))id=14   fied_1=s2
        #Category._meta.get_field('level').validators[0].limit_value
        #user_language = 'fa'
        #translation.activate(user_language)
        #request.session[translation.LANGUAGE_SESSION_KEY] = user_language
        #Accept-Language
        a = ''
        b = ''

        #formset_factory(my_forms.ImageForm)()
        #formset = formset_factory(my_forms.CategoryForm, extra=2)
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
        products_serialized = {'products': my_serializers.ProductListSerializer(products, many=True, context={'request': request}).data}       #my_serializers.ProductListSerializer(posts, many=True).data  is list not dict so cant use ** before it (like {**serialized})
        posts_serialized = {'posts': my_serializers.PostListSerializer(posts, many=True, context={'request': request}).data}
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **products_serialized, **posts_serialized})




class PostList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output 12 last created posts(visible=True)
        '''
        category_slug = kwargs.get('category')
        page = int(kwargs.get('page', 1))
        step = settings.POST_STEP
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            posts = get_posts_products_by_category(category)

        else:
            posts = None

        rang = (page * step - step, page * step)
        posts = get_posts(*rang, posts).select_related('category')
        serializers = {'posts': my_serializers.PostListSerializer(posts, many=True, context={'request': request}).data}             #you must put context={'request': request} in PostListSerializer argument for working request.build_absolute_uri  in PostListSerializer, otherwise request will be None in PostListSerializer and raise error
        sessionid = request.session.session_key
        page_count = get_page_count(posts, step)
        return Response({'sessionid': sessionid, **serializers, 'pages': page_count})

    def post(self, request, *args, **kwargs):
        form = my_forms.PostAdminForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            instance = form.save()
            return Response(my_serializers.PostDetailSerializer(instance, context={'request': request}).data)
        return Response(form.errors)




class ProductList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output shown 24 last created product and 4 last created post(visible=True, and select products with available=True in first).
        '''
        category_slug = kwargs.get('category')
        page = int(kwargs.get('page', 1))
        step = settings.PRODUCT_STEP
        if category_slug:
            ## 1- category. url example:  /products/category=sumsung (or  /products/?category=sumsung dont differrent) just dont put '/' in end of url!!!!
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

        rang = (page * step - step, page * step)
        products = get_products(*rang, products, orders)                                         #note(just for remembering): in nested order_by like: products.order_by('-ordered_quantity').order_by('-available')   ordering start from last order_by here: -available but in one order_by start from first element like:  products..order_by('-available', '-id')  ordering start from "-available"
        products_serialized = {'products': my_serializers.ProductListSerializer(products, many=True, context={'request': request}).data}
        sidebarcategory_checkbox_serialized = my_serializers.CategoryChainedSerializer(sidebarcategory_checkbox, many=True).data
        sidebarcategory_link_serialized = my_serializers.CategoryChainedSerializer(sidebarcategory_link, many=True).data
        sessionid = request.session.session_key
        page_count = get_page_count(products, step)
        return Response({'sessionid': sessionid, **products_serialized, **{'sidebarcategory_checkbox': sidebarcategory_checkbox_serialized}, **{'sidebarcategory_link': sidebarcategory_link_serialized}, 'brands': brands_serialized, 'filters': filters_serialized, 'pages': page_count})

    def post(self, request, *args, **kwargs):
        serializer = my_serializers.ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return Response(my_serializers.ProductDetailSerializer(instance, context={'request': request}).data)
        return Response(serializer.errors)



class PostDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                 generics.GenericAPIView):
    queryset = Post.objects.all()
    serializer_class = my_serializers.PostDetailMongoSerializer

    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': my_serializers.PostDetailSerializer(product_categories).data} because my_serializers.PostDetailSerializer(product_categories).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        '''
        input receive from /posts/ like posts0.url = "3/یسشی/"__________
        output a post depend on pk you specify.
        '''
        #permission_classes = [IsAuthenticated]
        #post = Post.objects.filter(id=kwargs['pk']).select_related('author', 'category').prefetch_related('comment_set')
        #data = my_serializers.PostDetailSerializer(post, many=True).data[0]
        post_col = mongo_db[settings.MONGO_POST_COL]
        data = post_col.find_one({"id": kwargs['pk']})['json']       # kwargs['pk'] must be int
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **data})               #serializer is list (because of many=True)    serializer[0] is dict

    def put(self, request, *args, **kwargs):
        # partial auto will set to serializer like: serializer(instance, data, partial=kwargs.pop('partial'))
        kwargs['partial'] = request.data.get('partial', True)
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.visible = False
        instance.save()




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
    def post(self, request, *args, **kwargs):
        # request variables in request.data is: content, post_id or product_id
        try:
            data, user = dict(request.data), None if not request.user.is_authenticated else request.user
            comment = Comment.objects.create(**data, author=user)
            if comment.post_id:
                mongo_db_name = settings.MONGO_POST_COL
                foreignkey = comment.post_id
            else:
                mongo_db_name = settings.MONGO_PRODUCT_COL
                foreignkey = comment.product_id
            data = get_parsed_data(comment, my_serializers.CommentSerializer)
            mycol = mongo_db[mongo_db_name], comment_id = comment
            mycol.update_one({'id': foreignkey}, {'$push': {'json.comment_set': data}})
            return Response({'status': 'نظر شما با موفقيت ثبت شد.'})
        except:
            return Response({'status': 'اطلاعات جهت ثبت نظر کافي نيست.'}, status=400)





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
        image = Image(image=request.data['file'], alt=ImageCreationSizes.get_alt('default'), path='posts')
        obj = ImageCreationSizes(data={'image': request.data['file']}, sizes=sizes, instances=[ImageSizes(alt=ImageCreationSizes.get_alt(size), size=size, father=image) for size in sizes])
        paths, instances = obj.save(upload_to='/media/posts_images/')
        image.save()
        ImageSizes.objects.bulk_create(instances)
        paths['default'], paths['image_id'] = image.image.url, image.id
        return Response(paths)
