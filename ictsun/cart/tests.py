from django.test import TestCase
from django.conf import settings
from django.contrib.auth import login, logout
from django.test.client import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

import time
from datetime import datetime
from decimal import Decimal

from main.models import Product, ShopFilterItem
from users.models import User
from .models import SesKey
from .cart import Cart


class CartTestCase(TestCase):                             # note: ShopFilterItemCartTestCase use this class and run its methods, so in using cart methods like cart.add or cart.remove you should provide shopfilteritem_id argument
    def setUp(self):                                      # session and other models create in test will remove after test ended, because test create its own db and delete it after test ends
        request = RequestFactory().get('/cart/add/')      # we should add session and user to request if creating request handy, reference: https://docs.djangoproject.com/en/4.0/topics/testing/advanced/#django.test.RequestFactory
        request.session = SessionStore()
        request.session.create()
        request.user = AnonymousUser()                    # if you dont put this, request.user will not fill after login and as unauthenticated user calling Cart(self.request) will raise error if request.user be like None
        self.request = request
        self.user = User.objects.create_user(phone='09147761266', password='a13431343')

    def _create_item(self, **kwargs):
        return {'product_id': str(Product.objects.create(**kwargs).id), 'shopfilteritem_id': None}

    def _get_cart_session_item(self, cart, item):
        return cart.session[settings.CART_SESSION_ID].get(item['product_id'], {})

    #login and logout done in LoginCartTestCase and ... classes
    def _login(self, request, user):
        return Cart(request)

    def _finalize_test(self, cart, request):
        cart.clear()
        if request.user.is_authenticated:
            logout(request)
        self.assertEqual(cart.session[settings.CART_SESSION_ID], {})        

    def test_add_to_session(self):
        """Here we add item1 product in unauthenticated and add item2 in authenticated state and check item1 and item2 added correctly or not"""
        item1, item2 = self._create_item(name='test1', stock=1), self._create_item(name='test2', stock=1)
        cart = Cart(self.request)
        # cart.session[settings.CART_SESSION_ID] should be blank {}
        self.assertEqual(cart.session[settings.CART_SESSION_ID], {})
        
        cart.add(item1['product_id'], quantity=1, shopfilteritem_id=item1['shopfilteritem_id'])
        # second add should not accept, because stock=0
        cart.add(item1['product_id'], quantity=1, shopfilteritem_id=item1['shopfilteritem_id'])
        self.assertEqual(self._get_cart_session_item(cart, item1), {'quantity': 1, 'price': '0.00', 'old_price': '0.00'})

        login(self.request, self.user)
        cart = Cart(self.request)
        cart.add(item2['product_id'], quantity=1, shopfilteritem_id=item2['shopfilteritem_id'])
        # test we have item1 1, 2
        self.assertEqual(list(cart.session[settings.CART_SESSION_ID].keys()), [item1['product_id'], item2['product_id']])

        # cart should be clear and logout after test ends
        self._finalize_test(cart, self.request)

    def test_minus_remove_session(self):
        # item1 id can be like 3 why? because every method create its own item, even if you create proucts in setUp() every method call SetUp() seperatly so item with different ids will be created
        item1 = self._create_item(name='test1', stock=2)
        cart = self._login(self.request, self.user)
        # cart.session[settings.CART_SESSION_ID] should be blank {}
        self.assertEqual(cart.session[settings.CART_SESSION_ID], {})

        cart.add(item1['product_id'], quantity=2, shopfilteritem_id=item1['shopfilteritem_id'])
        cart.minus(item1['product_id'], shopfilteritem_id=item1['shopfilteritem_id'])
        self.assertEqual(self._get_cart_session_item(cart, item1)['quantity'], 1)
        cart.minus(item1['product_id'], shopfilteritem_id=item1['shopfilteritem_id'])
        self.assertEqual(cart.session[settings.CART_SESSION_ID], {})
        # calling minus on blank cart should not raise error
        cart.minus(item1['product_id'], shopfilteritem_id=item1['shopfilteritem_id'])

        cart.add(item1['product_id'], quantity=1, shopfilteritem_id=item1['shopfilteritem_id'])
        cart.remove(item1['product_id'])
        self.assertEqual(cart.session[settings.CART_SESSION_ID], {})

        self._finalize_test(cart, self.request)

    def test_session_expiration(self):
        """first test session expiration when user loged out (test request.session)"""
        item1 = self._create_item(name='test1', stock=1)
        cart = self._login(self.request, self.user)
        # make sure cart is blank and dont initialed by previouse test methods
        self.assertEqual(cart.session[settings.CART_SESSION_ID], {})

        s = Session.objects.get(pk=cart.session.session_key)
        s.expire_date = datetime.now()
        s.save()
        time.sleep(1)
        # test session exipired succesfuly
        self.assertEqual(cart.session._get_session_from_db(), None)
        # here after calling Cart(self.request) new session should created instead expired session
        cart = Cart(self.request)
        cart.add(item1['product_id'], quantity=1, shopfilteritem_id=item1['shopfilteritem_id'])
        # item1 should added to cart sucessfuly
        self.assertTrue(self._get_cart_session_item(cart, item1))

        self._finalize_test(cart, self.request)

    def test_cart_iter(self):
        """item (in for item in cart) has 8 attribute: quantity, price, old_price, product, shopfilteritem, price_changes, lach_quantity, total_price we shoud check them work correctly"""
        product1, product2, product3 = Product.objects.create(name='test1', price=10000, stock=10), Product.objects.create(name='test2'), Product.objects.create(name='test3', price=20000, stock=1)
        shop_filter1, shop_filter2 = ShopFilterItem.objects.create(product=product2, stock=10, price=86945056), ShopFilterItem.objects.create(product=product2, stock=1, price=10000)
        cart = self._login(self.request, self.user)

        cart.add(product1.id, quantity=7)
        cart.add(shop_filter1.product.id, quantity=7, shopfilteritem_id=shop_filter1.id)
        cart.add(shop_filter2.product.id, quantity=1, shopfilteritem_id=shop_filter2.id)
        cart.add(product3.id, quantity=1)

        # test old_price price_changes ----------------------------------
        # change product2.price to make sure dont affect on its shopfilteritems prices (shop_filter1, shop_filter2)
        cart.cart_page = True
        product1.price, product2.price, shop_filter1.price = 11000, 10000, 86944056
        for item in [product1, product2, shop_filter1]: item.save()
        # loop over cart like "for item in cart"
        items = list(iter(cart))
        # product1 price increased 1000, shop_filter1 decreased 1000
        # items[0]['price_changes'] == Decimal('1000.00') == Decimal('1000') and hasn't difference
        self.assertEqual(items[0]['price_changes'], Decimal(1000))
        self.assertEqual(items[1]['price_changes'], Decimal(-1000))
        # when cart_page = True, after loop over cart, "old_price in session" == "old_price in cart" == "current price"
        self.assertTrue(items[0]['old_price'] == cart.session[settings.CART_SESSION_ID][str(product1.id)]['old_price'] == '11000.00')
        self.assertTrue(items[1]['old_price'] == cart.session[settings.CART_SESSION_ID][str(shop_filter1.product.id)][str(shop_filter1.id)]['old_price'] == '86944056.00')
        items = list(iter(cart))
        # "price_changes" should be 0
        self.assertEqual(items[0]['price_changes'], Decimal(0))
        self.assertEqual(items[1]['price_changes'], Decimal(0))
        # change price again! so with updating old_price price_changes copute should be like: items[0]['price_changes'] = 12000 - 11000, not like 12000 - 10000
        product1.price, shop_filter1.price = 12000, 86943056
        for item in [product1, product2, shop_filter1]: item.save()
        items = list(iter(cart))
        self.assertEqual(items[0]['price_changes'], Decimal(1000))
        self.assertEqual(items[1]['price_changes'], Decimal(-1000))

        cart.cart_page = False
        product1.price, shop_filter1.price = 14000, 86941056
        for item in [product1, shop_filter1]: item.save()
        items = list(iter(cart))
        # product1 price increased 2000, shop_filter1 decreased 2000
        self.assertEqual(items[0]['price_changes'], Decimal(2000))
        self.assertEqual(items[1]['price_changes'], Decimal(-2000))
        items = list(iter(cart))
        # "price_changes" should not change
        self.assertEqual(items[0]['price_changes'], Decimal(2000))
        self.assertEqual(items[1]['price_changes'], Decimal(-2000))
        # change price again! so without updating old_price price_changes compute should be like: items[0]['price_changes'] = 15000 - 12000, not like: 150000 - 14000
        product1.price, shop_filter1.price = 15000, 86940056
        for item in [product1, product2, shop_filter1]: item.save()
        items = list(iter(cart))
        self.assertEqual(items[0]['price_changes'], Decimal(3000))
        self.assertEqual(items[1]['price_changes'], Decimal(-3000))

        # test quantity and lach_quantity ----------------------------------
        product1.stock = 6
        shop_filter1.stock = 5
        product1.save()
        shop_filter1.save()
        cart.cart_page = False
        items = list(iter(cart))
        # lach_quantity of product1 is 1 and lach_quantity of shop_filter1 is 2
        self.assertEqual(items[0]['lach_quantity'], 1)
        self.assertEqual(items[1]['lach_quantity'], 2)
        # when cart_page is False quantity should be current quantity
        self.assertTrue(items[0]['quantity'] == cart.session[settings.CART_SESSION_ID][str(product1.id)]['quantity'] == 7)
        self.assertTrue(items[1]['quantity'] == cart.session[settings.CART_SESSION_ID][str(shop_filter1.product.id)][str(shop_filter1.id)]['quantity'] == 7)
        cart.cart_page = True
        items = list(iter(cart))
        # when cart_page is True quantity should be stock of its item
        self.assertTrue(items[0]['quantity'] == cart.session[settings.CART_SESSION_ID][str(product1.id)]['quantity'] == 6)
        self.assertTrue(items[1]['quantity'] == cart.session[settings.CART_SESSION_ID][str(shop_filter1.product.id)][str(shop_filter1.id)]['quantity'] == 5)

        self._finalize_test(cart, self.request)


