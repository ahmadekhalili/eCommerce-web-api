
from rest_framework import views
from rest_framework.response import Response

from decimal import Decimal

from .cart import Cart
from .serializers import CartProductSerializer


class CartPageView(views.APIView):       #user come from 'sabad'(in header) to here. 
    def get(self, request, *args, **kwargs):                                       #supose user refresh /cart/ page
        serializers, cart, total_prices = [], Cart(request), Decimal(0)
        cart.cart_page = True
        for item in cart:
            serializers.append({**CartProductSerializer(item, context={'request': request}).data, 'price_changes': item['price_changes'], 'lach_quantity': item['lach_quantity']}) #lach_quantity? supose we ordered 6x of a product, if we have only 2 product in our stock lach quantity is  4.
            total_prices += item['total_price']
        return Response({'sabad': serializers, 'products_count': cart.get_products_count(), 'total_prices': str(total_prices)})




class CartCategoryView(views.APIView):       #'sabad'(in header)
    def get(self, request, *args, **kwargs):                                       #supose user refresh /cart/ page
        serializers, cart, total_prices, total_weight, dimensions, dimensions_fail = [], Cart(request), Decimal(0), 0, [], False          #we sended dimensions not volume for using in future (in formols for processing carton size).
        for item in cart:
            serializers.append({**CartProductSerializer(item, context={'request': request}).data})
            total_prices += item['total_price']
            total_weight += item['product'].weight * item['quantity'] if item['product'].weight else 0
            dimensions += [item['product'].size for i in range(item['quantity'])]
            dimensions_fail = True if not item['product'].size else dimensions_fail
        dimensions = dimensions if not dimensions_fail else None             #if one product has not size, dont need dimensions at all. (we compute carton size as default size) 
        sessionid = request.session.session_key
        return Response({'sessionid': sessionid, 'sabad': serializers, 'products_count': cart.get_products_count(), 'total_prices': str(total_prices), 'total_weight': total_weight, 'dimensions': dimensions})




class CartAdd(views.APIView):       #user come from 'sabad'(in header) to this method.  add id in front, just front must car add current_item + cart_cookie in add. #set_fingers and remove  is in front 
    def post(self, request, *args, **kwargs):
        #SessionAuthenticationCustom().enforce_csrf(request)                        # this enable csrf checks for unauthenticated user (for loged in user, DEFAULT_AUTHENTICATION_CLASSES in settings.py cause csrf checks.
        data = request.data
        cart = Cart(request)
        cart.add(product_id=data['product_id'], quantity=data.get('quantity', 1), shopfilteritem_id=data.get('shopfilteritem_id'))    #cd['quantity'] is int but how is it because: coerce=int ? request.data['quantity'] is rest/views/CartDetail is string
        return Response({**CartCategoryView().get(request).data})




class CartMinus(views.APIView):       #reduce selected quantity of proselect by 1.  
    def post(self, request, *args, **kwargs):
        #SessionAuthenticationCustom().enforce_csrf(request)
        data = request.data
        cart = Cart(request)
        cart.minus(product_id=data['product_id'], shopfilteritem_id=data.get('shopfilteritem_id'))
        return Response({**CartCategoryView().get(request).data})




class CartRemove(views.APIView):       #user come from 'sabad'(in header) to this method.  add id in front, just front must car add current_item + cart_cookie in add. #set_fingers and remove  is in front 
    def post(self, request, *args, **kwargs):
        #SessionAuthenticationCustom().enforce_csrf(request)
        cart = Cart(request)
        cart.remove(request.data.get('product_id'), request.data.get('shopfilteritem_id'))
        return Response({**CartCategoryView().get(request).data})
