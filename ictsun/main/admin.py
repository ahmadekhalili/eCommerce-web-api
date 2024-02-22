from django.contrib import admin
from django.urls import path
from django.conf import settings
from django import forms
from django.db import models, router, transaction
from django.shortcuts import render
from django.http import QueryDict
from django.utils.html import format_html
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import gettext_lazy as _, activate, get_language
from django.contrib.admin.utils import unquote
from django.conf import settings

from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

import io
import json
import jdatetime
import os
import pymongo
import environ
from pathlib import Path
from urllib.parse import quote_plus
from modeltranslation.admin import TranslationAdmin
from modeltranslation.utils import get_translation_fields as g_t

from customed_files.django.classes.ModelAdmin import ModelAdminCust
from . import serializers as my_serializers
from . import forms as my_forms
from .models import *
from .methods import make_next, get_category_and_fathers, get_parsed_data, save_to_mongo, brand_save_to_mongo, \
    comment_save_to_mongo, category_save_to_mongo, filter_attribute_save_to_mongo, shopfilteritem_save_to_mongo, \
    image_save_to_mongo, SavePostProduct
from .contexts import PROJECT_VERBOSE_NAME
from .model_methods import set_levels_afterthis_all_childes_id

TO_FIELD_VAR = '_to_field'
csrf_protect_m = method_decorator(csrf_protect)

admin.site.site_header = _('{} site panel').format(PROJECT_VERBOSE_NAME)#f'پنل سايت {settings.PROJECT_VERBOSE_NAME}'    
admin.site.site_title = _('{} admin panel').format(PROJECT_VERBOSE_NAME)
admin.site.index_title = _('admin panel')
env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))
username, password, db_name = quote_plus(env('MONGO_USERNAME')), quote_plus(env('MONGO_USERPASS')), env('MONGO_DBNAME')
host = env('MONGO_HOST')
uri = f"mongodb://{username}:{password}@{host}:27017/{db_name}?authSource={db_name}"
mongo_db = pymongo.MongoClient(uri)['akh_db']


class CommentInline(admin.TabularInline):
    model = Comment
    fields = ('content', 'author', 'reviewer', 'status', 'get_published_date')
    readonly_fields = ('content', 'author', 'reviewer', 'status', 'get_published_date')
    
    def get_published_date(self, obj):                                       #auto_now_add and auto_now fields must be in read_only otherwise raise error (fill by django not user) and you cant control output of read_only fields with widget (from its form) so for this fiels you cant specify eny widget!!
        ymd = jdatetime.datetime.fromgregorian(datetime=obj.published_date).strftime('%Y %B %-d').split()         # this is like ['1388', 'Esfand', '1']
        return format_html('{} {}&rlm; {}، ساعت {}:{}'.format(ymd[2], _(ymd[1]), ymd[0], obj.published_date.minute, obj.published_date.hour))
    get_published_date.short_description = _('published date')


class ImageIconInline(admin.TabularInline):
    model = Image_icon
    fields = ('image', 'alt', 'path')