class LoginCartTestCase(CartTestCase):                        #repeat CartTestCase tests with loged in user
    def _login(self, request, user):
        login(self.request, self.user)
        return Cart(request)

    # tests done in CartTestCase as login and logout states so dont need be here
    def test_add_to_session(self):
        pass


class ShopFilterItemCartTestCase(CartTestCase):               #repeat CartTestCase tests with create ShopFilterItem istead product

    def _create_item(self, **kwargs):
        p = Product.objects.create(**kwargs)
        return {'product_id': str(p.id), 'shopfilteritem_id': str(ShopFilterItem.objects.create(product=p, stock=kwargs['stock'], price=0).id)}

    def _get_cart_session_item(self, cart, item):
        return cart.session[settings.CART_SESSION_ID].get(item['product_id'], {}).get(item['shopfilteritem_id'])

    # tests done in CartTestCase.test_cart_iter with product and shopfilteritem both, so dont need to here
    def test_cart_iter(self):
        pass


class LoginShopFilterItemCartTestCase(CartTestCase):         #repeat CartTestCase tests with create ShopFilterItem istead product and loged int user

    def _login(self, request, user):
        login(self.request, self.user)
        return Cart(request)

    # tests done in CartTestCase as login and logout states so dont need be here
    def test_add_to_session(self):
        pass

    def _create_item(self, **kwargs):
        p = Product.objects.create(**kwargs)
        return {'product_id': str(p.id), 'shopfilteritem_id': str(ShopFilterItem.objects.create(product=p, stock=kwargs['stock'], price=0).id)}

    def _get_cart_session_item(self, cart, item):
        return cart.session[settings.CART_SESSION_ID].get(item['product_id'], {}).get(item['shopfilteritem_id'])

    def test_cart_iter(self):
        pass
