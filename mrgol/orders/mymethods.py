from main.mymethods import PostDispatchPrice
from cart.views import CartMenuView
from cart.cart import Cart
from .models import ProfileOrder, Shipping


def profile_order_detail(request, pk):
    profileorder = ProfileOrder.objects.filter(id=pk).select_related('town__state')[0]
    cart_menu = CartMenuView().get(request).data
    if not cart_menu['sabad']:
        return None
    cart = Cart(request)
    shipping = Shipping.objects.first()
    post_price = PostDispatchPrice(cart_menu['total_weight'],  cart_menu['dimensions']).get_price(shipping.town.state.key, shipping.town.key, profileorder.town.state.key, profileorder.town.key)
    # note: post_price can be decimal or str (when post website, return error instead price post_price is str) like: post_price = 'ارسال مرسوله با توجه به شرایط انتخابی و نرخنامه پستی امکان پذیر نمی باشد'
    post_price += shipping.fee if type(post_price) != str else ''                       # we didn't import additional class decimal
    for dispatch in shipping.dispatch_set.all():
        if dispatch.town == profileorder.town:
            cart.session['personal_shipping_price'], cart.session['post_shipping_price'] = str(dispatch.shipping_price), str(post_price)               #personal_shipping_price and post_shipping_price uses in ListCreateOrderItem.post for creating order
            cart.save()
            return {'profileorder_selected': profileorder.id, 'personal_dispatch': {'price': dispatch.shipping_price, 'delivery_date': dispatch.delivery_date_delay}, 'post_price': post_price}
            
    cart.session['personal_shipping_price'], cart.session['post_shipping_price'] = None, str(post_price)
    cart.save()                
    return {'profileorder_selected': profileorder.id, 'post_price': post_price}        #profileorder_selected is for what? answer: front know whitch checkbox should be selected after profileorder creation(after coming from ListCreateProfileOrder.post to .get) 
