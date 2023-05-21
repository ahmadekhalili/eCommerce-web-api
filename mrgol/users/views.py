from django.conf import settings
from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.sessions.backends.db import SessionStore

from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .myserializers import UserSerializer, UserChangeSerializer
from .mymethods import login_validate
from .models import User
from cart.views import CartCategoryView
from cart.cart import Cart
from orders.models import ProfileOrder, Order
from orders.myserializers import ProfileOrderSerializer, OrderSerializer
from customed_files.rest_framework.rest_framework_customed_classes.custom_rest_authentication import CustomSessionAuthentication
from main.models import Post, Comment
from main.myserializers import CommentSerializer, PostListSerializer


class LogIn(views.APIView):
    def get(self, request, *args, **kwargs):                           #maybe an authenticated user come to login.get page, so we should provide sessionid
        '''
        input in header cookie "" or "favorite_products_ids=1,2,3"
        output {"csrfmiddlewaretoken": "...",  "csrftoken": "..."}
        '''
        return Response({**CartCategoryView().get(request, datas_selector='csrf').data})              #dont need sending product or other, supose user request several time this page(refreshing page), why in every reqeust, send products and other, for optain product front can request to other link and optain it and save it and in refreshing page dont need send products again(cach it in user browser).

    def post(self, request, *args, **kwargs):                            #an example for acceesing to LogIn.post:   http POST http://192.168.114.6:8000/users/login/ email=a@gmail.com password=a13431343 csrfmiddlewaretoken=jKnAefVUhdxR0fS3Jh0uozdtBc3FwtDOy2ghKVucLG479jQMYFTSxxIpjVjEEkds cookie:"csrftoken=uBvlhHOgqfaYmASnY3BtanycxOKz00cVJTo2NnnyUIHevEQ6druRjl38fx0y8RMz; favorite_products_ids=1,3,4"        
        '''
        input in request.POST {"csrfmiddlewaretoken": "...",  "phone": "...", "password": "..."}
        input in header cookie "csrftoken=..." or "csrftoken=...; favorite_products_ids=1,2,3;" if favorite_products_ids provides(in user cookie)
        output  {"sessionid": "...",  "user": "...", "favorite_products_ids": "..."}     "favorite_products_ids=1,2,3"
        '''
        user = login_validate(request)
        CustomSessionAuthentication().enforce_csrf(request)          #if you dont put this here, we will havent csrf check (meants without puting csrf codes we can login easily)(because in djangorest, csrf system based on runing class SessionAuthentication(here)CustomSessionAuthentication and class CustomSessionAuthentication runs when you are loged in, because of that we use handy method enforce_csrf(we arent here loged in), just in here(in other places, all critical tasks that need csrf checks have permissions.IsAuthenticated require(baese csrf check mishavad)).        
        login(request, user)
        cart = Cart(request)
        supporter_datas = CartCategoryView().get(request, datas_selector='products_user').data
        return Response({'sessionid': request.session.session_key, **supporter_datas})




from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError, ErrorDetail
class SignUp(views.APIView):

    def post(self, request, *args, **kwargs):
        '''
        input in POST = {"csrfmiddlewaretoken": "...", "email": "...", "password1": "...", "password2": "..."}__________
        input in header = {"csrftoken": "..."}
        '''
        CustomSessionAuthentication().enforce_csrf(request)
        phone, password1, password2 = request.data.get('phone'), request.data.get('password1'), request.data.get('password2')
        serializer = UserSerializer(data={'phone': phone, 'password': password1})
        serializer.is_valid(raise_exception=True)                           # raise errors better than User.objects.create_user(...) forr example creating user with dublicate phone, create_user raise error:  duplicate key value violates unique constraint "users_user_phone_key"...     while is_valid raise: "unique": "کاربر با این شماره تلفن از قبل موجود است."
        serializer.save()
        return Response(serializer.data)




class UserChange(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        '''
        input, output = None__________
        method get is done in front, front create a userchangeform and request url /supporter_datas/user/ to optain user datas for prepopulate fields.__________
        for decide which user fields should provide in userchangeform, you can see User table in /static/app1/mrgol_visualized.png/
        '''
        return Response({**CartCategoryView().get(request, datas_selector='user_csrf').data})

    def put(self, request, *args, **kwargs):                #connect like this:   http PUT http://192.168.114.21:3000/users/userchange/ cookie:"sessionid=87y70z4bnj6kj9698qbpas1a0w3ncfpx; csrftoken=SSp1m9eJ7mHuIncE88iEwF2VzspDFi7uOWlXamzNjd1vDZT9YjxrFgNjyDUIs7wQ" first_name="تچیز" csrfmiddlewaretoken=KZNz210BMpQLjRurCxxMtDnILetmQxMDG3JvQelFYgaMetbWsIMzCe86KpYrDmbZ        important: if you dont pot partial=True always raise error 
        '''
        input = submited userchangeform should sent here (/userchange/) like <from action="domain.com/users/userchange/" ...>__________
        output(in success) = front should request user (/supporter_datas/user/) to optain user with new changes.__________
        output(in failure) = {"is_superuser": ["Must be a valid boolean."],"email": ["Enter a valid email address."]}
        '''
        if request.data.get('postal_code'):
            profile_order = ProfileOrder.objects.filter(user=request.user, main=True)
            serializer = ProfileOrderSerializer(profile_order[0], data={'postal_code': request.data['postal_code']}, partial=True) if profile_order else {}
            if serializer:
                if serializer.is_valid():
                    serializer.save()
                    return Response({'postal_code': serializer.data.get('postal_code')})
                else:
                    return Response(serializer.errors)
            else:
                return Response({})

        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(dict([(key, serializer.data.get(key)) for key in request.data if serializer.data.get(key)]))             #{**CartCategoryView().get(request, datas_selector='user').data}
        else:
            return Response(serializer.errors)




class UserProfile(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        profileorders = request.user.profileorders.select_related('town__state')
        profileorders_serialized = ProfileOrderSerializer(profileorders, many=True).data
        orders = Order.objects.filter(profile_order__user=request.user)
        orders_serialized = OrderSerializer(orders, many=True, context={'request': request}).data
        comments_serialized = CommentSerializer(request.user.written_comments.all(), many=True).data
        user_serialized = UserSerializer(request.user).data
        return Response({'profileorders': profileorders_serialized, 'orders': orders_serialized, 'comments': comments_serialized, 'user': user_serialized})




class AdminProfile(views.APIView):
    def get(self, request, *args, **kwargs):
        user = User.objects.filter(id=kwargs.get('id'))
        if user:
            user_serialized = UserSerializer(user[0]).data
            fields = ['first_name', 'last_name', 'date_joined', 'email']
            # we don't want to create admin profile serializer just for reading process. filter UserSerializer instead.
            profile = {key: user_serialized[key] for key in user_serialized if key in fields}
            posts = Post.objects.filter(author=user[0])
            posts_serialized = PostListSerializer(posts, many=True, context={'request': request}).data
            comments = Comment.objects.filter(author=user[0])
            comments_serialized = CommentSerializer(comments, many=True).data
        return Response({'profile': profile, 'posts': posts_serialized, 'comments': comments_serialized})
