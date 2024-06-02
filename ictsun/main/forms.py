from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxLengthValidator
from django.forms.utils import ErrorList
from django import forms
from django.utils.text import slugify

from copy import copy

from customed_files.django.classes import custforms
from users.models import User
from .widgets import *
from .methods import get_mt_input_classes
from .models import Product, Category, Filter, Image, Comment, Filter_Attribute, ShopFilterItem, Image_icon
# note1: if edit or add a form field exits in translation.py, like add Categoryform.name field, make sure in admin panel shown correctly (in 'tabbed' mode). if not shown correctly, you have to add a widget with required modeltreanslation classes like in ProductAdminForm.alt_fa.widget.attrs


class PostAdminForm(forms.Form):
    #slug_fa = forms.SlugField(required=False, widget=forms.TextInput(attrs={'class': get_mt_input_classes('slug_fa')}), allow_unicode=True, label=_('slug'))      # Note: slug fa in fronend should be required False to ignore error for slug fa in saving (frontend only sends slug)
    title = forms.CharField()
    slug = forms.CharField()
    brief_description = forms.CharField(widget=forms.Textarea)
    detailed_description = forms.CharField(widget=forms.Textarea, required=False)
    instagram_link = forms.CharField(required=False)
    tags = forms.CharField(required=False)
    published_date = forms.CharField(disabled=True, required=False)
    updated = forms.CharField(disabled=True, required=False)
    #category = forms.ModelChoiceField(queryset=Category.objects.filter(post_product='post'), required=False, label=_('category'))
    #author = forms.ModelChoiceField(queryset=User.objects.all(), required=False, label=_('author'))


image_qusmark_text = _('Image rate should be 1:1')
weight_qusmark_text = _('weight in gram')
length_qusmark_text = _('size in millimeter')
class ProductAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        initial, instance = kwargs.get('initial'), kwargs.get('instance')
        initial = kwargs['initial'] if kwargs.get('initial') else {}
        length, width, height = [float(i) for i in instance.size.split(',')] if instance and instance.size else (None,None,None)
        initial = {**initial, 'length': length, 'width': width, 'height': height} if length else initial
        super(). __init__(*args, **kwargs)
        self.fields['length'] = forms.FloatField(widget=NumberInputQuesMark(qus_text=length_qusmark_text), label=_('length'))
        self.fields['width'] = forms.FloatField(label=_('width'))
        self.fields['height'] = forms.FloatField(label=_('height'))

    category = custforms.ModelChoiceFieldCustom(queryset=Category.objects.all(), widget=product_category_widget, required=True, label=_('category'))
    #weight_fa = forms.FloatField(widget=NumberInputQuesMark(attrs={'class': get_mt_input_classes('weight_fa')}, qus_text=weight_qusmark_text), required=True, label=_('weight'))

    class Meta:                               # take fields from admin.fiedset but this is needed for validation
        model = Product
        fields = '__all__'


class CommentForm(forms.ModelForm):
    status = custforms.CustomField(widget=status_widget, required=True, label=_('status'))
    #published_date = CustomField(disabled=True, widget=published_date_widget, label=_('published date'))
    reviewer = custforms.CustomField(widget=reviewer_widget, label='reviewer')           # can use choicefield, problem in saving that.
    
    class Meta:
        model = Comment
        fields = '__all__'




class CategoryForm(forms.ModelForm):
    level = custforms.CustomIntegerField(widget=level_widget, label=_('level'))
    father_category = custforms.ModelChoiceFieldCustom(queryset=Category.objects.all(), widget=father_category_widget, required=False, label=_('father category'))       #puting ModelChoiceFieldCustom will cease: when creating new category with level 1, father category will feel auto after saving!
    post_product = forms.CharField(widget=TextInputQuesMark(qus_text='post or product'), label=_('post or product'))

    class Meta:
        model = Category
        fields = '__all__'

    def is_valid(self):
        # used in main.admin.CategoryAdmin to save to mongo, also self.instance is mutable and must use copy.
        self.previouse_cat = copy(self.instance)
        return super().is_valid()




name_qusmark_text = _("name for quering. it should be unique. (it is equel to verbose_name of filter in most cases but can be difference. for example supose we have filter1 and filter2 so: name of filter1=`Phone Operating System` unequel with verbose_name of filter1=`Operating System`  name of filter2=`Laptop Operating System` unequel with verbose_name of filter2=`Operating System`)")
verbose_qusmark_text = _("name for showing to user. (it is equel to name of filter in most cases)")
class FilterForm(forms.ModelForm):
    name_fa = forms.CharField(validators=[MaxLengthValidator(limit_value=25)], widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('name_fa')}, qus_text=name_qusmark_text), label=_('name'))
    name_en = forms.CharField(validators=[MaxLengthValidator(limit_value=25)], widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('name_en')}, qus_text=name_qusmark_text), required=False, empty_value=None, label=_('name'))
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




class ImageIconForm(forms.ModelForm):
    image = forms.ImageField(widget=image_icon_QuesMark(qus_text=image_qusmark_text, input=''), required=True, label=_('image icon'))
    #alt_fa = forms.CharField(max_length=55, widget=forms.TextInput(attrs={'class': get_mt_input_classes('alt_fa')}), label=_('alt'))
    #alt_en = forms.CharField(max_length=55, widget=forms.TextInput(attrs={'class': get_mt_input_classes('alt_en')}), required=False, empty_value=None, label=_('alt'))   # if you don't put required=False, this field will be required in modeltranslation tab.

    class Meta:
        model = Image_icon
        fields = '__all__'




class ImageForm(forms.ModelForm):
    image = forms.ImageField(widget=image_widget, required=True, label=_('image'))
    alt_fa = forms.CharField(widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('alt_fa')}, qus_text=name_qusmark_text), max_length=55, label=_('alt'))
    alt_en = forms.CharField(widget=TextInputQuesMark(attrs={'class': get_mt_input_classes('alt_en')}, qus_text=name_qusmark_text), max_length=55, required=False, empty_value=None, label=_('alt'))

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
