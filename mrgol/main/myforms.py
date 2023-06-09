from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.forms.utils import ErrorList
from django import forms
from django.conf import settings
from django.core.files import File

import json
import uuid
from modeltranslation.utils import get_translation_fields as g_t

from customed_files.django.classes import myforms
from users.models import User
from . import myserializers
from .mywidgets import *
from .mymethods import get_mt_input_classes
from .models import Post, Product, Category, Filter, Image, Comment, Filter_Attribute, Brand, ShopFilterItem, Image_icon
# note1: if edit or add a form field exits in translation.py, like add Categoryform.name field, make sure in admin panel shown correctly (in 'tabbed' mode). if not shown correctly, you have to add a widget with required modeltreanslation classes like in ProductForm.alt_fa.widget.attrs



class PostForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.filter(post_product='post'), label=_('category'))

    class Meta:
        model = Post
        fields = '__all__'

    def save(self, commit=True):
        image_icon = Image_icon(alt=self.data.get('alt', uuid.uuid4().hex[:6]), path='posts')
        image_icon.image = File(self.files['main_image'])
        image_icon.save()
        self.instance.main_image_id = image_icon.id
        return super().save(commit)



image_qusmark_text = _('Image rate should be 1:1')
weight_qusmark_text = _('weight in gram')
length_qusmark_text = _('size in millimeter')
class ProductForm(myforms.ProductModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None):
        initial = initial if initial else {}
        length, width, height = [float(i) for i in instance.size.split(',')] if instance and instance.size else (None,None,None)
        initial = {**initial, 'length': length, 'width': width, 'height': height} if length else initial
        try:
            image_icon = instance.image_icon
            image, alts = image_icon.image, {}
            for f in g_t('alt'):
                if getattr(image_icon, f, None):
                    alts[f] = getattr(image_icon, f)
        except:
            image = None
        if image:
            initial = {**initial, 'image': image}
            for f in alts:
                initial[f] = alts[f]
        super(). __init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance, use_required_attribute, renderer)

    #category = myforms.CustomChoiceField(choices=(), widget=product_category_widget, required=True, label=_('category'))
    category = myforms.CustomModelChoiceField(queryset=Category.objects.all(), widget=product_category_widget, required=True, label=_('category'))
    image = forms.ImageField(widget=image_icon_widget(qus_text=image_qusmark_text, input=''), required=True, label=_('image icon'))
    alt_fa = forms.CharField(max_length=55, widget=forms.TextInput(attrs={'class': get_mt_input_classes('alt_fa')}), label=_('alt'))
    alt_en = forms.CharField(max_length=55, widget=forms.TextInput(attrs={'class': get_mt_input_classes('alt_en')}), required=False, label=_('alt'))   # if you don't put required=False, this field will be required in modeltranslation tab.
    weight_fa = forms.FloatField(widget=NumberInputQuesMark(attrs={'class': get_mt_input_classes('weight_fa')}, qus_text=weight_qusmark_text), required=True, label=_('weight'))
    weight_en = forms.FloatField(widget=NumberInputQuesMark(attrs={'class': get_mt_input_classes('weight_en')}, qus_text=weight_qusmark_text), required=False, label=_('weight'))
    length = forms.FloatField(widget=NumberInputQuesMark(qus_text=length_qusmark_text), label=_('length'))
    width = forms.FloatField(label=_('width'))
    height = forms.FloatField(label=_('height'))

    class Meta:                                          #take fields from admin.fiedset but this is needed for validation.
        model = Product
        fields = ['name', 'slug', 'meta_title', 'meta_description', 'brief_description', 'detailed_description', 'price', 'available', 'visible', 'filter_attributes', 'category', 'rating', 'image', 'alt_fa', 'alt_en', 'weight_fa', 'weight_en', 'length', 'width', 'height']

    def save(self, commit=True):
        length, width, height = self.cleaned_data.get('length'), self.cleaned_data.get('width'), self.cleaned_data.get('height')
        self.cleaned_data['size'] = str(length) + ',' + str(width) + ',' + str(height) if length and width and height else ''
        self.instance.size = self.cleaned_data['size']
        return super().save(commit)


class CommentForm(forms.ModelForm):
    status = myforms.CustomField(widget=status_widget, required=True, label=_('status'))
    #published_date = CustomField(disabled=True, widget=published_date_widget, label=_('published date'))
    reviewer = myforms.CustomField(widget=reviewer_widget, label='reviewer')           # can use choicefield, problem in saving that.
    
    class Meta:
        model = Comment
        fields = '__all__'




class CategoryForm(forms.ModelForm):
    level = myforms.CustomIntegerField(widget=level_widget, label=_('level'))
    father_category = myforms.CustomModelChoiceField(queryset=Category.objects.all(), widget=father_category_widget, required=False, label=_('father category'))       #puting CustomModelChoiceField will cease: when creating new category with level 1, father category will feel auto after saving!

    class Meta:
        model = Category
        fields = '__all__'

    def is_valid(self):
        self.previouse_name = self.instance.name            # used in main.admin.CategoryAdmin.save_related
        self.previouse_slug = self.instance.slug
        return self.is_bound and not self.errors




name_qusmark_text = _("name for quering. it should be unique. (it is equel to verbose_name of filter in most cases but can be difference. for example supose we have filter1 and filter2 so: name of filter1=`Phone Operating System` unequel with verbose_name of filter1=`Operating System`  name of filter2=`Laptop Operating System` unequel with verbose_name of filter2=`Operating System`)")
verbose_qusmark_text = _("name for showing to user. (it is equel to name of filter in most cases)")
class FilterForm(forms.ModelForm):
    name_fa = forms.CharField(validators=[MaxLengthValidator(limit_value=25)], widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('name_fa')}, qus_text=name_qusmark_text), label=_('name'))
    name_en = forms.CharField(validators=[MaxLengthValidator(limit_value=25)], widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('name_en')}, qus_text=name_qusmark_text), required=False, label=_('name'))
    verbose_name_fa = forms.CharField(validators=[MaxLengthValidator(limit_value=25)], widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('verbose_name_fa')}, qus_text=verbose_qusmark_text), label=_('verbose_name'))
    verbose_name_en = forms.CharField(validators=[MaxLengthValidator(limit_value=25)], widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('verbose_name_en')}, qus_text=verbose_qusmark_text), required=False, label=_('verbose_name'))

    class Meta:
        model = Filter
        fields = '__all__'




class Filter_AttributeForm(forms.ModelForm):
    class Meta:
        model = Filter_Attribute
        fields = '__all__'

    def is_valid(self):
        self.previouse_name = self.instance.name            # used in main.admin.Filter_AttributeAdmin.save_related
        return self.is_bound and not self.errors




class ImageForm(forms.ModelForm):
    image = forms.ImageField(widget=image_widget, required=True, label=_('image'))
    alt_fa = forms.CharField(widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('alt_fa')}, qus_text=name_qusmark_text), max_length=55, label=_('alt'))
    alt_en = forms.CharField(widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('alt_en')}, qus_text=name_qusmark_text), max_length=55, required=False, label=_('alt'))

    class Meta: 
        model = Image
        fields = ['image', 'alt_fa', 'alt_en']


class ShopFilterItemForm(forms.ModelForm):

    class Meta: 
        model = ShopFilterItem
        exclude = ['previous_stock']

'''
class ShopFilterItemForm(forms.ModelForm):
    #filter_attribute = forms.ModelChoiceField(queryset=Filter_Attribute.objects.filter(filterr__selling=True), label=_('filter_attribute'))
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

