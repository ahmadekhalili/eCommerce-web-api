from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.forms.utils import ErrorList
from django import forms
from django.core.files import File
from django.utils.text import slugify

import json
from copy import copy
from modeltranslation.utils import get_translation_fields as g_t

from customed_files.django.classes import custforms
from users.models import User
from . import serializers
from .widgets import *
from .methods import get_mt_input_classes, ImageCreation
from .model_methods import save_to_mongo
from .models import Post, Product, Category, Filter, Image, Comment, Filter_Attribute, Brand, ShopFilterItem, \
    Image_icon, PostDetailMongo, ProductDetailMongo
# note1: if edit or add a form field exits in translation.py, like add Categoryform.name field, make sure in admin panel shown correctly (in 'tabbed' mode). if not shown correctly, you have to add a widget with required modeltreanslation classes like in ProductForm.alt_fa.widget.attrs



class PostForm(forms.ModelForm):
    # in form calling, request is required like: PostForm(data=request.POST, request=request)
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None, request=None):
        self.request = request
        super(). __init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance, use_required_attribute, renderer)
        if self.fields.get('slug'):                       # when use form manually in views.py, fields is like: [title, title_fa, title_en, slug, slug_fa,..] as expected  but when use PostFrom in adminpanel, self.fields is like: [title_fa, title_en, slug_fa,..] because admin edit and removes original model fields like 'title', 'slug'
            self.fields['slug'].required = False          # we can define slug field instead this but tab selection for languages will disappeare.

    slug_fa = forms.SlugField(required=False, widget=forms.TextInput(attrs={'class': get_mt_input_classes('slug_fa')}), allow_unicode=True, label=_('slug'))      # Note: slug fa in fronend should be required False to ignore error for slug fa in saving (frontend only sends slug)
    slug_en = forms.SlugField(required=False, widget=forms.TextInput(attrs={'class': get_mt_input_classes('slug_en')}), allow_unicode=True, label=_('slug'))      # Note: slug en in admin panel should be required False to ignore error for slug en in saving.
    category = forms.ModelChoiceField(queryset=Category.objects.filter(post_product='post'), label=_('category'))
    author = forms.ModelChoiceField(queryset=User.objects.all(), required=False, label=_('author'))

    class Meta:
        model = Post
        fields = '__all__'#['title', 'meta_title', 'meta_description', 'brief_description', 'detailed_description', 'instagram_link', 'published_date', 'updated', 'tags', 'category', 'author']

    def save(self, commit=True):
        setattr(self.instance, 'slug', slugify(self.data['title'], allow_unicode=True)) if self.data.get('title') else None   # fill slug field in forms submitted by frontend (front should not fill slug). frontend send data like: 'title': value, 'meta_title': value...   while admin panel send like 'title_fa': value, 'slug_fa': value, 'meta_title': value
        if getattr(self, 'request', None):          # admin form has not request parameter
            self.instance.author = self.request.user
        instance = super().save(commit)
        # calling post.image_icon_set.exists() several time, cause runs several query
        post = instance if instance else self.instance
        image_icon_exits = post.image_icon_set.exists()
        if self.files.get('file') or self.files.get('image_icon_set-0-image'):  # in post updating, we update post images icons when frontend provide self.data['file'] or admin sends first image image_icon_set-0-image (means in admin we can edit image icons only if we change first image icon). suppose post1.image_icon_set.all() == [image240, image420, image40,.., imagedefault] . now if you go to admin/post/post1 and edit one of image icones and submit what will happen? program will save 7 another image for one that if this condition wasnt.
            obj = ImageCreation(self.data, self.files, [240, 420, 640, 720, 960, 1280, 'default'])
            obj.set_instances(Image_icon, path='posts', post=post)
            paths, instances = obj.create_images(path='/media/posts_images/icons/')
            post.image_icon_set.all().delete() if image_icon_exits else None
            Image_icon.objects.bulk_create(instances) if instances else None
        return post


image_qusmark_text = _('Image rate should be 1:1')
weight_qusmark_text = _('weight in gram')
length_qusmark_text = _('size in millimeter')
class ProductForm(custforms.ProductModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None):
        initial = initial if initial else {}
        length, width, height = [float(i) for i in instance.size.split(',')] if instance and instance.size else (None,None,None)
        initial = {**initial, 'length': length, 'width': width, 'height': height} if length else initial
        super(). __init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance, use_required_attribute, renderer)

    #category = custforms.ChoiceFieldCustom(choices=(), widget=product_category_widget, required=True, label=_('category'))
    category = custforms.ModelChoiceFieldCustom(queryset=Category.objects.all(), widget=product_category_widget, required=True, label=_('category'))
    weight_fa = forms.FloatField(widget=NumberInputQuesMark(attrs={'class': get_mt_input_classes('weight_fa')}, qus_text=weight_qusmark_text), required=True, label=_('weight'))
    weight_en = forms.FloatField(widget=NumberInputQuesMark(attrs={'class': get_mt_input_classes('weight_en')}, qus_text=weight_qusmark_text), required=False, label=_('weight'))
    length = forms.FloatField(widget=NumberInputQuesMark(qus_text=length_qusmark_text), label=_('length'))
    width = forms.FloatField(label=_('width'))
    height = forms.FloatField(label=_('height'))

    class Meta:                                          #take fields from admin.fiedset but this is needed for validation.
        model = Product
        fields = ['name', 'slug', 'meta_title', 'meta_description', 'brief_description', 'detailed_description', 'price', 'available', 'visible', 'filter_attributes', 'category', 'brand', 'rating', 'weight_fa', 'weight_en', 'length', 'width', 'height']

    def save(self, commit=True):
        length, width, height = self.cleaned_data.get('length'), self.cleaned_data.get('width'), self.cleaned_data.get('height')
        self.cleaned_data['size'] = str(length) + ',' + str(width) + ',' + str(height) if length and width and height else ''
        self.instance.size = self.cleaned_data['size']
        instance = super().save(commit)
        # calling product.image_icon_set.exists() several time, cause runs several query
        product = instance if instance else self.instance
        image_icon_exits = product.image_icon_set.exists()
        if self.files.get('file') or self.files.get('image_icon_set-0-image'):  # in product updating, we update product images icons when frontend provide self.data['file'] or admin sends first image image_icon_set-0-image (means in admin we can edit image icons only if we change first image icon). supposep roduct1.image_icon_set.all() == [image240, image420, image40,.., imagedefault] . now if you go to admin/product/product1 and edit one of image icones and submit what will happen? program will save 7 another image for one that if this condition wasnt.
            obj = ImageCreation(self.data, self.files, [240, 420, 640, 720, 960, 1280, 'default'])
            obj.set_instances(Image_icon, path='products', product=product)
            paths, instances = obj.create_images(path='/media/products_images/icons/')
            product.image_icon_set.all().delete() if image_icon_exits else None
            Image_icon.objects.bulk_create(instances) if instances else None
        return product


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

    class Meta:
        model = Category
        fields = '__all__'

    def is_valid(self):
        # used in main.admin.CategoryAdmin.save_to_mongo, also self.instance is mutable and must use copy.
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
    image = forms.ImageField(widget=image_icon_widget(qus_text=image_qusmark_text, input=''), required=True, label=_('image icon'))
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

