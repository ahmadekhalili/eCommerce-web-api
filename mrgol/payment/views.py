from django.http import HttpResponse
from django.shortcuts import redirect

from rest_framework import views
from rest_framework.response import Response

from zeep import Client
from decimal import Decimal

from main.models import Product, ShopFilterItem
from main.model_methods import update_product_stock
from cart.cart import Cart
from orders.models import OrderItem, Order


MERCHANT = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
client = Client('https://sandbox.zarinpal.com/pg/services/WebGate/wsdl')
description = "توضیحات مربوط به تراکنش را در این قسمت وارد کنید"                      
email = 'email@example.com'                                                           
mobile = '09123456789'                                           

CallbackURL = 'http://127.0.0.1:8000/payment/verify/'#Important: need to edit for realy server.


class PaymentStart(views.APIView):
    def post(self, request, *args, **kwargs):
        total_prices = kwargs.get('total_prices')
        global amount                                       
        amount = total_prices if total_prices else 0                           #amount = None raise error and dont run program but amount = 0 make error_message=-1
        result = client.service.PaymentRequest(MERCHANT, amount, description, email, mobile, CallbackURL)
        if result.Status == 100:
            url = 'https://sandbox.zarinpal.com/pg/StartPay/' + str(result.Authority)
            error_message = None
        else:
            url = None
            error_message = 'ارور کد: ' + str(result.Status)
        return Response({'url': url, 'error_message': error_message})




class paymentVerify(views.APIView): 
    def get(self, request, *args, **kwargs):
        print('TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT')
        global amount
        cart = Cart(request)

        if request.GET.get('Status') == 'OK':
            global amount
            orderitems, products, shopfilteritems, lists, total_prices = [], [], [], [], Decimal(0)
            for item in cart:
                total_prices += item['total_price']
                lists.append([item['shopfilteritem'], item['product'], item['quantity']]) if item['shopfilteritem'] else lists.append([item['product'], item['quantity']])                    
                orderitems.append(OrderItem(product=item['product'], price=item['total_price'], quantity=item['quantity']))
            amount = total_prices
            result = client.service.PaymentVerification(MERCHANT, request.GET['Authority'], amount)
            if result.Status == 100:
                RefID = result.RefID
                order = Order.objects.create(profile_order_id=cart.session['profile_order_id'], paid_type='online', paid=True, cd_peigiry=RefID, price=amount, order_status='0')
                for orderitem in orderitems:
                    orderitem.order = order
                for L in lists:
                    if isinstance(L[0], ShopFilterItem):
                        L[0].stock -= L[2]
                        L[0].available = False if L[0].stock < 1 else True
                        product = update_product_stock(L[0], L[1], saving=False)
                        L[0].previous_stock = L[0].stock
                        shopfilteritems.append(L[0]), products.append(L[1])
                    else:
                        L[0].stock -= L[1]
                        L[0].available = False if L[0].stock < 1 else True
                        products.append(L[0])

                OrderItem.objects.bulk_create(orderitems)                   #bulk_create create several objects at less than or equal 3 conecting to db.
                Product.objects.bulk_update(products, ['stock', 'available'])
                ShopFilterItem.objects.bulk_update(shopfilteritems, ['stock', 'available'])
                
                message = f'عملیات با موفقیت به اتمام رسیده و خرید شما انجام شد. کد پیگیری: {RefID}'
                cart.clear()
                return Response({'message': message})

            elif result.Status == 101:
                message = 'عملیات پرداخت انجام شده است.'
                cart.clear()                                    
                return Response({'message': message, 'status': str(result.Status)})
            else:
                message = 'عمليات پرداخت ناموفق.'
                return Response({'message': message, 'status': str(result.Status)})    

        else:
            message = 'عمليات پرداخت ناموفق يا توسط کاربر لغو شده است.'
            return Response({'message': message, 'status': str(result.Status)}) 




def send_request(request):
    #return HttpResponse('')
    global amount                                       #must global
    amount = 100
    result = client.service.PaymentRequest(MERCHANT, amount, description, email, mobile, CallbackURL)
    if result.Status == 100:
        return redirect('https://sandbox.zarinpal.com/pg/StartPay/' + str(result.Authority))
    else:
        return HttpResponse('Error code: ' + str(result.Status))


def verify(request):
    #return HttpResponse('')
    cart = Cart(request)
    if request.GET.get('Status') == 'OK':
        global amount
        amount = 100#cart.get_total_prices()
        result = client.service.PaymentVerification(MERCHANT, request.GET['Authority'], amount)
        if result.Status == 100:
            return HttpResponse('success loooooooooooooooooooool')
        else:
            return HttpResponse('eroooooooooooooooooooooooooor')
            