class PostAdmin(TranslationAdmin):
    prepopulated_fields = {'slug':('title',)}
    inlines = [CommentInline, ImageIconInline]
    readonly_fields = ('get_published_date', 'get_updated')
    form = my_forms.PostAdminForm

    class Media:                                 # this cause languages shown separatly in admin panel. (it should be use always, otherwise all field of all languages shown under each other at once)
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

    def get_published_date(self, obj):                                       #auto_now_add and auto_now fields must be in read_only otherwise raise error (must fill by django not form) and you cant control output of read_only fields with widget (from its form) so for this fiels you cant specify eny widget!!
        date = jdatetime.datetime.fromgregorian(datetime=obj.published_date).strftime('%Y %B %-d').split()
        return format_html('{} {}&rlm; {}، ساعت {}:{}'.format(date[2], _(date[1]), date[0], obj.published_date.minute, obj.published_date.hour))
    get_published_date.allow_tags = True
    get_published_date.short_description = _('published date')

    def get_updated(self, obj):                                       #auto_now_add and auto_now fields must be in read_only otherwise raise error (must fill by django not form) and you cant control output of read_only fields with widget (from its form) so for this fiels you cant specify eny widget!!
        date = jdatetime.datetime.fromgregorian(datetime=obj.updated).strftime('%Y %B %-d').split()
        return format_html('{} {}&rlm; {}، ساعت {}:{}'.format(date[2], _(date[1]), date[0], obj.updated.minute, obj.updated.hour))
    get_updated.allow_tags = True
    get_updated.short_description = _('updated date')

    def save_model(self, request, obj, form, change):
        # this method calls 'obj.save()', this have to be done in save_related instead here.
        self.obj = obj

    def save_related(self, request, form, formsets, change):
        # here save post.image_icon_set
        for formset in formsets:
            if type(formset).__name__ == 'Image_iconFormFormSet':
                form.cleaned_data['icon'] = formset.cleaned_data[0]
                if form.cleaned_data['icon']:    # formset.cleaned_data[0] is {} when don't fill icon formset
                    del form.cleaned_data['icon']['DELETE']
                    del form.cleaned_data['icon']['id']  # keys must be Image_icon fields all additional must delete
                    del formsets[formsets.index(formset)]
        # formsets is like: Image_iconFormFormSet, CommentFormFormSet.., formset is list of several icons, comments ...
        # we must delete Image_iconFormFormSet because image saving should be done in save_product not admin.
        SavePostProduct.save_post(save_func=self.obj.save, save_func_args={}, instance=self.obj,
                                  data=form.cleaned_data, partial=False)
        super().save_related(request, form, formsets, change)             # manytomany fields will remove from form.instance._meta.many_to_many after calling save_m2m()
        save_to_mongo(mongo_db[settings.MONGO_POST_COL], form.instance, my_serializers.PostDetailMongoSerializer, change, request)

    def delete_model(self, request, obj):
        if not settings.DEBUG:    # productions mode
            obj.visible = False
            obj.save()
        else:                     # development mode
            super().delete_model(request, obj)

admin.site.register(Post, PostAdmin)




class BrandAdmin(TranslationAdmin):
    prepopulated_fields = {'slug':('name',)}

    class Media:                                 # this cause languages shown separatly in admin panel. (it should be use always, otherwise all field of all languages shown under each other at once)
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

    def save_related(self, request, form, formsets, change):             # here update product in mongo database  (productdetailmongo_col['json']['brand']) according to Brand changes. for example if brand_1.name changes to 'Apl'  ProductDetailMongo:  [{ id: 1, json: {brand: 'Apl', ...}}, {id: 2, ...}]
        super().save_related(request, form, formsets, change)
        brand_save_to_mongo(mongo_db, form.instance, change, request)

admin.site.register(Brand, BrandAdmin)


filters_list_filter = []
try:                               #in first creating db,  we have not eny table so raise error in for filter in Filter.objects.prefetch_related ...
    i = -1
    for filter in Filter.objects.prefetch_related('filter_attributes'):
        i += 1
        def lookups(self, request, model_admin, filter=filter):                    #should return list of tuples like [('1', 'one'), ('2', 'two'), ..]
            return filter.filter_attributes.values_list('id', 'name')

        def queryset(self, request, queryset):
            if self.value():                                                #if dont put this, list_display will be blank always (even when you want all objects like when you go to url: "http://192.168.114.21:8000/admin/orders/profileorder" program come here and self.value() is None in that case and queryset.filter(state=None) make our queryset clear!
                return queryset.filter(filter_attributes=self.value())

        def choices(self, changelist):
            for lookup, title in self.lookup_choices:
                yield {
                    'selected': self.value() == str(lookup),
                    'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                    'display': title,
                }
        filters_list_filter.append(type('Filter_AttributeListFilter', (admin.SimpleListFilter,),
                 {'title': filter.name, 'parameter_name': 'filter_attribute', 'template': 'admin/main/product/filter_attribute_filter_custom.html',
                  'state_filter_id': f'state_filter-{i}', 'state_filter_link_id': f'state_filter-link-{i}', 'state_filter_h3_id': f'state_filter-h3-{i}', 'state_filter_more_id': f'state_filter-more-{i}', 'state_filter_less_id': f'state_filter-less-{i}', 'state_filter_icon_id': f'state_filter-icon-{i}',
                  'lookups': lookups, 'queryset': queryset, 'choices': choices}))
