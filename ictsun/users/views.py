from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth import login
from django.utils.translation import gettext_lazy as _

from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

import requests
import pymongo
import environ
import uuid
import jwt
import os
from pathlib import Path
from urllib.parse import quote_plus

from .serializers import UserSerializer
from .methods import login_validate
from .models import User
from cart.views import CartCategoryView
from cart.cart import Cart
from orders.views import ListCreateOrderItem
from orders.models import ProfileOrder
from orders.serializers import ProfileOrderSerializer
from main.models import Comment
from main.methods import DictToObject
from main.serializers import CommentSerializer, PostListSerializer

env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))
username, password, db_name = quote_plus(env('MONGO_USERNAME')), quote_plus(env('MONGO_USERPASS')), env('MONGO_DBNAME')
auth_source, host = env('MONGO_SOURCE'), env('MONGO_HOST')
uri = f"mongodb://{username}:{password}@{host}:27017/{db_name}?authSource={auth_source}"
mongo_db = pymongo.MongoClient(uri)[db_name]


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
        #SessionAuthenticationCustom().enforce_csrf(request)          #if you dont put this here, we will havent csrf check (meants without puting csrf codes we can login easily)(because in djangorest, csrf system based on runing class SessionAuthentication(here)SessionAuthenticationCustom and class SessionAuthenticationCustom runs when you are loged in, because of that we use handy method enforce_csrf(we arent here loged in), just in here(in other places, all critical tasks that need csrf checks have permissions.IsAuthenticated require(baese csrf check mishavad)).
        login(request, user)
        Cart(request)
        supporter_datas = CartCategoryView().get(request, datas_selector='products_user').data
        return Response({'message': 'loged in!', 'sessionid': request.session.session_key, **supporter_datas})



class SendSMS(views.APIView):
    def get(self, request, *args, **kwargs):
        r = Response({})
        r.set_cookie('age', 'MY age VALUE')
        return r

    def post(self, request, *args, **kwargs):
        '''
        here we generate a code. 1- sms it to client phone 2- set encoded of code to client cookie.
        after entering code by client, we compare code is entered with code in cookie.
        '''
        if request.data.get('phone'):
            to = str(request.data['phone'])     # phone format should be like: 0910233....
            message = '''
            کد فعال سازی شما {} می باشد.
            {}
            '''
            cd = uuid.uuid4().hex[:4]
            encoded = jwt.encode({'phone': to, 'code': cd}, settings.SECRET_HS, algorithm="HS256")
            domain = Site.objects.get_current()
            data = {'from': '50004001337664', 'to': to, 'text': message.format(cd, domain)}
            response = requests.post('https://console.melipayamak.com/api/send/simple/9b40f9cf113c4d3fad0da51284014d04',
                                     json=data)      # here sms is sent (by console way).
            r = Response({'cookie_token': encoded, **response.json()})
            r.set_cookie('token', encoded)        # cookie is set directly to client browser.
            return r
        return Response({'message': _('please specify your phone number.')})


class SignUp(views.APIView):
    def post(self, request, *args, **kwargs):    # create user only with phone (and sms verification)
        '''
        input in POST = {"csrfmiddlewaretoken": "...", "phone": "...", "password1": "...", "password2": "..."}__________
        input in header cookie = {"csrftoken": "..."}
        '''
        #SessionAuthenticationCustom().enforce_csrf(request)
        posted_cd = request.data['code']
        # decoded contain phone and code (sent via SMS)
        decoded = jwt.decode(request.COOKIES['token'], settings.SECRET_HS, algorithms=["HS256"])
        if decoded['code'] == posted_cd:         # both variables have to be str
            serializer = UserSerializer(User.objects.create(phone=decoded['phone']))
            return Response({'message': _('user successfully created.'), **serializer.data})
        return Response({'message': _('verification code is incorrect')})


class UserUpdate(views.APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, *args, **kwargs):                #connect like this:   http PUT http://192.168.114.21:3000/users/update/ cookie:"sessionid=87y70z4bnj6kj9698qbpas1a0w3ncfpx; csrftoken=SSp1m9eJ7mHuIncE88iEwF2VzspDFi7uOWlXamzNjd1vDZT9YjxrFgNjyDUIs7wQ" first_name="تچیز" csrfmiddlewaretoken=KZNz210BMpQLjRurCxxMtDnILetmQxMDG3JvQelFYgaMetbWsIMzCe86KpYrDmbZ        important: if you dont pot partial=True always raise error
        '''
        input = submited userchangeform must sent here (/update/) like <from action="domain.com/users/update/" ...>__________
        output(in success) = front must request user (/supporter_datas/user/) to optain user with new changes.__________
        output(in failure) = {"is_superuser": ["Must be a valid boolean."],"email": ["Enter a valid email address."]}
        '''
        user = request.user
        if request.data.get('password'):       # set password (in first time)
            user.set_password(request.data['password'])
            user.save()
            serializer = UserSerializer(user)
            return Response({'message': _('password has been set successfully'), **serializer.data})

        elif request.data.get('postal_code'):
            profile_order = ProfileOrder.objects.filter(user=user, main=True)
            serializer = ProfileOrderSerializer(profile_order[0], data={'postal_code': request.data['postal_code']}, partial=True) if profile_order else {}
            if serializer:
                if serializer.is_valid():
                    serializer.save()
                    return Response({'postal_code': serializer.data.get('postal_code')})
                else:
                    return Response(serializer.errors)
            else:
                return Response({})

        else:
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
        comments_serialized = CommentSerializer(request.user.written_comments.all(), many=True).data
        user_serialized = UserSerializer(request.user).data
        return Response({'profileorders': profileorders_serialized, **ListCreateOrderItem().get(request).data, 'comments': comments_serialized, 'user': user_serialized})




class AdminProfile(views.APIView):
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        user = User.objects.filter(id=pk)
        if user:
            user_serialized = UserSerializer(user[0]).data
            fields = ['first_name', 'last_name', 'date_joined', 'email']
            # we don't want to create admin profile serializer just for reading process. filter UserSerializer instead.
            profile = {key: user_serialized[key] for key in user_serialized if key in fields}
            posts = DictToObject(mongo_db.post.find({'author.id': pk}), many=True)
            posts_serialized = PostListSerializer(posts, many=True).data
            comments = Comment.objects.filter(author=user[0])
            comments_serialized = CommentSerializer(comments, many=True).data
        return Response({'profile': profile, 'posts': posts_serialized, 'comments': comments_serialized})
