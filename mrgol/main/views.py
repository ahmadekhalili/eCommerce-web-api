from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.core.cache import cache
#from django.template.defaultfilters import slugify
from django.utils.text import slugify
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.contrib.sessions.backends.db import SessionStore
from django.core.validators import MinValueValidator, MaxValueValidator

from rest_framework import viewsets
from rest_framework import generics, mixins
from rest_framework import permissions, authentication
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework import views

from . import myserializers, myforms
from .mymethods import get_products, get_posts, get_posts_products_by_root, make_next
from .models import *
from users.myserializers import UserSerializer, UserChangeSerializer
from users.models import User
from cart.models import SesKey
from cart.myserializers import CartProductSerializer
from cart.cart import Cart
from orders.models import ProfileOrder
#Post_Category        Product_Category


from django.utils.html import format_html
from django.utils import translation
from django.contrib import messages
from django.forms.models import inlineformset_factory
from django.forms import formset_factory
from orders.models import ProfileOrder, Order, paid_type_choices
from decimal import Decimal
from django.db.models import F, Q, Case, Value, When, Count
from orders.forms import OrderCreateForm
from orders.models import OrderItem, Order, ProfileOrder
from orders.myserializers import OrderItemSerializer
from rest_framework.routers import DefaultRouter
from customed_files import date_convertor
from orders.myserializers import ProfileOrderSerializer, OrderSerializer, OrderItemSerializer


def index(request):
    if request.method == 'GET':
        #cache.set('name', ['mkh is my name', 'akh is my name'])
        #str(request.META.get('HTTP_COOKIE'))id=14   fied_1=s2
        #Root._meta.get_field('level').validators[0].limit_value
        #user_language = 'fa'
        #translation.activate(user_language)
        #request.session[translation.LANGUAGE_SESSION_KEY] = user_language
        #Accept-Language

        posts = ''

        a = ''
        b = ''

        #formset_factory(myforms.ImageForm)()
        #formset = formset_factory(myforms.RootForm, extra=2)
        #posts = f(initial=[{'name': 'asdasd', 'slug':'eqwe', 'level': 1, 'father_root': 26, 'post_product': 'product',}])#inlineformset_factory(Product, Root, fields=('name', 'slug', 'level', 'father_root', 'post_product'))(instance=p)
        rend = render(request, 'main/index.html', {'posts': posts, 'a': a})
        #rend.set_cookie('cart_products', {'1': {'q': 23, 'p': 33}, '2': {'q': 230, 'p': 330}})
        return rend
    
    else:
        posts= 'age' in request.POST
        p=''
        return render(request, 'main/index.html', {'posts': posts, 'p': p})




    
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
        if 'products' in datas_selector:
            serializers, cart, total_prices = [], Cart(request), Decimal(0)
            for item in cart:
                serializers.append({**CartProductSerializer(item['product'], context={'request': request}).data, 'price': str(item['price']), 'quantity': item['quantity'], 'price_changes': item['price_changes'], 'total_price': str(item['total_price'])})
                total_prices += item['total_price']
            datas = {**datas, **{'sabad': serializers, 'products_count': cart.get_products_count(), 'total_prices': str(total_prices)}}
            
        if 'favorites' in datas_selector:
            pass
            #datas = {**datas, **{'favorites': Cart(request).get_favorite_products()}}
        if 'user' in datas_selector:                                                    #if datas_selector was None it will raise error in here.
            userserializer = UserSerializer(request.user, context={'request': request}) if request.user.is_authenticated else None
            datas = {'user': userserializer.data} if userserializer else {'user': None}            #calling UserSerializer(request.user).data for unauthenticated user  (anomouse user) will raise error
            
        if 'csrf' in datas_selector:
            request_csrf_token, csrf_token= get_token(request), get_token(request) if "CSRF_COOKIE" not in request.META else ''
            datas = {**datas, **{'csrfmiddlewaretoken': get_token(request), 'csrftoken': get_token(request)}}
        return datas

    def get(self, request, *args, **kwargs):        
        return Response(self.all_datas(request, **kwargs))
    
    def post(self, request, *args, **kwargs):
        return Response(self.all_datas(request, **kwargs))



