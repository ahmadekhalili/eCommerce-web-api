from django import forms
from django.utils.translation import gettext_lazy as _

from customed_files.states_towns import list_states_towns
from main.models import State
from .models import ProfileOrder, Order, OrderItem, Shipping, Dispatch
from .widgets import shipping_town_widget

states = [("", "انتخاب کنيد")] + [(L[0][0], L[0][1]) for L in list_states_towns]
class ProfileOrderCreateForm(forms.ModelForm):
    state = forms.ChoiceField(choices=states, required=True, label=_('state'))
    town = forms.CharField(max_length=10, widget=shipping_town_widget, required=True, label=_('town')) #if you choice ChoiceField for this, in saving in admin error like "Select a valid choice. 5691 is not one of the available choices." you will see because ChoiceField should select only from choices, but here value selected is dynamic and is out of choices.
    
    class Meta:
        model = ProfileOrder
        fields = '__all__'




class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'




class ShippingForm(forms.ModelForm):
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('instance'):
            self.fields['state'].initial = kwargs.get('instance').state
            self.fields['town'].widget.initial = kwargs.get('instance').town
    '''        
    state = forms.ChoiceField(choices=states, required=True, label=_('state'))
    town = forms.CharField(max_length=10, widget=shipping_town_widget, required=True, label=_('town')) #if you choice ChoiceField for this, in saving in admin error like "Select a valid choice. 5691 is not one of the available choices." you will see because ChoiceField should select only from choices, but here value selected is dynamic and is out of choices.
    address = forms.CharField(max_length=250, required=True, label=_('address'))
    
    class Meta:
        model = Shipping
        fields = ['fee', 'state', 'town', 'address']



        
class DispatchForm(forms.ModelForm):
    state = forms.ChoiceField(choices=states, required=True, label=_('state'))
    town = forms.CharField(max_length=10, widget=forms.widgets.Select, required=True, label=_('town'))

    class Meta:
        model = Dispatch
        verbose_name = "Phone"
        verbose_name_plural = "My Phones"
        fields = ['shipping_price', 'delivery_date_delay', 'state', 'town']



