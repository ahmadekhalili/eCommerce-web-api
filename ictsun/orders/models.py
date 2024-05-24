from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from datetime import datetime
from phonenumber_field.modelfields import PhoneNumberField

from main.models import Product, ShopFilterItem, Town
from users.models import User
# note1: if you add or remove a field, you have to apply it in translation.py 'fields' if was required.
# note2: if you make changes in a model, you have to apply changes to it's serializers if needed.


def validate_postal_code(date):
    if len(date) != 10:
        raise ValidationError(_("10 digit postal code"))
    
class ProfileOrder(models.Model):
    user = models.ForeignKey(User, related_name='profileorders', on_delete=models.SET_NULL, null=True, verbose_name=_('user'))     # a user can have several profile_orders. for example one user create two profile_order for two different address. first for it's work orders (different address and postal code)  and second for home orders. even may you want work orders's factor print with different name than you.
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    phone = PhoneNumberField(_('phone number'))    
    town = models.ForeignKey(Town, to_field='key', on_delete=models.SET_NULL, null=True, verbose_name=_('town')) 
    address = models.CharField(_('address'), max_length=250)
    postal_code = models.CharField(_('postal code'), max_length=10, validators=[validate_postal_code])          #profile.postal_code should not be unique supose one 'motager' in its home add profile, when he change its home another 'mostager' come to this home and want add profile to this home so if postale_code was unique he cant.
    email = models.EmailField(_('email address'), blank=True, null=True)
    main = models.BooleanField(_('main profileorder'), default=False)      # can conflict with verbose_name app main
    visible = models.BooleanField(_('delete'), default=True, db_index=True)
    #profileorder_set

    class Meta:
        verbose_name = _('profile order')
        verbose_name_plural = _('profile orders')

    def __str__(self):
        first_name, last_name = self.first_name, self.last_name
        return _('profile order') + ' ' + f'{first_name}' +  ' ' + f'{last_name}'   




paid_type_choices = [('online', _('online payment')), ('cod', _('cash on delivery'))]               #important:    dont traslate online and cod it must be static because they saved in db and we do specefic task based on its value!!!    cod == cash on delivery (pardakht dar mahal che ba kart che naghdi)
order_status_choices = [('0', _('in processing')), ('1', _('delivered to post/courier')), ('2', _('delivered')), ('3', _('returned')), ('4', _('canceled'))]
class Order(models.Model):
    paid_type = models.CharField(_('paid type'), max_length=10, choices=paid_type_choices)
    paid = models.BooleanField(_('paid'), default=False)
    cd_peigiry = models.CharField(_('cd peigiry'), max_length=30, blank=True, null=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=0, blank=False, null=False)       # this price has not to translate, we want saved in history and whould be clear that in which type of price and which type of product (en product or fa) user has ordered?
    shipping_price = models.DecimalField(_('shipping price'), max_digits=10, decimal_places=0, blank=False, null=False)           #shipping_price(hazine hamlo naghl) = dispatch price(hazine ersal)  +  haqozzahme (hazine tahvil kala be post)
    shipping_type = models.CharField(_('shipping type'), max_length=20)                                                           #must be post or personal_dispatch
    order_status = models.CharField(_('order status'), max_length=1, choices=order_status_choices)
    delivery_date = models.DateTimeField(_('delivery date'), blank=True, null=True)                  #will fill auto to time order_status chenged to delivered. care about datetime field without auto_now or auto_now_add in serializing or other proccesig because this fields can be None after object creation so for example in myserializer.py should put condition like 'if delivery_date==None do_other_somthing..' or other condition for managing none value and prevent error raising.
    created = models.DateTimeField(_('created date'), auto_now_add=True)
    visible = models.BooleanField(_('delete'), default=True, db_index=True)
    profile_order = models.ForeignKey(ProfileOrder, on_delete=models.SET_NULL, null=True, verbose_name=_('profile order'))
    #items

    def delivery_date_str(self):
        return 'asasd'
    
    class Meta:
        ordering = ('-created',)
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):
        return _('order') + str(self.id)                     

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
    
    def save(self, *args, **kwargs):
        if self.order_status == '2':
            now = datetime.now()
            self.delivery_date = now
        super().save(*args, **kwargs)

    


    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name=_('order'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=0, blank=False, null=False)
    quantity = models.PositiveIntegerField(_('quantity'), blank=False, null=False)
    visible = models.BooleanField(_('delete'), default=True, db_index=True)
    shopfilteritem = models.ForeignKey(ShopFilterItem, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('shopfilteritem'))  
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('product')) #important: one of the shopfilteritem / product fields should fill. means if shopfilteritem exists fill that fill and if not fill product field.
    
    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
    
    def __str__(self):
        return _('order item') + str(self.id)  

    def get_cost(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        return self                                       #for default django in saving dont return instance but with this returned, like: OrderItem(order=order, product=p, price="44", quantity=1).save() now creted objects will return.

    '''
    def delete(self, using=None, keep_parents=False):
        raise
        print('@@@@@@@@@@@@@@@@@@@@@@@2', self)
    '''




class Shipping(models.Model):                                     #this is specefic model class(non create and del permission). we have two type Shipping, "personal" and "post" that is in one Shipping.
    fee = models.DecimalField(_('personal fee'), max_digits=10, decimal_places=0, default=0, blank=True)                #for only post shipping..
    town = models.ForeignKey(Town, to_field='key', on_delete=models.SET_NULL, null=True, verbose_name=_('town'))         #this is adderes mabda
    address = models.CharField(_('address'), max_length=250)              
    #dispatch_set
    
    class Meta:
        verbose_name = _('shipping')
        verbose_name_plural = _('shipping')                       #dont need s.
    
    def __str__(self):
        return str(_('shipping'))


class Dispatch(models.Model):                                     
    shipping_price = models.DecimalField(_('shipping price'), max_digits=10, decimal_places=0, blank=False, null=False)
    delivery_date_delay = models.CharField(_('delivery date delay'), max_length=30)
    town = models.ForeignKey(Town, to_field='key', on_delete=models.SET_NULL, null=True, verbose_name=_('town'))     #this is adress maghsad that admin can send to that.
    shipping = models.ForeignKey(Shipping, on_delete=models.CASCADE, verbose_name=_('shipping'))
    
    class Meta:
        verbose_name = _('Personal Dispatch')
        verbose_name_plural = _('Personal Dispatch')                       
    
    def __str__(self):
        return _('Dispatch') + ' ' + self.town.name
