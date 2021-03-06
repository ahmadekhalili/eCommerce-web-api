from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django import forms
from django.conf import settings
import json

from customed_files.django.classes import myforms
from users.models import User
from . import myserializers
from .mywidgets import image_icon_widget, image_widget, filter_attributes_widget, product_root_widget, level_widget, father_root_widget, confirm_status_widget, confermer_widget, published_date_widget
from .models import Product, Root, Image, Comment, Filter_Attribute, ShopFilterItem



from itertools import chain           
class ProductForm(myforms.ProductModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None):
        initial = initial if initial else {}
        length, width, height = [float(i) for i in instance.size.split(',')] if instance else (None,None,None)
        initial = {**initial, 'length': length, 'width': width, 'height': height} if length else initial
        try:
            image_icon = instance.image_icon
            image, alt = image_icon.image, image_icon.alt
        except:
            image = None
        if image:
            initial = {**initial, 'image': image, 'alt': alt} 
        super(). __init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance, use_required_attribute, renderer)
        
    #root = myforms.CustomChoiceField(choices=(), widget=product_root_widget, required=True, label=_('menu'))
    root = myforms.CustomModelChoiceField(queryset=Root.objects.all(), widget=product_root_widget, required=True, label=_('menu'))
    image = forms.ImageField(widget=image_icon_widget, required=True, label=_('image icon'))
    alt = forms.CharField(max_length=55, label=_('alt'))
    length = forms.FloatField(label=_('length'))
    width = forms.FloatField(label=_('width'))
    height = forms.FloatField(label=_('height'))
    
    class Meta:                                          #take fields from admin.fiedset but this is needed for validation.
        model = Product
        fields = ['name', 'slug', 'meta_title', 'meta_description', 'brief_description', 'price', 'available', 'visible', 'filter_attributes', 'root', 'rating', 'image', 'alt', 'length', 'width', 'height']
                
    def save(self, commit=True):
        length, width, height = self.cleaned_data.get('length'), self.cleaned_data.get('width'), self.cleaned_data.get('height')
        self.cleaned_data['size'] = str(length) + ',' + str(width) + ',' + str(height) if length and width and height else ''
        self.instance.size = self.cleaned_data['size']
        return super().save(commit)
        

class CommentForm(forms.ModelForm):
    confirm_status = myforms.CustomField(widget=confirm_status_widget, required=True, label=_('confirm status'))
    #published_date = CustomField(disabled=True, widget=published_date_widget, label=_('published date'))
    confermer = myforms.CustomField(widget=confermer_widget, label='confermer')           #can user choicefield, problem in saving that.
    
    class Meta:
        model = Comment
        fields = '__all__'




class RootForm(forms.ModelForm):
    level = myforms.CustomIntegerField(widget=level_widget, label=_('level'))
    father_root = myforms.CustomModelChoiceField(queryset=Root.objects.all(), widget=father_root_widget, required=False, label=_('father root'))       #puting CustomModelChoiceField will cease: when creating new root with level 1, father root will feel auto after saving!
        
    class Meta:
        model = Root
        fields = '__all__'




class ImageForm(forms.ModelForm):
    image = forms.ImageField(widget=image_widget, required=True, label=_('image'))
    alt = forms.CharField(max_length=55, label=_('alt'))
    
    class Meta: 
        model = Image
        fields = ['image', 'alt']


'''
class ShopFilterItemForm(forms.ModelForm):
    #filter_attributes = forms.ModelMultipleChoiceField(queryset=Filter_Attribute.objects.all())
    class Meta: 
        model = ShopFilterItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    filter_attributes'].choices, self.fields['product'].choices = filter_attributes_choices, product_choices
      
    def clean(self):
        current_filter_attributes_ids = [filter_attribute.id for filter_attribute in self.cleaned_data.get('filter_attributes')]
        shopfilteritem_id = self.instance.id    
        all_tpl = ShopFilterItem_Filter_Attributes.objects.values_list('shopfilteritem', 'filter_attribute')    #all_tpl is like [(1, 2), (2, 4), (1, 3)]
        all_dct = dict([(key, []) for key in dict(all_tpl)])                             
        [all_dct[i].append(j) for key in all_dct for i,j in all_tpl if key == i]                                #all_dct is like {1: [2, 3], 2: [4]}  
        all_dct[shopfilteritem_id] = current_filter_attributes_ids + all_dct[shopfilteritem_id] if all_dct[shopfilteritem_id] else current_filter_attributes_ids  #now all_dct is like {1: [2, 3], 2: [4, 7]}  7 is new filter_attribute we added that was not in db.  
                
        current_dct = sorted(all_dct.pop(shopfilteritem_id))
        dublicated = False
        for key in all_dct:                                     #note: dont use loop in one line like this:    dublicated = True for key in all_dct if sorted(all_dct[key]) == current_dct else False        because after making dublicated = true it can be False in next loop!
            if sorted(all_dct[key]) == current_dct:
                dublicated = True
        if dublicated:              
            raise ValidationError(_("select unique sets of filter attributes."))
'''    



