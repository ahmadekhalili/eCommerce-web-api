from django.contrib import admin
from django.contrib import messages
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from users.mymethods import user_name_shown
from .models import ProfileOrder, Order, OrderItem


class OrderItemFormSet(BaseInlineFormSet):
    def delete_existing(self, obj, commit=True):          #for controling deletion of inlines we should use method delete_existing i found it ez by returning an "raise" in OrderItem.delete(self, using=None, keep_parents=False) method and when delete and orderitem in admin order page django trace error page will shown and i found method delete_existing
        if commit:
            obj.visible = False
            obj.save()
            
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    formset = OrderItemFormSet                            #django create its formset from this.
    raw_id_fields = ['product']

    '''
    def delete_model(self, request, obj):                 #this dont work in inlines we must use delete_existing
        obj.visible = False
        obj.save()
    '''        
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'paid_type', 'paid', 'cd_peigiry']
    list_filter = ['profile_order', 'paid', 'created']
    readonly_fields = ('created', 'firstlast_name_account', 'firstlast_name_order', 'phone', 'email', 'address', 'postal_code', 'order_status')
    inlines = [OrderItemInline]
    fieldsets = (
        (_('address'), {
            'classes': ('collapse',),
            'fields': ('firstlast_name_account', 'firstlast_name_order', 'phone', 'email', 'address', 'postal_code'),
        }),
        (None, {
            'fields': ('profile_order', 'paid_type', 'paid', 'cd_peigiry', 'price', 'order_status', 'created')
        }),

    )
    
    def firstlast_name_account(self, obj):                         #how put method in fieldset? (normaly like in list_display cant) here i did this link orders: https://stackoverflow.com/questions/14777989/how-do-i-call-a-model-method-in-django-modeladmin-fieldsets
        return user_name_shown(obj.profile_order.user)
    firstlast_name_account.allow_tags = True
    firstlast_name_account.short_description = _('first/last name')
    def firstlast_name_order(self, obj):
        return '{} {}'.format(obj.profile_order.first_name, obj.profile_order.last_name)
    firstlast_name_order.allow_tags = True
    firstlast_name_order.short_description = _('ordered with name')
    def phone(self, obj):
        return obj.profile_order.phone
    phone.allow_tags = True
    phone.short_description = _('phone number')
    def email(self, obj):
        return obj.profile_order.email
    email.allow_tags = True
    email.short_description = _('email address')
    def address(self, obj):
        return obj.profile_order.address
    address.allow_tags = True
    address.short_description = _('address')
    def postal_code(self, obj):
        return obj.profile_order.postal_code
    postal_code.allow_tags = True
    postal_code.short_description = _('postal code')
    
    def delete_model(self, request, obj):
        obj.visible = False
        obj.save()
    '''
    def message_user(self, request, message, level=messages.INFO, extra_tags='',
                     fail_silently=False):
        messages.success(request, 'success, loooooooooooool')
    '''        
admin.site.register(Order, OrderAdmin)





class ProfileOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'phone', 'email', 'address', 'postal_code']

    def delete_model(self, request, obj):
        obj.visible = False
        obj.save()
        
admin.site.register(ProfileOrder, ProfileOrderAdmin)


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity']

admin.site.register(OrderItem, OrderItemAdmin)
