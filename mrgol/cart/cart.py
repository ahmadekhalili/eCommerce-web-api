from django.conf import settings
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.contrib.sessions.backends.db import SessionStore

import ast

from .models import SesKey
from main.models import Product, Filter, ShopFilterItem
from .myserializers import CartProductSerializer

class Cart(object):

    def __init__(self, request):
        self.request = request
        self.cart_page = False
        unauth_cart = {}
        if self.request.user.is_authenticated:
            unauth_cart, request.session[settings.CART_SESSION_ID] = (request.session[settings.CART_SESSION_ID], {}) if request.session.get(settings.CART_SESSION_ID) else ({}, {})               # cart value of unauthenticate user should assing to authenticate user session, but for next calls of Cart (like cart = Cart(request)) request.session[settings.CART_SESSION_ID] shoud clear
            ob = SesKey.objects.get(user=self.request.user)     #SesKey created with post_save signal.
            self.session = SessionStore(session_key=ob.ses_key)       
        else:
            self.session = request.session
        cart = self.session._get_session(no_load=False).get(settings.CART_SESSION_ID, {})   #if our cart is blank (self.session['cart'] was blank) dont return None because it will raise error in self.cart.get(...) error: None type has not get method!!!!
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}  #eny changing self.session will affect request.sessio(mutable)
            self.session.modified = False 
        self.cart = cart
        if unauth_cart.keys():
            [self.add(key, unauth_cart[key]['quantity']) for key in unauth_cart]
            
    def add(self, product_id, quantity=1, shopfilteritem_id=None):             #product_id should be str(it can be int if for example in django rest api clint send like {"prodict_id":1} instead  {"prodict_id":"1"}
        quantity = int(quantity)
        item = get_object_or_404(ShopFilterItem, id=shopfilteritem_id) if shopfilteritem_id else get_object_or_404(Product, id=product_id) #selected_ShopFilterItems_ids = [request.POST.get('name') for name in Filter.objects.filter(selling=True).values_list('name', flat=True) if name in request.POST and request.POST.get('name')]     
        quantity = self.cart.get(product_id, {}).get('quantity', 0) + quantity
        if quantity <= item.stock:                             #note if quantity > item.stock we dont need do enything because it done in __iter__
            if product_id not in self.cart:
                self.cart[product_id] = {'quantity': quantity, 'price': str(item.price), 'old_price': str(item.price), 'shopfilteritem_id': shopfilteritem_id}        #if item.price was decimal raise json serializer error(because session only can save str)               
            else:
                self.cart[product_id] = {'quantity': quantity, 'price': str(item.price), 'old_price': self.cart[product_id]['old_price'], 'shopfilteritem_id': shopfilteritem_id}     #important: we must not update old_price to current price "chon hata ba ezafe kardane kalaii ba qeimat taqir yafte moshkeli nist chon beharhal baraie namaiesh kalahaie sabad baiad be __ietr__ beravad barname var dar anja error taqir qeimat tolid va old_price be qeimat jadid update mishvad. ta dobare error namaiesh nadahad!"        
            self.save()

    def minus(self, product_id, shopfilteritem_id=None):             #product_id should be str
        item = get_object_or_404(ShopFilterItem, id=shopfilteritem_id) if shopfilteritem_id else get_object_or_404(Product, id=product_id)
        if product_id in self.cart:
            if self.cart[product_id]['quantity'] >= 1:
                self.cart[product_id]['quantity'] -= 1
                self.save()
            else:
                self.remove(product_id)
                
    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart                      #if self.session is authentication session, modify-save will done here.                                         
        self.session.save()                                                     #in removing for unauthenticated user dont remove that product from request.session without self.session.save()!   and also for authenticated_user self.session is cart session and need .save for saving
        
    def remove(self, product_id):                                               #product_id should be str
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):        
        product_ids, shopfilteritem_ids =  self.cart.keys(), [self.cart[key]['shopfilteritem_id'] for key in self.cart if self.cart[key]['shopfilteritem_id']]
        ids_products = dict([(str(product.id), product) for product in Product.objects.filter(id__in=product_ids)])          #this is like: {'1': product_1, '2': product_2}   note ids of product_ids can be str
        ids_shopfilteritems = dict([(str(shopfilteritem.product_id), shopfilteritem) for shopfilteritem in ShopFilterItem.objects.filter(id__in=shopfilteritem_ids)])  #ids_products key type should be same with ids_shopfilteritems key type.
        for id in product_ids:
            item = self.cart[id].copy()              #item = self.cart[key] is mutable so every change in item, affect self.cart and self.session and self.request!!!!
            item['product'] = ids_products.get(id)   #supose you have product_ids = [1,2]  supose admin delete product(1) so ids_products should be like:  [product(2)] so ids_products.get(1) = None, if we hanle it like this only deleted product will desapire in "sabad" of user but if we dont handle it and raise error in our program, all items of "sabad" will disapier.
            if item['product']:
                item['shopfilteritem'] = ids_shopfilteritems.get(id)
                item['price'] = item['shopfilteritem'].price if item['shopfilteritem'] else item['product'].price        #django_rest framework convert decimal to str so we convert to str not int!           
                price_changes = item['price'] - Decimal(item['old_price']) 
                item['price_changes'] = price_changes if price_changes>=0 else price_changes*(-1)
                item['lach_quantity'] = item['quantity']-item['shopfilteritem'].stock  if item['shopfilteritem'] and item['quantity']>item['shopfilteritem'].stock else item['quantity']-item['product'].stock if not item['shopfilteritem'] and item['quantity']>item['product'].stock else 0
                self.cart[id]['quantity'] = item['quantity']-item['lach_quantity'] if self.cart_page else self.cart[id]['quantity']
                self.cart[id]['price'] = str(item['price'])               #if self.cart[id]['price'] dont update to current price, with changing product.price in admin panel price in cart dont change at all.  
                self.cart[id]['old_price'] = self.cart[id]['price'] if self.cart_page else self.cart[id]['old_price']                    #self.cart[id]['old_price'] sohuld update to current price only if user visited cart page
                item['total_price'] = item['price'] * item['quantity']
                yield item
        self.save()

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_products_count(self):
        return len(self.cart.values())      #self.cart.values() is like: [{'quantity': 3, 'price': '1000'},  {'quantity': 1, 'price': '3000'}]

    def get_total_prices(self):
        return sum(item['total_price'] for item in self)

    def clear(self):                                                    #important: cart.clear work after .add for example supose you have:  cart.clear()  next run cart.add(product_id=data['product_id'], ...)  cart.clear dont ward!!!
        self.session[settings.CART_SESSION_ID] = {}
        self.session['personal_shipping_price'] = ''
        self.session['post_shipping_price'] = ''
        self.session['profile_order_id'] = ''
        self.session['order_id'] = ''
        self.session['orderitem_ids'] = None
        self.session.save()
        


        
