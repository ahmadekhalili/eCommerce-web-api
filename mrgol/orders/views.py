from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from decimal import Decimal
from datetime import datetime

from customed_files.date_convertor import MiladiToShamsi
from customed_files.states_towns import list_states_towns
from main.models import Product, ShopFilterItem
from main.model_methods import update_product_stock
from main.mymethods import PostDispatchPrice
from cart.views import CartMenuView
from cart.cart import Cart
from payment.views import PaymentStart
from .models import ProfileOrder, Order, OrderItem, Shipping, Dispatch
from .myserializers import ProfileOrderSerializer, OrderSerializer, OrderItemSerializer



class ListCreateProfileOrder(views.APIView):
    permission_classes = [IsAuthenticated]                               #redirect to login page by front if user is not loged in.
    def get(self, request, *args, **kwargs):                             #here listed ProfileOrders of a user.  come here from url /cart/.  here front side must create "checkbox like" element  refrencing to ListCreateOrderItem, and when click on checkbox auto submit to ProfileOrderDetail.get for optaining shiping price.  
        profileorders = request.user.profileorders.select_related('town__state')
        if profileorders:
            for profileorder in profileorders:
                profileorder.state = profileorder.town.state             #profileorder.state needed in ProfileOrderSerializer
            cart_menu = CartMenuView().get(request).data
            return Response({**cart_menu, 'profileorders': ProfileOrderSerializer(profileorders, many=True).data})   
        else:            
            return Response({**cart_menu, 'profileorders': None})         #after this front side must create blank ProfileOrder Form with action refrenced to ListCreateProfileOrder.post. (you can create form and its html elements by django modelform and say to front html elements)    

    def post(self, request, *args, **kwargs):                             #here ProfileOrder cerated from Form datas sended by user.
        data = request.data                                               #data sended must be like {"first_name": "javad", "last_name":"haghi", "phone":"09127761277", "town":"1", "address":"tehran", "postal_code":"1111111111"} to save ProfileOrder object successfuly.
        main_profileorder = ProfileOrder.objects.filter(user=request.user, main=True)
        data['main'] = True if not main_profileorder else False           #first profileorder must be main profileorder.
        data['user'] = request.user.id
        serializer  = ProfileOrderSerializer(data=data)     
        if serializer.is_valid():
            profileorder = serializer.save()
            get = request.GET.copy()
            get.setlist('profileorder_id', str(profileorder.id))
            request.GET = get
            return Response(ProfileOrderSerializer(profileorder).data)    #why dont use like: OrderSerializer(order).data?   answer: may user create second order, so we need alwayes use user.orders.all() .
        else:
            return Response(serializer.errors)




class ProfileOrderDetail(views.APIView):                                  
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):                                       #here shipping price compute and sended to front. (depende whitch profileorder choisen)
        profileorder = ProfileOrder.objects.filter(id=kwargs.get('pk')).select_related('town__state')[0]
        cart_menu = CartMenuView().get(request).data
        if not cart_menu['sabad']:
            return Response(_('your cart is empty, add a product to order.'))
        cart = Cart(request)
        shipping = Shipping.objects.first()
        post_price = PostDispatchPrice(cart_menu['total_weight'],  cart_menu['dimensions']).get_price(shipping.town.state.key, shipping.town.key, profileorder.town.state.key, profileorder.town.key) + shipping.fee
        for dispatch in shipping.dispatch_set.all():
            if dispatch.town == profileorder.town:
                cart.session['personal_shipping_price'], cart.session['post_shipping_price'] = str(dispatch.shipping_price), str(post_price)               #personal_shipping_price and post_shipping_price uses in ListCreateOrderItem.post for creating order
                cart.save()
                return Response({'profileorder_selected': profileorder.id, 'personal_dispatch': {'price': dispatch.shipping_price, 'delivery_date': dispatch.delivery_date_delay}, 'post_price': post_price})
            
        cart.session['personal_shipping_price'], cart.session['post_shipping_price'] = None, str(post_price)
        cart.save()                
        return Response({'profileorder_selected': profileorder.id, 'post_price': post_price})        #profileorder_selected is for what? answer: front know whitch checkbox should be selected after profileorder creation(after coming from ListCreateProfileOrder.post to .get) 
            
    def put(self, request, *args, **kwargs):                                           #here ProfileOrder updated.
        profileorder = ProfileOrder.objects.get(id=kwargs.get('pk'))
        serializer  = ProfileOrderSerializer(instance=profileorder, data=request.data, partial=True)     
        if serializer.is_valid():
            profileorder = serializer.save()                           
            return Response(ProfileOrderSerializer(profileorder).data)
        else:
            return Response(serializer.errors)

    def delete(self, request, *args, **kwargs):                                        #here ProfileOrder deleted.
        profileorder = ProfileOrder.objects.get(id=kwargs.get('pk'))
        profileorder.visible = False
        profileorder.save()
        return Response('deleted successfuly')