except:
    pass


class ImageInline(admin.StackedInline):
    model = Image
    form = my_forms.ImageForm


class ProductAdmin(ModelAdminCust):
    search_fields = ['id', 'name__contains', 'slug', 'brand']                            #important: update manualy js file searchbar_help_text_product in class media.
    list_display = ['id', 'name', 'price', 'stock', 'rating', 'get_created_brief', 'get_updated_brief']                 #this line is for testing mode!!!
    list_filter = [*filters_list_filter, 'available', 'created', 'updated']
    exclude = ('visible',)
    prepopulated_fields = {'slug':('name',)}
    filter_horizontal = ('filter_attributes',)
    inlines = [ImageInline, CommentInline, ImageIconInline]
    readonly_fields = ('rating', 'get_created', 'get_updated')
    form = my_forms.ProductAdminForm
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'brief_description', 'detailed_description', 'price', 'available', 'category', 'filter_attributes', 'rating', 'stock', 'brand', 'weight', 'get_created', 'get_updated')
        }),
        (_('size'), {
            'classes': ('collapse',),
            'fields': ('length', 'width', 'height'),
        }),
        (_('seo fields'), {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description'),
        }),
    )

    class Media:                                 # this cause languages shown separatly in admin panel. (it should be use always, otherwise all field of all languages shown under each other at once)
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
            'js/admin/searchbar_help_text_product.js',  # addres is in static folder
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

    def get_created_brief(self, obj):
        date = jdatetime.datetime.fromgregorian(date=obj.created).strftime('%Y %-m %-d').split()       # -m -d month date in one|two digit,  but m d is month day in two digit
        return f'{date[0]}/{date[1]}/{date[2]}'
    get_created_brief.allow_tags = True
    get_created_brief.short_description = _('created date')
    def get_updated_brief(self, obj):             
        date = jdatetime.datetime.fromgregorian(date=obj.created).strftime('%Y %-m %-d').split()
        return f'{date[0]}/{date[1]}/{date[2]}'
    get_updated_brief.allow_tags = True
    get_updated_brief.short_description = _('updated date')

    def get_created(self, obj):
        date = jdatetime.datetime.fromgregorian(datetime=obj.published_date).strftime('%Y %B %-d').split()
        return format_html('{} {}&rlm; {}، ساعت {}:{}'.format(date[2], _(date[1]), date[0], obj.published_date.minute, obj.published_date.hour))
    get_created.allow_tags = True
    get_created.short_description = _('created date')
    def get_updated(self, obj):             
        date = jdatetime.datetime.fromgregorian(datetime=obj.published_date).strftime('%Y %B %-d').split()
        return format_html('{} {}&rlm; {}، ساعت {}:{}'.format(date[2], _(date[1]), date[0], obj.published_date.minute, obj.published_date.hour))
    get_updated.allow_tags = True
    get_updated.short_description = _('updated date')

    def get_queryset(self, request):
        queryset = Product.objects.exclude(visible=False)
        return queryset

    def save_model(self, request, obj, form, change):
        # this method calls 'obj.save()', this have to be done in save_related instead here.
        self.obj = obj

    def save_related(self, request, form, formsets, change):
        # here save product.size and product.image_icon_set, and save in mongo database (ProductDetailMongo col)
        for formset in formsets:
            if type(formset).__name__ == 'Image_iconFormFormSet':
                form.cleaned_data['icon'] = formset.cleaned_data[0]
                if form.cleaned_data['icon']:    # formset.cleaned_data[0] is {} when don't fill icon formset
                    del form.cleaned_data['icon']['DELETE']
                    del form.cleaned_data['icon']['id']  # keys must be Image_icon fields all additional must delete
                    del formsets[formsets.index(formset)]
        # formsets is like: Image_iconFormFormSet, CommentFormFormSet.., formset is list of several icons, comments ...
        # we must delete Image_iconFormFormSet because image saving should be done in save_product not admin.
        SavePostProduct.save_product(save_func=self.obj.save, save_func_args={}, instance=self.obj,
                                 data=form.cleaned_data, partial=False)
        super().save_related(request, form, formsets, change)             # manytomany fields will remove from form.instance._meta.many_to_many after calling save_m2m()
        save_to_mongo(mongo_db[settings.MONGO_PRODUCT_COL], form.instance, my_serializers.ProductDetailMongoSerializer, change, request)

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        #if request.method == 'POST':
        #    print('11111111111111111111111111111', request.POST)
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        obj = None
        if object_id:                                   #in adding object in admin panel, object_id is none.
            obj = self.get_object(request, unquote(object_id), to_field)
        extra_context = {}

        selectname_filters, selectid_filters, selectname_filter_attributes, selectid_filter_attributes = [], [], [], []
        filters = list(Filter.objects.prefetch_related('filter_attributes'))               #if dont use list, using filters again, reevaluate filters and query again to database!
        filters_attributes = []
        for filter in filters:                 #in this part we want create dynamicly options inside <select ..> </select>  for field category.level depend on validators we define in PositiveSmallIntegerField(validators=[here]) for example if we have MinValueValidator(1) MaxValueValidator(3) we have 3 options: <option value="1"> 1 </option>   <option value="2"> 2 </option>   <option value="3"> 3 </option>
            filters_attributes += [json.dumps([serializer for serializer in my_serializers.Filter_AttributeListSerializer(filter.filter_attributes.all(), many=True).data])]
        for i in range(50):
            selectname_filters += ['filters'+str(i)]
            selectid_filters += ['id_filters'+str(i)]
            selectname_filter_attributes += ['product_filter_attributes_set-{}-filter_attribute'.format(i)]
            selectid_filter_attributes += ['id_product_filter_attributes_set-{}-filter_attribute'.format(i)]
        extra_context['filters_filters_attributes'] = list(zip(filters, filters_attributes))
        extra_context['range_filters'] = '1:{}'.format(len(filters)) if len(filters)>=1 else '1:1'            #ff len(filter)==0  '1:0' will make error in our program.
        extra_context['selected_filter_attributes'] = make_next([type('type', (), {'id':-1})])                #we create blank class with attribute id=-1 so in our template dont raise error: {{ selected_filter_attributes.next.id }}
        extra_context['selected_filters'] = make_next([])
        extra_context['selectname_filters'], extra_context['selectid_filters'] = make_next(selectname_filters), make_next(selectid_filters)
        extra_context['selectname_filter_attributes'], extra_context['selectid_filter_attributes'] = make_next(selectname_filter_attributes), make_next(selectid_filter_attributes)

        if object_id:
            selected_filter_attributes = obj.filter_attributes.select_related('filterr')      #value is current product.  
            selected_filters = [filter_attribute.filterr for filter_attribute in selected_filter_attributes if filter_attribute]             #if obj.filter_attributes.all() was blank, filter_attribute.id  raise error so we need check with if filter_attribute
            extra_context['selected_filter_attributes'] = make_next(selected_filter_attributes)  
            extra_context['selected_filters'] = make_next(selected_filters)
            # if add product in shell, mongo_product can be None
            mongo_product = mongo_db[settings.MONGO_PRODUCT_COL].find_one({"id": obj.id})['json']
            extra_fields = {}
            if mongo_product:
                for tuple in mongo_product.json.items():                              # find all additional fields added in admin panel and add to 'data' in order to save them to db
                    if len(tuple[0]) > 6 and tuple[0][:6] == 'extra_':
                        extra_fields[tuple[0]] = tuple[1]
                extra_context['extra_fields'] = extra_fields                          # extra_fields is like: {'extra_colorbody': 'orange', 'extra_bodyweight': 2}
        return super().changeform_view(request, object_id, form_url, extra_context)

    def add_vieww(self, request, form_url='', extra_context=None):
        if request.method == 'POST':
            filter_attributes_value = []
            for i in range(1, 50):
                filter_attribute_name = 'filter_attributes'+str(i)
                filter_attribute_value = request.POST.get(filter_attribute_name)
                if filter_attribute_value:
                    filter_attributes_value += filter_attribute_value
            filter_attributes_value = ['1', '2']
            post = request.POST.copy()
            post.setlist('filter_attributes', filter_attributes_value)
            request.POST = post
        return super().changeform_view(request, None, form_url, extra_context)
    
    def change_vieww(self, request, object_id, form_url='', extra_context=None):
        if request.method == 'POST':  
            filter_attributes_value = []
            for i in range(1, 50):
                filter_attribute_name = 'filter_attributes'+str(i)
                filter_attribute_value = request.POST.get(filter_attribute_name)
                if filter_attribute_value:
                    filter_attributes_value += filter_attribute_value
            post = request.POST.copy()
            post.setlist('filter_attributes', filter_attributes_value)
            request.POST = post
        return super().change_view(request, object_id, form_url, extra_context)

    def delete_model(self, request, obj):
        if not settings.DEBUG:    # productions mode
            obj.visible = False
            obj.save()
        else:                     # development mode
            super().delete_model(request, obj)

