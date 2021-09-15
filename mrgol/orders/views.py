from django.utils.translation import gettext_lazy as _

from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from decimal import Decimal

from main.views import SupporterDatasSerializer
from main.models import Product, ShopFilterItem
from main.model_methods import update_product_stock
from cart.cart import Cart
from payment.views import PaymentStart
from .models import ProfileOrder, Order, OrderItem
from .forms import OrderCreateForm
from .myserializers import ProfileOrderSerializer, OrderSerializer, OrderItemSerializer



class ListCreateProfileOrder(views.APIView):
    #permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):                             #here listed ProfileOrders of a user.  come here from url /cart/.  (after runing class cart/views/CartView should come to this class   
        user = request.user
        if user.is_authenticated:
            profileorders = user.profileorders.all()
            if profileorders:
                return Response({**SupporterDatasSerializer().get(request, datas_selector='products_user_csrf').data, 'profileorders': ProfileOrderSerializer(profileorders, many=True).data})   #here front side must create "checkbox like" element  refrencing to ListCreateOrderItem, also front should create price changes message if item['old_price'] vs item['price'] is different.
            else:
                
                return Response({**SupporterDatasSerializer().get(request, datas_selector='products_user_csrf').data, 'profileorders': None})     #here front side must create blank ProfileOrder Form with action refrenced to ListCreateProfileOrder.post. (you can create form and its html elements by django modelform and say to front html elements)
        else:                                     
            return Response({**SupporterDatasSerializer().get(request, datas_selector='user_csrf').data})        #redirect to login page by front.

    def post(self, request, *args, **kwargs):                             #here ProfileOrder cerated from Form datas sended by user.
        if request.user.is_authenticated:
            data = request.data                                               #request.data is exatly dict and you can easily assign to it.
            main_profileorder = ProfileOrder.objects.filter(user=request.user, main=True)
            data['main'] = True if not main_profileorder else False           #first profileorder must be main profileorder.
            data['user'] = request.user.id
            serializer  = ProfileOrderSerializer(data=data)     #data must be like {"user": 1, "first_name": "javad", "last_name":"haghi", "phone":"09127761277", "email":"aa@gmail.com", "address":"tehran", "postal_code":"1111111111"} to save ProfileOrder object successfuly. id of user can be int or str dont different.
            if serializer.is_valid():
                profileorder = serializer.save()                           
                return Response({**SupporterDatasSerializer().get(request, datas_selector='products_user_csrf').data, 'profileorders': ProfileOrderSerializer(request.user.profileorders.all(), many=True).data})   #why dont use like: OrderSerializer(order).data?   answer: may user create second order, so we need alwayes use user.orders.all() .
            else:
                return Response(serializer.errors)
        else:                                     
            return Response({**SupporterDatasSerializer().get(request, datas_selector='user_csrf').data})



class ListCreateOrderItem(views.APIView):  
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):                            #here listed  products ordered for showing in userprofile.
        orders = Order.objects.filter(profile_order__user=request.user, paid=True).select_related('profile_order').prefetch_related('items__product__image_icon', 'items__product__rating').order_by('-created')#OrderItem.objects.filter(order__profile_order__user=request.user, order__paid=True).select_related('order__profile_order').order_by('-order__created')
        return Response({'orders': OrderSerializer(orders, many=True, context={'request': request}).data})
    
    def post(self, request, *args, **kwargs):                           #here created orderitems.  come here from class ListCreateProfileOrder.get    connect here with utl: http http://192.168.114.21:8000/orders/orderitems/ cookie:"sessionid=601jyaeogtlq6jil5fjasvng2fh77kos" profile_order_id=1
        cart = Cart(request)
        paid_type = request.data.get('paid_type', 'online')
        total_prices = Decimal(0)

        if paid_type == 'cod':
            orderitems, products, shopfilteritems, lists = [], [], [], []
            for item in cart:
                price_changed = True if item['price_changes'] != Decimal('0') else price_changed
                quantity_ended = True if item['shopfilteritem'] and item['quantity'] > item['shopfilteritem'].stock else True if item['quantity'] > item['product'].stock else quantity_ended
                total_prices += item['total_price']
                lists.append([item['shopfilteritem'], item['product'], item['quantity']]) if item['shopfilteritem'] else lists.append([item['product'], item['quantity']])                    
                orderitems.append(OrderItem(product=item['product'], price=item['total_price'], quantity=item['quantity']))
        
            if not price_changed and not quantity_ended:
                order = Order.objects.create(profile_order_id=request.data['profile_order_id'], paid_type='cod', price=total_prices, order_status='0')
                for orderitem in orderitems:
                    orderitem.order = order 
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

        elif paid_type == 'online':
            price_changed, quantity_ended = False, False
            for item in cart:
                price_changed = True if item['price_changes'] != Decimal('0') else price_changed
                quantity_ended = True if item['shopfilteritem'] and item['quantity'] > item['shopfilteritem'].stock else True if item['quantity'] > item['product'].stock else quantity_ended
                total_prices += item['total_price']
            if not price_changed and not quantity_ended:
                cart.session['profile_order_id'] = request.data['profile_order_id']
                cart.session.save()
                payment_start = PaymentStart().post(request, total_prices=total_prices)
                return payment_start
            else:
                return Response({'price_changed': price_changed, 'quantity_ended': quantity_ended, **SupporterDatasSerializer().get(request, datas_selector='products_user_csrf').data})       #redirect to cart page by front.

        else:
            return Response({})