class ListCreateOrderItem(views.APIView):  
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):                            #here listed  products ordered for showing in userprofile.
        orders = Order.objects.filter(profile_order__user=request.user).select_related('profile_order').prefetch_related('items__product__image_icon', 'items__product__rating').order_by('-created')#OrderItem.objects.filter(order__profile_order__user=request.user, order__paid=True).select_related('order__profile_order').order_by('-order__created')
        return Response({'orders': OrderSerializer(orders, many=True, context={'request': request}).data})
    
    def post(self, request, *args, **kwargs):                           #here created orderitems.  come here from class ProfileOrderDetail (cart.session['shipping_price'] initialized in this class)     connect here with utl: http http://192.168.114.21:8000/orders/orderitems/ cookie:"sessionid=..." profile_order_id=1 paid_type=cod shipping_type=personal_dispatch  or post     also cart.session['shipping_price'] should be initited in ListCreateProfileOrder.get
        cart, data, total_prices, price_changed, quantity_ended = Cart(request), request.data, Decimal(0), False, False
        paid_type, shipping_type = data.get('paid_type', 'online'), data.get('shipping_type')              #important: if website have cod and online front should create 2 chekbox for thats.
        orderitems, products, shopfilteritems, lists = [], [], [], []
        for item in cart:
            price_changed = True if item['price_changes'] != Decimal('0') else price_changed
            quantity_ended = True if item['shopfilteritem'] and item['quantity'] > item['shopfilteritem'].stock else True if item['quantity'] > item['product'].stock else quantity_ended     #if item['shopfilteritem'] was true but item['quantity'] > item['shopfilteritem'].stock was false supose item['quantity'] > item['product'].stock was true its return true in quantity_ended must be false but here it dont happend because:  item['product'].stock > item['shopfilteritem'] always  (because of ShopFilterItem.save.update_product_stock) 
            total_prices += item['total_price']
            lists.append([item['shopfilteritem'], item['product'], item['quantity']]) if item['shopfilteritem'] else lists.append([item['product'], item['quantity']])                    
            orderitems.append(OrderItem(shopfilteritem=item['shopfilteritem'], price=item['total_price'], quantity=item['quantity'])) if item['shopfilteritem'] else orderitems.append(OrderItem(product=item['product'], price=item['total_price'], quantity=item['quantity']))      #here this line will saved just for cod (for online after payment)
       
        if not price_changed and not quantity_ended and paid_type in ['cod', 'online'] and shipping_type in ['personal_dispatch', 'post']:
            shipping_price = Decimal(cart.session['personal_shipping_price']) if shipping_type == 'personal_dispatch' else Decimal(cart.session['post_shipping_price'])
            total_prices += shipping_price
            order = Order.objects.create(profile_order_id=data['profile_order_id'], paid_type=paid_type, paid=False, price=total_prices, shipping_price=shipping_price, shipping_type=shipping_type, order_status='0')
            for orderitem in orderitems:
                orderitem.order = order
            if paid_type == 'cod':
                for L in lists:
                    if isinstance(L[0], ShopFilterItem):
                        L[0].stock -= L[2]                                         #important: .update is completly seperate method from .save and dont run .save so we need update availabe too. reference: https://stackoverflow.com/questions/33809060/django-update-doesnt-call-override-save
                        L[0].available = False if L[0].stock < 1 else True
                        product = update_product_stock(L[0], L[1], saving=False)
                        L[0].previous_stock = L[0].stock
                        shopfilteritems.append(L[0]), products.append(L[1])
                    else:
                        L[0].stock -= L[1]
                        L[0].available = False if L[0].stock < 1 else True
                        products.append(L[0])
                OrderItem.objects.bulk_create(orderitems)                                         #bulk_create create several objects at less than or equal 3 conecting to db.
                Product.objects.bulk_update(products, ['stock', 'available'])
                ShopFilterItem.objects.bulk_update(shopfilteritems, ['stock', 'available'])       #if shopfilteritems was blank it is not problem.
                cart.clear()
                return Response({'orderitems created successfully'})
            
            else:
                orderitem_ids = []
                for orderitem in orderitems:                                                      #note in OrderItem.objects.bulk_create dont returned eny instance and have not sulotion (maybe in later version fixed)
                    orderitem = orderitem.save()
                    orderitem_ids.append(orderitem.id)
                Product.objects.bulk_update(products, ['stock', 'available'])
                ShopFilterItem.objects.bulk_update(shopfilteritems, ['stock', 'available'])       #if shopfilteritems was blank it is not problem.
                cart.session['order_id'] = order.id
                cart.session['orderitem_ids'] = orderitem_ids
                cart.save()
                return PaymentStart().post(request, total_prices)
     
        elif price_changed or quantity_ended:
            return Response({'price_changed': price_changed, 'quantity_ended': quantity_ended, **CartMenuView().get(request, datas_selector='products_user_csrf').data})       #redirect to cart page by front.
        else:
            return Response({})