admin.site.register(Product, ProductAdmin)




class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'get_published_date', 'status']
    #fields = ('status', 'content', 'author', 'reviewer')
    #readonly_fields = ('author', 'reviewer', 'get_published_date')
    #form = my_forms.CommentForm

    def get_queryset(self, request):
        queryset = Comment.objects.exclude(status='4')
        return queryset
    
    def get_published_date(self, obj):                                       #auto_now_add and auto_now fields must be in read_only otherwise raise error (fill by django not user) and you cant control output of read_only fields with widget (from its form) so for this fiels you cant specify eny widget!!
        date = jdatetime.datetime.fromgregorian(datetime=obj.published_date).strftime('%Y %B %-d').split()
        return format_html('{} {} &rlm; {}، ساعت {}:{}'.format(date[2], _(date[1]), date[0], obj.published_date.hour, obj.published_date.minute))
    get_published_date.allow_tags = True
    get_published_date.short_description = _('published date')
    '''
    def has_add_permission(self, request, obj=None):
        return False
    '''

    def save_form(self, request, form, change):
        try:
            status = form.instance.status                       #this is just for change page and in adding new comment this raise error so need try except.
            saved_status = Comment.objects.get(id=form.instance.id).status
            if status != saved_status and status != '2' and status != '4':
                form.instance.reviewer = request.user
        except:
            pass
        return form.save(commit=False)

    def delete_model(self, request, obj):
        if not settings.DEBUG:    # productions mode
            obj.status = '4'
            obj.save()
        else:                     # development mode
            super().delete_model(request, obj)

    def save_related(self, request, form, formsets, change):         # here update product in mongo database  (product_detail_mongo.json.comment_set) according to Comment changes. for example if we have comment_1 (comment_1.product=<Product (1)>)   comment_1.content changes to 'another_content'  ProductDetailMongo:  [{id: 1, json: {comment_set: [{ id: 2, status: '1', published_date: '2022-08-07T17:33:38.724203', content: 'another_content', author: { id: 1, user_name: 'ادمین' }, reviewer: null, post: null, product: 12 }], ...}}, {id: 2, ...}]
        super().save_related(request, form, formsets, change)
        comment_save_to_mongo(mongo_db, form.instance, my_serializers.CommentSerializer, change, request)