from rest_framework.permissions import IsAuthenticated
class HomePage(views.APIView):
    #permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        '''
        output 6 last created product and 4 last created post(visible=True, and select products with available=True in first).
        '''
        products = get_products(0, 6)
        posts = get_posts(0, 4).select_related('root') if get_posts(0, 4) else []
        #supporter_datas = supporter_datas_serializer(request, mode='read')
        products_serialized = {'products': myserializers.ProductListSerializer(products, many=True, context={'request': request}).data}       #myserializers.ProductListSerializer(posts, many=True).data  is list not dict so cant use ** before it (like {**serialized})
        posts_serialized = {'posts': myserializers.PostListSerializer(posts, many=True, context={'request': request}).data}
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **products_serialized, **posts_serialized})

    def post(self, request, *args, **kwargs):
        return Response({'loooooooooool': 'tooooooool'})
        



'''
@api_view(['GET', 'POST'])
def product_list(request):
    """
    List all products, or create a new product.
    """
    if request.method == 'GET':
        products = Product.objects.filter(id__lt=100).select_related('rating').prefetch_related('comments', 'image_set')
        serializer = myserializers.ProductDetailSerializer(products, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = myserializers.ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#.prefetch_related('comments__author')
class ProductList(generics.ListAPIView):

    def list(self, request, *args, **kwargs):
        super().list(request, *args, **kwargs)
        serializer = p(queryset, many=True, context={'request': request})
        return Response(serializer.data)  
    queryset = Product.objects.filter(id__lt=100).select_related('rating').prefetch_related('comments', 'image_set')
    serializer_class = myserializers.ProductDetailSerializer
    #permission_classes = [permissions.IsAuthenticated]


why this desing expired?
class PostList(views.APIView):                                                              
    def get(self, request):
        count = 0
        posts = Post.objects.filter(id__in=[1, 2, 3, 4, 5])
        serializers = myserializers.PostListSerializer(posts, many=True, context={'request': request}).data              #you must put context={'request': request} in PostListSerializer argument for working request.build_absolute_uri  in PostListSerializer, otherwise request will be None in PostListSerializer and raise error 
        for post in posts:
            pk, slug = post.id, post.slug
            serializer = serializers[count]
            serializer['url'] = f'{pk}/{slug}/'
            #serializer['image_icon'] = request.build_absolute_uri(post.image_icon) 
            count += 1
        return Response(serializers)    

'''
    



class PostList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output 12 last created posts(visible=True)
        '''
        menu_slug = kwargs.get('menu')
        if menu_slug:
            root = get_object_or_404(Root, slug=menu_slug)
            posts = get_posts_products_by_root(root)
            sessionid = request.session.session_key
            serializers = {'posts': myserializers.PostListSerializer(posts, many=True, context={'request': request}).data}             #you must put context={'request': request} in PostListSerializer argument for working request.build_absolute_uri  in PostListSerializer, otherwise request will be None in PostListSerializer and raise error 
            return Response({'sessionid': sessionid, **serializers})   
        posts = get_posts(0, 8).select_related('root')
        serializers = {'posts': myserializers.PostListSerializer(posts, many=True, context={'request': request}).data}             #you must put context={'request': request} in PostListSerializer argument for working request.build_absolute_uri  in PostListSerializer, otherwise request will be None in PostListSerializer and raise error 
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializers})   




