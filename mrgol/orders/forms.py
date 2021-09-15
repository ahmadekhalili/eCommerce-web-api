from django import forms
from .models import ProfileOrder, Order, OrderItem




class ProfileOrderCreateForm(forms.ModelForm):
    #postal_code = forms.CharField(max_length=20, required=True)
    
    class Meta:
        model = ProfileOrder
        fields = '__all__'





class OrderCreateForm(forms.ModelForm):
    #postal_code = forms.CharField(max_length=20, required=True)
    
    class Meta:
        model = Order
        fields = '__all__'