admin.site.register(Comment, CommentAdmin)




class CategoryInline(admin.TabularInline):
    model = Category
    fields = ['get_id', 'name', 'level']
    readonly_fields = ['get_id', 'name', 'level']
    verbose_name = _('Sub category')
    verbose_name_plural = _('Sub categories')
    
    def has_delete_permission(self, request, obj=None):
        return False

    def get_id(self, obj):
        return obj.id
    get_id.short_description = _('id')


class Category_FiltersInline(admin.StackedInline):
    model = Category_Filters

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        #kwargs["queryset"] = models.Testrelated.objects.all()
        kwargs["widget"] = forms.Select#(attrs={"style": "width:400px"},)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


Category_level_CHOICES = ((1,'1'), (2,'2'), (3,'3'))               #value for send is first element (here like 1) and value for showing is second (here like '1')
class CategoryAdmin(TranslationAdmin):
    inlines = [CategoryInline]
    prepopulated_fields = {'slug':('name',)}
    #exclude = ('post_product',)
    filter_horizontal = ('filters', 'brands')
    form = my_forms.CategoryForm
    list_display = ['str_ob', 'id']
    ordering = ['id']

    class Media:                                 # this cause languages shown separatly in admin panel. (it should be use always, otherwise all field of all languages shown under each other at once)
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

    def str_ob(self, obj):
        return obj.__str__()
    str_ob.short_description = _('name')
    str_ob.admin_order_field = 'level'
    
    def delete_queryset(self, request, queryset):
        categories = list(queryset)
        dict_ids = [category.id for category in categories]
        queryset.delete()
        
        for id, category in zip(dict_ids, categories):
            previous_father_queryset = Category.objects.filter(id=category.father_category_id).select_related('father_category__'*5+'father_category') if category.father_category_id else None
            category.id, category.father_category, category.father_category_id = id, None, None
            categories_before_join, categories_after_join = set_levels_afterthis_all_childes_id(previous_father_queryset, [category], Category._meta.get_field('level').validators[1].limit_value, delete=True)
            Category.objects.bulk_update(categories_before_join, ['levels_afterthis', 'all_childes_id']) if categories_before_join else None

    def save_related(self, request, form, formsets, change):         # here update product in mongo database  (product_detail_mongo.json.categories) according to Category changes. for example if <Category digital>.name changes to 'digggital'  all products with category 'digital' os children of 'digital' like 'phone' or 'smart phone' will changes like product_1 (product_1.category=<Category digital>), product_2 (product_2.category=<Category phone>), product_3 (product_3.category=<Category smart phone>):   product detail mongo col:  [{ id: 1, json: {categories: [{ name: 'digggital', slug: 'digital' }], ...}}, { id: 2, json: {categories: [{ name: 'digital', slug: 'digital' }, { name: 'phone', slug: 'phone' }], ...}}, { id: 3, json: {categories: [{ name: 'digggital', slug: 'digital' }, { name: 'phone', slug: 'phone' }, { name: 'smart phone', slug: 'smart-phone' }], ...}}]
        super().save_related(request, form, formsets, change)
        category_save_to_mongo(mongo_db, form, my_serializers.CategoryChainedSerializer, change)

    '''
    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if request.POST:
            #post = request.POST.copy()
            #post.setlist('level', ['1'])
            #request.POST = post
        return super().changeform_view(request, object_id=None, form_url='', extra_context=None)
    '''
    '''
    def get_urls(self):
        urls = super().get_urls()
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)
        info = self.model._meta.app_label, self.model._meta.model_name

        for i in range(len(urls)):
            try:                                  #some urls have not .pattern so raise error in if istatment without try.
                if '/change/' in str(urls[i].pattern):
                    urls[i] = path('<path:object_id>/change/', wrap(self.change_view), name='%s_%s_change' % info)
            except:
                pass
   
        my_urls = [path('aa/', self.my_view)]            
        return my_urls + urls
    
    def my_view(self, request):
        return render(request, 'change.html', {})#HttpResponse('loooooooooooooooooool')
    '''
    def change_vieww(self, request, object_id, form_url='', extra_context=None):
        if request.method == 'POST':
            return super().change_view(request, object_id, form_url, extra_context)            
        
        else:
            category = Category.objects.get(id=object_id)
            for field in category._meta.fields:                 #in this part we want create dynamicly options inside <select ..> </select>  for field category.level depend on validators we define in PositiveSmallIntegerField(validators=[here]) for example if we have MinValueValidator(1) MaxValueValidator(3) we have 3 options: <option value="1"> 1 </option>   <option value="2"> 2 </option>   <option value="3"> 3 </option>
                if isinstance(field, models.PositiveSmallIntegerField):
                    level_field = field                                  #optain object PositiveSmallIntegerField of Category.level, note: category.level is not same with level_field (category.level.validators raise error) category.level is field value and some limited attributes and level_field is object PositiveSmallIntegerField created by category.level with full attrs of PositiveSmallIntegerField like validators (validators we definded in PositiveSmallIntegerFieldand argument and...)
            limit_value_MinValueValidator, limit_value_MaxValueValidator = level_field.validators[0].limit_value,  level_field.validators[1].limit_value
            MinValue_MaxValue_range = list(range(limit_value_MinValueValidator, limit_value_MaxValueValidator+1))   #limit_value_MinValueValidator here is 1 because in validators we definded MinValueValidator(1)  and limit_value_MaxValueValidator here is 3 because we definded MaxValueValidator(3)   
            
            categories_seperated_by_level_jslist = []
            all_categories = Category.objects.all()
            for i in MinValue_MaxValue_range:
                categories_seperated_by_level_jslist += [json.dumps([serializer for serializer in my_serializers.CategoryListSerializer(all_categories, many=True).data if serializer['level']==i-1])]           #1- we dont need other fields of category (so just use __str())   2- json.dumps is in fact aray of javascript, because python list can use as javascript aray. supose: L=[1,2,3],  L cant use in javascript as list(javascript dont understand that) but in js_L=json.dumps(L) we can use js_L in javascript ez.   3- we cant use list in list in json.dumps() for example json.dumps([[1,2], [3,4]]) isnt acceptable.
            return render(request, 'admin/change_category_template.html', {
                'category': category,
                'levelrange_categories': list(zip(MinValue_MaxValue_range, categories_seperated_by_level_jslist)),
                'range_1': '1:{}'.format(MinValue_MaxValue_range[-1])})      #why we used range_1?  because in django template we cant refere to last index by this way: L[1:]  so this is error: {% for i, j in levelrange_categories|slice:"1:" %}  so we need find last index here and send to template (like "1:3" that 3 is last index) but note using {{ }} will make work in django template like: {{ for i, j in levelrange_categories|slice:"1:" }}    this is work without eny error(i dont know why)
