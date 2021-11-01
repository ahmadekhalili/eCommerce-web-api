from django.contrib import admin
from django.contrib import messages
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

import json
from datetime import datetime

from customed_files.states_towns import list_states_towns
from customed_files.date_convertor import MiladiToShamsi, month_name
from main.models import State
from users.mymethods import user_name_shown
from .models import ProfileOrder, Order, OrderItem, Shipping, Dispatch
from .forms import ProfileOrderCreateForm, ShippingForm, DispatchForm, OrderForm


class ProfileOrderAdmin(admin.ModelAdmin):
    search_fields = ['id', 'first_name', 'last_name']
    list_display = ['id', 'user', 'first_name', 'last_name', 'state', 'town']
    list_filter = ['state', 'town']
    form = ProfileOrderCreateForm
    def delete_model(self, request, obj):
        obj.visible = False
        obj.save()
        
admin.site.register(ProfileOrder, ProfileOrderAdmin)





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
    search_fields = ['id']
    list_display = ['pk', 'get_created', 'paid_type', 'paid', 'price', 'order_status']
    list_filter = ['paid', 'order_status', 'created']
    readonly_fields = ('get_delivery_date', 'get_created', 'firstlast_name_account', 'firstlast_name_order', 'phone', 'email', 'address', 'postal_code')
    inlines = [OrderItemInline]
    fieldsets = (
        (_('address'), {
            'classes': ('collapse',),
            'fields': ('firstlast_name_account', 'firstlast_name_order', 'phone', 'email', 'address', 'postal_code'),
        }),
        (None, {
            'fields': ('profile_order', 'paid_type', 'paid', 'cd_peigiry', 'price', 'shipping_price', 'shipping_type', 'order_status', 'get_delivery_date', 'get_created')
        }),
    )
    
    def pk(self, obj):
        return obj.id
    pk.short_description = _('id')
        
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

    def get_delivery_date(self, obj):                                       #auto_now_add and auto_now fields must be in read_only otherwise raise error (fill by django not user) and you cant control output of read_only fields with widget (from its form) so for this fiels you cant specify eny widget!!
        return '{} {} {}، ساعت {}:{}'.format(obj.delivery_date.day, month_name(obj.delivery_date.month), obj.delivery_date.year, obj.delivery_date.hour, obj.delivery_date.minute)
    get_delivery_date.allow_tags = True
    get_delivery_date.short_description = _('delivery date')
    def get_created(self, obj):
        return '{} {} {}، ساعت {}:{}'.format(obj.created.day, month_name(obj.created.month), obj.created.year, obj.created.hour, obj.created.minute)
    get_created.allow_tags = True
    get_created.short_description = _('created')
    
    def delete_model(self, request, obj):
        obj.visible = False
        obj.save()
    '''
    def message_user(self, request, message, level=messages.INFO, extra_tags='',
                     fail_silently=False):
        messages.success(request, 'success, loooooooooooool')
    '''        
admin.site.register(Order, OrderAdmin)





class OrderItemAdmin(admin.ModelAdmin):
    search_fields = ['order']
    list_display = ['order', 'price', 'quantity', 'item']
    
    def item(self, obj):
        return obj.shopfilteritem if obj.shopfilteritem else obj.product

    class Media:
        js = ('admin/js/custom/custom_admin.js',)
admin.site.register(OrderItem, OrderItemAdmin)

 



class DispatchInline(admin.TabularInline):
    model = Dispatch
    form = DispatchForm
    template = 'admin/edit_inline/dispatch_tabular.html'

    
class ShippingAdmin(admin.ModelAdmin):
    form = ShippingForm
    inlines = [DispatchInline]
    fieldsets = (
        (_('post Shipping'), {
            'classes': ('collapse',),
            'fields': ('fee',),
        }),
        (_('store location'), {
            'classes': ('collapse',),
            'fields': ('state', 'town', 'address'),
        }),
    )

    def _changeform_view(self, request, object_id, form_url, extra_context):                                   #templates of inlines (like dispatch_tabular) render here so context of inlines(variables we want use in inlines templates) should initiate here.
        response = super()._changeform_view(request, object_id, form_url, extra_context)
        town_select_ids = [[f'id_dispatch_set-{i}-state', f'id_dispatch_set-{i}-town'] for i in range(51)]                          #dict([(f'{i}', [f'id_dispatch_set-{i}-state', f'id_dispatch_set-{i}-town']) for i in range(51)])      #this is like: {'0': ['id_dispatch_set-0-state', 'id_dispatch_set-0-town']}    note: structure like d={'id_dispatch_set-0-state', 'id_dispatch_set-0-town'} is worse because in template using like d.id_dispatch_set-0-state  raise error because '-' dont accept in django template and changing auto_id that django generate for us, is worse too because it is hard and even when changed, in post and other methods django use its  own id and it is problem!!!
        if hasattr(response, 'context_data'):
            states_towns = [(state.key, json.dumps(state.towns)) for state in State.objects.filter(key__in=response.context_data['original'].dispatch_set.values_list('state', flat=True))]#[[L[0], json.dumps(L[1])] for L in list_states_towns]                    #[[('1', 'tehran'), json.dumps((('3', 'shahriar'), ('4', 'karaj')))], [('2', 'ardabil'), json.dumps((('5', 'khalkhal'), ('6', 'hir')))]]
            response.context_data = {**response.context_data, 'town_select_ids': town_select_ids, 'states_towns': states_towns} if states_towns else {**response.context_data}       #it was standard we first call super()._changeform_view and add our contextes in extra_context argument but here because we need obj (is optained after super) we added contextes after super (.context_data add contexes to response in class SimpleTemplateResponse)        
        return response
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        if Shipping.objects.exists():
            return False
        return True

admin.site.register(Shipping, ShippingAdmin)
