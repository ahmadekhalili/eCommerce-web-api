from django import forms

from .custom_BoundField import CustomBoundField
from main.models import Root




    
class CustomModelChoiceField(forms.ModelChoiceField):
    def get_bound_field(self, form, field_name):
        """
        Return a BoundField instance that will be used when accessing the form
        field in a template.
        """
        return CustomBoundField(form, self, field_name)




    
class CustomChoiceField(forms.ChoiceField):
    def get_bound_field(self, form, field_name):
        """
        Return a BoundField instance that will be used when accessing the form
        field in a template.
        """
        return CustomBoundField(form, self, field_name)
    




class CustomIntegerField(forms.IntegerField):
    def get_bound_field(self, form, field_name):
        """
        Return a BoundField instance that will be used when accessing the form
        field in a template.
        """
        return CustomBoundField(form, self, field_name)




    
class CustomField(forms.Field):
    def get_bound_field(self, form, field_name):
        """
        Return a BoundField instance that will be used when accessing the form
        field in a template.
        """
        return CustomBoundField(form, self, field_name)

