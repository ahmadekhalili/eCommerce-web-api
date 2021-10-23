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

CallbackURL = 'http://192.168.114.21:8000/payment/verify/'#Important: need to edit for realy server.


class PaymentStart(views.APIView):
    def post(self, request, *args, **kwargs):
        total_prices = args[0]
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
        global amount
        cart = Cart(request)

        if request.GET.get('Status') == 'OK':
            global amount
            products, shopfilteritems = [], []
            order = Order.objects.get(id=cart.session['order_id'])            
            amount = order.price
            result = client.service.PaymentVerification(MERCHANT, request.GET['Authority'], amount)
            if result.Status == 100:
                RefID = result.RefID
                order.paid, order.cd_peigiry = True, RefID
                order = order.save()
                orderitems = OrderItem.objects.filter(id__in=cart.session['orderitem_ids'])
                for orderitem in orderitems:
                    if orderitem.shopfilteritem:
                        orderitem.shopfilteritem.stock -= orderitem.quantity                                         #important: .update is completly seperate method from .save and dont run .save so we need update availabe too. reference: https://stackoverflow.com/questions/33809060/django-update-doesnt-call-override-save
                        orderitem.shopfilteritem.available = False if orderitem.shopfilteritem.stock < 1 else True
                        product = update_product_stock(orderitem.shopfilteritem, orderitem.product, saving=False)
                        orderitem.shopfilteritem.previous_stock = orderitem.shopfilteritem.stock
                        shopfilteritems.append(orderitem.shopfilteritem), products.append(orderitem.product)                    
                    else:
                        orderitem.product.stock -= orderitem.quantity
                        orderitem.product.available = False if orderitem.product.stock < 1 else True
                        products.append(orderitem.product)
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
            