class ProductList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output shown 24 last created product and 4 last created post(visible=True, and select products with available=True in first).
        '''
        #menu_slug = request.GET.get('menu')
        menu_slug = kwargs.get('menu')
        if menu_slug:                              
            ## 1- menu category. url example:  /products/menu=sumsung (or  /products/?menu=sumsung dont differrent) just dont put '/' in end of url!!!!
            root = get_object_or_404(Root, slug=menu_slug)
            products = get_posts_products_by_root(root)
            root_and_allitschiles = Root.objects.filter(id__in=list(filter(None, root.all_childes_id.split(',')))+[root.id])   #why we used filter? root.all_childes_id.split(',') may return: [''] that raise error in statements like  filter(in__in=['']) so we ez remove blank str of list by filter.
            sidebarmenu_checkbox =  root_and_allitschiles.filter(level__in=[root.id, root.id+1]) if root.levels_afterthis == 1 else None
            sidebarmenu_link = root_and_allitschiles.filter(level__in=[root.id, root.id+1]) if root.levels_afterthis > 1 else None
            filter_ids = root_and_allitschiles.values_list('filter', flat=True)
            filters_serialized = myserializers.FilterSerializer(Filter.objects.filter(id__in=filter_ids).prefetch_related('filter_attributes'), many=True).data       #in FilterSerializer has field 'filter_attributes' so if we dont put this prefetch, program will run 1+len(filters) queries (for example supose we have this filters:  <object(1) Filter>, <object(2) Filter> queries number was run for serializing filters: our program run one query for this two object and second for: <object(1) Filter>.filter_attributes.all() and third for <object(2) Filter>.filter_attributes.all() so run 3 query for this 2 filter object! but now just run 2 for eny filter objects.
            
        else:                                      #none category.   url example:  /products/
            products = get_products(0, 24)
            sidebarmenu_checkbox = None
            sidebarmenu_link = Root.objects.filter(level=1)
            filters_serialized = myserializers.FilterSerializer(Filter.objects.all().prefetch_related('filter_attributes'), many=True).data    

        ## 2 sidebar filter.   url example: /products?meshki_1=1/      filter_attributes_slugid_id_list is like: [{'meshki_1': '1'}, {'sefid_2': '2'}, ..]. why we choiced  slug+_+id?  answer: in below line we use requet.GET['key'] that is like request.GET['meshki_1'] so str "meshki_1' must be uniqe and with slung+_+id it is unique
        filter_attributes_slugid_id_list = [{f"{filter_attribute['slug']}_{filter_attribute['id']}": str(filter_attribute['id'])} for filter in filters_serialized for filter_attribute in filter['filter_attributes']]    
        selected_filter_attributes_ids = [int(request.GET[key]) for key in request.GET if {key: request.GET[key]} in filter_attributes_slugid_id_list]
        products = products.filter(filter_attributes__in=selected_filter_attributes_ids) if selected_filter_attributes_ids else products
        if request.GET.get('mx'):                                                                         #sidebar filder price
            products = products.filter(price__gte=request.GET.get('mn'), price__lte=request.GET.get('mx'))           #request.GET.get('mn') and request.GET.get('mx') can be int or str dont raise eny problem.
            
        ## 3 select category  url example:  /products/کالای-دیجیتال/?select=bestselling
        Dict = {'expensivest': products.order_by('-price'), 'cheapest': products.order_by('price'), 'bestselling': products.annotate(ordered_quantity=Sum(Case(When(order_items__order__paid=True, then=F('order_items__quantity'))))).order_by('-ordered_quantity'), 'newest': products.order_by('-id')}
        if request.GET.get('select') in Dict:
            products = Dict[request.GET.get('select')]
            
        products = get_products(0, 24, products)                                         #note(just for remembering): in nested order_by like: products.order_by('-ordered_quantity').order_by('-available')   ordering start from last order_by here: -available but in one order_by start from first element like:  products..order_by('-available', '-id')  ordering start from "-available" 
        products_serialized = {'products': myserializers.ProductListSerializer(products, many=True, context={'request': request}).data}
        sidebarmenu_checkbox_serialized = myserializers.RootChainedSerializer(sidebarmenu_checkbox, many=True).data
        sidebarmenu_link_serialized = myserializers.RootChainedSerializer(sidebarmenu_link, many=True).data
        sessionid = request.session.session_key
        
        return Response({'sessionid': sessionid, **products_serialized, **{'sidebarmenu_checkbox': sidebarmenu_checkbox_serialized}, **{'sidebarmenu_link': sidebarmenu_link_serialized}, 'filters': filters_serialized})




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




class PostRootList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output all posts menues objects.
        '''          
        post_roots = Root.objects.filter(post_product='post', level=1)
        serializers = {'post_menues': myserializers.RootListSerializer(post_roots, many=True).data}
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializers})




