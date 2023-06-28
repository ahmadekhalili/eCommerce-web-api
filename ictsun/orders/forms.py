from django import forms
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _

from customed_files.django.classes import custforms
from customed_files.states_towns import list_states_towns
from main.models import State
from .models import ProfileOrder, Order, OrderItem, Shipping, Dispatch
from .widgets import shipping_town_widget

states = [("", "انتخاب کنيد")] + [(L[0][0], L[0][1]) for L in list_states_towns]
class ProfileOrderCreateForm(forms.ModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None):
        initial = initial if initial else {}
        selected_state = (instance.town.state.key, instance.town.state.name) if instance else None
        initial = {**initial, 'state': selected_state} if selected_state else initial
        super(). __init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance, use_required_attribute, renderer)

    state = forms.ChoiceField(choices=states, label=_('state'))
    town = custforms.CharFieldForForeignKey(max_length=10, widget=shipping_town_widget, required=True, label=_('town')) #if you choice ChoiceField for this, in saving in admin error like "Select a valid choice. 5691 is not one of the available choices." you will see because ChoiceField should select only from choices, but here value selected is dynamic and is out of choices.
    
    class Meta:
        model = ProfileOrder
        fields = ['user', 'first_name', 'last_name', 'phone', 'state', 'town', 'address', 'postal_code', 'email', 'main']




class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'




class ShippingForm(forms.ModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None):
        initial = initial if initial else {}
        selected_state = (instance.town.state.key, instance.town.state.name) if instance else None
        initial = {**initial, 'state': selected_state} if selected_state else initial
        super(). __init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance, use_required_attribute, renderer)
      
    state = forms.ChoiceField(choices=states, label=_('state'))
    town = custforms.CharFieldForForeignKey(max_length=10, widget=shipping_town_widget, required=True, label=_('town')) #if you choice ChoiceField for this, in saving in admin error like "Select a valid choice. 5691 is not one of the available choices." you will see because ChoiceField should select only from choices, but here value selected is dynamic and is out of choices.
    address = forms.CharField(max_length=250, required=True, label=_('address'))
    
    class Meta:
        model = Shipping
        fields = ['fee', 'state', 'town', 'address']



        
class DispatchForm(forms.ModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None):
        initial = initial if initial else {}
        selected_state = (instance.town.state.key, instance.town.state.name) if instance else None
        initial = {**initial, 'state': selected_state} if selected_state else initial
        super(). __init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance, use_required_attribute, renderer)

    state = forms.ChoiceField(choices=states, label=_('state'))
    town = custforms.CharFieldForForeignKey(max_length=10, widget=forms.widgets.Select, required=True, label=_('town'))

    class Meta:
        model = Dispatch
        fields = ['shipping_price', 'delivery_date_delay', 'state', 'town']



