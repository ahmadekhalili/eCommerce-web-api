from django.conf import settings

from rest_framework import views
from rest_framework.response import Response

from .cart import Cart
from main.views import SupporterDatasSerializer
from customed_files.rest_framework.rest_framework_customed_classes.custom_rest_authentication import CustomSessionAuthentication 


class CartView(views.APIView):       #user come from 'sabad'(in header) to this method. 
    def get(self, request, *args, **kwargs):                                       #supose user refresh /cart/ page
        return Response(SupporterDatasSerializer().get(request, datas_selector='products_user_csrf').data)



class CartAdd(views.APIView):       #user come from 'sabad'(in header) to this method.  add id in front, just front must car add current_item + cart_cookie in add. #set_fingers and remove  is in front 
    def post(self, request, *args, **kwargs):
        #CustomSessionAuthentication().enforce_csrf(request)
        data = request.data
        cart = Cart(request)
        cart.add(product_id=data['product_id'], quantity=data.get('quantity', 1), shopfilteritem_id=data.get('shopfilteritem_id'))    #cd['quantity'] is int but how is it because: coerce=int ? request.data['quantity'] is rest/views/CartDetail is string
        #cart.clear()
        supporter_datas = SupporterDatasSerializer().get(request, datas_selector='products').data
        cart_cookie = str(dict([(str(product['id']), product['price']) for product in supporter_datas['sabad'] if supporter_datas['sabad']]))      #lool this line, this is like: "{'1': '1000', '2': '2000'}"
        '''if not cart.session.session_key:                   #for first session creation, sesskey dont create!! for example: request.session={'1': {'quantity':1, 'price': '1000'}} request.session.session_key is none!! (session in db crated but session_key is not acceptable so we save it for accepting session_key.
            cart.session.save()'''
        sessionid = request.session.session_key               #note: for authenticated user we optain SessionStore by request.user so front just send sessionid for login, and after that we can optain session.
        return Response({'sessionid': cart.session.session_key, settings.CART_SESSION_ID: cart_cookie, **supporter_datas})




class CartRemove(views.APIView):       #user come from 'sabad'(in header) to this method.  add id in front, just front must car add current_item + cart_cookie in add. #set_fingers and remove  is in front 
    def post(self, request, *args, **kwargs):
        #CustomSessionAuthentication().enforce_csrf(request)
        cart = Cart(request)
        cart.remove(request.data.get('product_id'))
        supporter_datas = SupporterDatasSerializer().get(request, datas_selector='products').data
        cart_cookie = str(dict([(str(product['id']), product['price']) for product in supporter_datas['sabad'] if supporter_datas['sabad']]))      #lool this line, this is like: "{'1': '1000', '2': '2000'}"
        return Response({'sessionid': request.session.session_key, settings.CART_SESSION_ID: cart_cookie, **supporter_datas})
