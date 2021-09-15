from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from main.models import Product
from users.models import User


def validate_postal_code(date):
    if len(date) != 10:
        raise ValidationError(_("10 digit postal code"))
    
class ProfileOrder(models.Model):
    user = models.ForeignKey(User, related_name='profileorders', on_delete=models.SET_NULL, null=True, verbose_name=_('user'))
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    phone = PhoneNumberField(_('phone number'))    
    email = models.EmailField(_('email address'))
    address = models.CharField(_('address'), max_length=250)
    postal_code = models.CharField(_('postal code'), max_length=20, validators=[validate_postal_code], unique=True, db_index=False)
    main = models.BooleanField(_('main profileorder'), default=False)      #car conflict with verbose_name app main.
    visible = models.BooleanField(_('delete'), default=True, db_index=True)
    #profileorder_set

    class Meta:
        verbose_name = _('profile order')
        verbose_name_plural = _('profile orders')

    def __str__(self):
        first_name, last_name = self.first_name, self.last_name
        return _('profile order') + ' ' + f'{first_name}' +  ' ' + f'{last_name}'   


paid_type_choices = [('online', _('online payment')), ('cod', _('cash on delivery'))]               #important:    dont traslate online and cod it must be static because they saved in db and we do specefic task based on its value!!!    cod == cash on delivery (pardakht dar mahal che ba kart che naghdi)
order_status_choices = [('0', _('in processing')), ('1', _('delivered')), ('2', _('returned')), ('3', _('canceled'))]
class Order(models.Model):
    paid_type = models.CharField(_('paid type'), max_length=10, choices=paid_type_choices)
    paid = models.BooleanField(_('paid'), default=False)
    cd_peigiry = models.CharField(_('cd peigiry'), max_length=30, blank=True, null=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=0, blank=False, null=False)
    order_status = models.CharField(_('order status'), max_length=1, choices=order_status_choices)  
    created = models.DateTimeField(_('created'), auto_now_add=True)
    visible = models.BooleanField(_('delete'), default=True, db_index=True)
    profile_order = models.ForeignKey(ProfileOrder, on_delete=models.SET_NULL, null=True, verbose_name=_('profile order'))
    #items
    
    class Meta:
        ordering = ('-created',)
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):
        return _('order') + str(self.id)                    #why i dont used like   

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())



    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name=_('order'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=0, blank=False, null=False)
    quantity = models.PositiveIntegerField(_('quantity'), blank=False, null=False)
    visible = models.BooleanField(_('delete'), default=True, db_index=True)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('product'))
    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
    
    def __str__(self):
        return _('order item') + str(self.id)  

    def get_cost(self):
        return self.price * self.quantity   

    '''
    def delete(self, using=None, keep_parents=False):
        raise
        print('@@@@@@@@@@@@@@@@@@@@@@@2', self)
    '''
'''
#order has paid, means after completing every buying process  <order object>.paid should be True (customer paided), so for every buying we must create an order (to show us that buy has paided or not!) but problem is:
#in Order, instead of saving address, name, address, postal_code.... of Order in database in every buying , (that this fields is same in every Order) we implement this fields on OrderProfle so because of that,    address, name, postal_code .... just saved in database in limited number(for example <OrderProfile (1)>) and for every order we created for example Order1, Order2, Order4.. we just referec to OrderProfile1 and so we just create one time this fields(address, name..) in multiple Orders.
create, update, paid must explicity defind for Order
'''