class ProductRootList(views.APIView):
    def get(self, request, *args, **kwargs):
        '''
        output all Products menues objects.
        '''
        prefetch_query = 'root_childs'
        for i in range(Root._meta.get_field('level').validators[1].limit_value-2):
            prefetch_query += '__root_childs'
        product_prant_roots = Root.objects.filter(post_product='product', level=1).prefetch_related(prefetch_query)
        serializers = {'product_menues': myserializers.RootListSerializer(product_prant_roots, many=True).data}
        #sessionid = request.session.session_key
        return Response({'sessionid': '', **serializers})



    
class PostDetail(views.APIView):
    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': myserializers.PostDetailSerializer(product_roots).data} because myserializers.PostDetailSerializer(product_roots).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        '''
        input receive from /posts/ like posts0.url = "3/یسشی/"__________
        output a post depend on pk you specify.
        '''
        #permission_classes = [permissions.IsAuthenticated]
        post = Post.objects.filter(id=kwargs['pk']).select_related('author', 'root').prefetch_related('content_set', 'comment_set')
        serializer = myserializers.PostDetailSerializer(post, many=True).data
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializer[0]})               #serializer is list (because of many=True)    serializer[0] is dict




    
class ProductDetail(views.APIView):
    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': myserializers.PostDetailSerializer(product_roots).data} because myserializers.PostDetailSerializer(product_roots).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        '''
        input receive from /products/ like products0.url = "1/گل-زر/"__________
        output a product depend on pk you specify.
        '''
        select_related_father_root = 'root'
        for i in range(Root._meta.get_field('level').validators[1].limit_value-1):
            select_related_father_root += '__father_root'
        product = Product.objects.filter(id=kwargs['pk']).select_related(select_related_father_root, 'rating').prefetch_related('comment_set', 'image_set')
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




'''
generics.RetrieveAPIView
queryset = Post_Category.objects.all()
serializer_class = myserializers.PostListSerializer
def retrieve(self, request, *args, **kwargs):
    instance = self.get_object()
    serializer = myserializers.PostListSerializer(instance.post_set.all(), many=True, context={'request': request})
    return Response(serializer.data)


class PostRootDetail(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': myserializers.PostDetailSerializer(product_roots).data} because myserializers.PostDetailSerializer(product_roots).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        #input: receive from  /posts/roots/  like product_roots0.url = "/1/زینتی/"__________
        #output: Root is choicen depend on pk you specify and next depend on post or product root, will be shown all products or posts related to root and root's children. {"sessionid": "...", "products": [...]} 
        root = Root.objects.get(id=kwargs['pk'])
        serializers = {'posts': myserializers.PostListSerializer(get_posts_products_by_root(root), many=True, context={'request': request}).data}            
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializers})

    
class ProductRootDetail(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):                #dont need define like serializer = {'post': myserializers.PostDetailSerializer(product_roots).data} because myserializers.PostDetailSerializer(product_roots).data dont has many=True so is dict not list and dont raise error when putin in Reaponse
        #input: receive from /products/roots/   like product_roots0.url = "/1/زینتی/"__________
        #output: Root is choicen depend on pk you specify and next depend on post or product root, will be shown all products or posts related to root and root's children. {"sessionid": "...", "products": [...]}
        root = Root.objects.get(id=kwargs['pk'])
        serializers = {'products': myserializers.ProductListSerializer(get_posts_products_by_root(root), many=True, context={'request': request}).data}
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, **serializers})
'''




class ProductCommentCreate(generics.RetrieveAPIView):
    def post(self, request, *args, **kwargs):                
        '''
        '''    
        if request.user.is_authenticated:
            try:
                data = request.data
                comment = Comment.objects.create(content=data['content'], author=request.user, product_id=data['product_id'])
                return Response({'status': 'نظر شما با موفقيت ثبت شد.'})
            except:
                return Response({'status': 'اطلاعات جهت ثبت نظر کا في نيست.'})
        else:
            return Response({'user': request.user})



