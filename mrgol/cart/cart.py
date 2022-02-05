from django.conf import settings
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.contrib.sessions.backends.db import SessionStore

import ast
from datetime import datetime

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
            ob = SesKey.objects.get(user=self.request.user)     # SesKey created with post_save signal.
            self.session = SessionStore(session_key=ob.ses_key)
            if not self.session._get_session_from_db() or self.session._get_session_from_db().expire_date < datetime.now():            # if you make a session exipired by session model(contrib.session.models Session) session will expire and its ._get_session_from_db() will return None like cart = Cart(request) s = Session.objects.get(pk=cart.session.session_key)  s.expire_date = datetime(1900, 1, 1)  s.save()   now cart.session._get_session_from_db() will return None and cart.session exipired
                self.session.clear_expired()
                self.session.create()
                ob.ses_key = self.session.session_key
                ob.save()
        else:
            self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID, {})
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}  # eny changing self.session will affect request.sessio(mutable)
            self.session.modified = False 
        self.cart = cart
        if unauth_cart:                                         # after login user previous cart values should put to new session, here done it
            for product_id in unauth_cart:
                if self.is_nested_dict(unauth_cart, product_id):
                    for shopfilteritem_id in unauth_cart[product_id]:
                        self.add(product_id, unauth_cart[product_id][shopfilteritem_id]['quantity'], shopfilteritem_id)
                else:
                    self.add(product_id, unauth_cart[product_id]['quantity'])

    def get_cart_item(self, product_id, shopfilteritem_id=None):              # note: if you make index on get_cart_item() you can ust it as set func, for example: self.get_cart_item(1, None)['quantity'] = 10 this is acceptable, but self.get_cart_item(1, None) = {...} is error and should use set_cart_item in that case
        if shopfilteritem_id:
            return self.cart.get(product_id, {}).get(shopfilteritem_id, {})
        else:
            return self.cart.get(product_id, {})

    def set_cart_item(self, value, product_id, shopfilteritem_id=None):
        if shopfilteritem_id:
            self.cart[product_id][shopfilteritem_id] = value
        else:
            self.cart[product_id] = value

    def del_cart_item(self, product_id, shopfilteritem_id=None):
        if shopfilteritem_id:
            del self.cart[product_id][shopfilteritem_id]
            if not self.cart[product_id]:                                      # supose self.cart = {9: {4: {'quantity': 1, ...}}} after running del self.cart[product_id][shopfilteritem_id]  self.cart = {9: {}} 
                del self.cart[product_id]
        else:
            del self.cart[product_id]

    def is_nested_dict(self, cart, product_id):                                # check we have nested dict in cart[product_id] or not for example self.cart[1] = {'quantity': quantity, 'price': ...} is dict level 1 (not nested) but self.cart[1] = {2: {'quantity': quantity, 'price': ...}} is dict level 2 (nested)
        return type(list(cart[product_id].keys())[0]) == int

    def add(self, product_id, quantity=1, shopfilteritem_id=None):             # product_id (or shopfilteritem_id dont different) shoud be int, product_id type is important in __iter__  (in __ter__ ids type in product_ids var should be same with ids in ids_products var)
        quantity = int(quantity)
        item = get_object_or_404(ShopFilterItem, id=shopfilteritem_id) if shopfilteritem_id else get_object_or_404(Product, id=product_id)
        quantity = self.get_cart_item(product_id, shopfilteritem_id).get('quantity', 0) + quantity
        if quantity <= item.stock:                                             # note if quantity > item.stock we dont need do enything because it done in __iter__
            if product_id not in self.cart:                                    # important: we must not update old_price to current price "chon hata ba ezafe kardane kalaii ba qeimat taqir yafte moshkeli nist chon beharhal baraie namaiesh kalahaie sabad baiad be __ietr__ beravad barname var dar anja error taqir qeimat tolid va old_price be qeimat jadid update mishvad. ta dobare error namaiesh nadahad!"
                if shopfilteritem_id:
                    self.cart[product_id] = {shopfilteritem_id: {'quantity': quantity, 'price': str(item.price), 'old_price': str(item.price)}}
                else:
                    self.cart[product_id] = {'quantity': quantity, 'price': str(item.price), 'old_price': str(item.price)}
            else:
                value = {'quantity': quantity, 'price': str(item.price), 'old_price': str(item.price)} if not self.cart[product_id].get(shopfilteritem_id) else {'quantity': quantity, 'price': str(item.price), 'old_price': self.get_cart_item(product_id, shopfilteritem_id)['old_price']}# else means "if product_id in self.cart or shopfilteritem_id in self.cart[product_id]"
                self.set_cart_item(value, product_id, shopfilteritem_id)
            self.save()       # self.cart is like: {1: {'quantity': 1, 'price': '1000', 'old_price': '1000'}, 2: {1: {'quantity': 1, 'price': '2000', 'old_price': '2000'}, 2: {'quantity': 1, 'price': '3000', 'old_price': '3000'}}

    def minus(self, product_id, shopfilteritem_id=None):                       # product_id should be same type you added in first to cart
        item = get_object_or_404(ShopFilterItem, id=shopfilteritem_id) if shopfilteritem_id else get_object_or_404(Product, id=product_id)
        if product_id in self.cart:
            if self.get_cart_item(product_id, shopfilteritem_id)['quantity'] >= 1:
                self.get_cart_item(product_id, shopfilteritem_id)['quantity'] -= 1
                self.save()
            if self.get_cart_item(product_id, shopfilteritem_id)['quantity'] < 1:
                self.remove(product_id, shopfilteritem_id)

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart                      # if self.session is authentication session, modify-save will done here.                                         
        self.session.save()                                                     # in removing for unauthenticated user dont remove that product from request.session without self.session.save()!   and also for authenticated_user self.session is cart session and need .save for saving

    def remove(self, product_id, shopfilteritem_id=None):
        self.del_cart_item(product_id, shopfilteritem_id)
        self.save()

    def __iter__(self):                                   # important: supose for item in cart: cart is like: [{'quantity': 2, 'price': 1, 'old_price': '1', 'product': product(1), 'shopfilteritem': None, 'price_changes': 0, 'lach_quantity': 0, 'total_price': 2}, {'quantity': 2, 'price': 10, 'old_price': '10', 'product': product(2), 'shopfilteritem': shopfilteritem(1), 'price_changes': 0, 'lach_quantity': 0, 'total_price': 2}]
        product_ids, shopfilteritem_ids =  self.cart.keys(), [key2 for key in self.cart if self.is_nested_dict(self.cart, key) for key2 in self.cart[key]]
        ids_products = dict([(product.id, product) for product in Product.objects.filter(id__in=product_ids)])          #this is like: {'1': product_1, '2': product_2}   note ids of product_ids can be str
        ids_shopfilteritems = dict([(shopfilteritem.id, shopfilteritem) for shopfilteritem in ShopFilterItem.objects.filter(id__in=shopfilteritem_ids)])  #ids_products key type should be same with ids_shopfilteritems key type.
        for id in product_ids:
            item, mutable_item = self.cart[id].copy(), self.cart[id]                        # item = self.cart[key] is mutable so every change in item, affect self.cart and self.session and self.request!!!!
            item['product'] = ids_products.get(id)        # supose you have product_ids = [1,2]  supose admin delete product(1) so ids_products should be like:  {'2': product(2)} so ids_products.get(1) = None, if we hanle it like this only deleted product will desapire in "sabad" of user but if we dont handle it and raise error in our program, all items of "sabad" will disapier.
            if item['product']:
                loop = list(self.cart[id].keys()) if self.is_nested_dict(self.cart, id) else ['one']                         # list(self.cart[id].keys())[0]) is like 1 when in cart we added a shopfilteritem but when in cart we added a product is like 'quantity'
                for shopfilteritem_id in loop:                                                                               # should loop one time if we have not shopfilteritem
                    if self.is_nested_dict(self.cart, id):
                        item, mutable_item = self.cart[id][shopfilteritem_id].copy(), self.cart[id][shopfilteritem_id]
                    item['shopfilteritem'] = ids_shopfilteritems.get(shopfilteritem_id)
                    item['price'] = item['shopfilteritem'].price if item['shopfilteritem'] else item['product'].price        # django_rest framework convert decimal to str so we convert to str not int!           
                    item['price_changes'] = item['price'] - Decimal(item['old_price'])                                       # price_changes should support posetive and negative numbers, means if price_changes was positive front should display message like: "gheimat aqlam price_changes afzesh yaft" or if was negative: "gheimat aqlam price_changes kahesh yaft"
                    item['lach_quantity'] = item['quantity']-item['shopfilteritem'].stock  if item['shopfilteritem'] and item['quantity']>item['shopfilteritem'].stock else item['quantity']-item['product'].stock if not item['shopfilteritem'] and item['quantity']>item['product'].stock else 0       # lach_quantity fill when item.stock decreased by admin
                    mutable_item['quantity'] = item['quantity'] = item['quantity']-item['lach_quantity'] if self.cart_page else item['quantity']          # mutable_item is somthing that saved in db and item is somthing shown to user in sabad(by "yield item) so we want update both of them
                    mutable_item['price'] = str(item['price'])              # if self.cart[id]['price'] dont update to current price, with changing product.price in admin panel price in cart dont change at all.  
                    mutable_item['old_price'] = item['old_price'] = mutable_item['price'] if self.cart_page else mutable_item['old_price']                       # self.cart[id]['old_price'] sohuld update to current price only if user visited cart page
                    item['total_price'] = item['price'] * item['quantity']
                    yield item
        self.save()

    def __len__(self):
        quantities = 0
        for product_id in self.cart:
            if is_nested_dict(self.cart, product_id):
                for shopfilteritem_id in self.cart[product_id]:
                    quantities += self.cart[product_id][shopfilteritem_id]['quantity']
            else:
                quantities += self.cart[product_id]['quantity']
        return quantities

    def get_products_count(self):                        # we didnt use 'for item in cart' because it use database query and is not optimal
        counter = 0
        for product_id in self.cart:
            if is_nested_dict(self.cart, product_id):
                for shopfilteritem_id in self.cart[product_id]:
                    counter += 1
            else:
                counter += 1
        return counter

    def get_total_prices(self):
        return sum(item['total_price'] for item in self)

    def clear(self):                                                       # important: cart.clear work after .add for example supose you have:  cart.clear()  next run cart.add(product_id=data['product_id'], ...)  cart.clear dont ward!!!
        self.session[settings.CART_SESSION_ID] = {}
        self.session['personal_shipping_price'] = ''
        self.session['post_shipping_price'] = ''
        self.session['profile_order_id'] = ''
        self.session['order_id'] = ''
        self.session['orderitem_ids'] = None
        self.session.save()