admin.site.register(Category, CategoryAdmin)




class FilterAdmin(TranslationAdmin):
    list_display = ['id', 'name']
    form = my_forms.FilterForm

    class Media:                                 # this cause languages shown separatly in admin panel. (it should be use always, otherwise all field of all languages shown under each other at once)
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

admin.site.register(Filter, FilterAdmin)


class Filter_AttributeAdmin(TranslationAdmin):
    list_display = ('id', 'name', 'filterr')                         # filterr doesnt add additional query (can read project\project parts\admin\list_display seperat
    prepopulated_fields = {'slug':('name',)}
    form = my_forms.Filter_AttributeForm

    class Media:                                 # this cause languages shown separatly in admin panel. (it should be use always, otherwise all field of all languages shown under each other at once)
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        filter_attribute_save_to_mongo(mongo_db, form, change)

admin.site.register(Filter_Attribute, Filter_AttributeAdmin)


class ShopFilterItemAdmin(TranslationAdmin):
    form = my_forms.ShopFilterItemForm
    list_display = ['get_str', 'stock', 'price']

    class Media:                                 # this cause languages shown separatly in admin panel. (it should be use always, otherwise all field of all languages shown under each other at once)
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

    def get_str(self, obj):
        return str(obj)
    get_str.short_description = _('shopfilteritem')                  # should be same with ShopFilterItem.Meta.verbose_name

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        shopfilteritem_save_to_mongo(mongo_db, form, my_serializers.ShopFilterItemSerializer, change)

admin.site.register(ShopFilterItem, ShopFilterItemAdmin)


class ImageSizesInline(admin.TabularInline):
    model = ImageSizes
    fields = ('image', 'alt', 'size')


class ImageAdmin(TranslationAdmin):
    inlines = [ImageSizesInline]
    class Media:                                 # this cause languages shown separatly in admin panel. (it should be use always, otherwise all field of all languages shown under each other at once)
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        image_save_to_mongo(mongo_db, form.instance, my_serializers.ImageSerializer, change)

admin.site.register(Image, ImageAdmin)



# admin.site.register(Image_icon) image icons should edit in post and product pages (for integration for mongo creation)

admin.site.register(State)


#admin.site.disable_action('delete_selected') 
'''
#this get_form has put for copy paste easily in admin.py.
    def get_form(self, request, obj=None, change=False, **kwargs):
        a = super().get_form(request, obj=None, change=False, **kwargs)
        return a
'''
#video note: my_forms.ProductAdminForm.base_fields you can eazy see django modelform chose whitch fields for you foreignkey for manytomany or ... mode fields.
