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
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.utils import unquote
import json

from customed_files.django.classes.custom_ModelAdmin import CustModelAdmin
from customed_files.date_convertor import MiladiToShamsi
from . import myserializers
from . import myforms
from .models import *
from .mymethods import make_next
from .mycontexts import PROJECT_VERBOSE_NAME
from .model_methods import set_levels_afterthis_all_childes_id

TO_FIELD_VAR = '_to_field'
csrf_protect_m = method_decorator(csrf_protect)

admin.site.site_header = _('{} site panel').format(PROJECT_VERBOSE_NAME)#f'پنل سايت {settings.PROJECT_VERBOSE_NAME}'    
admin.site.site_title = _('{} admin panel').format(PROJECT_VERBOSE_NAME)
admin.site.index_title = _('admin panel')


class CommentInline(admin.TabularInline):
    model = Comment
    fields = ('content', 'author', 'confermer', 'confirm_status', 'get_published_date')
    readonly_fields = ('content', 'author', 'confermer', 'confirm_status', 'get_published_date')
    
    def get_published_date(self, obj):                                       #auto_now_add and auto_now fields must be in read_only otherwise raise error (fill by django not user) and you cant control output of read_only fields with widget (from its form) so for this fiels you cant specify eny widget!!
        date = MiladiToShamsi(obj.published_date.year, obj.published_date.month, obj.published_date.day).result(month_name=True)
        return format_html(f'{date[2]} {date[1]} {date[0]}، ساعت {obj.published_date.hour}:{obj.published_date.minute}')
    get_published_date.short_description = _('published date')


class PostAdmin(admin.ModelAdmin):
    #filter_horizontal = ('contents',)
    prepopulated_fields = {'slug':('title',)}
    inlines = [CommentInline]
    readonly_fields = ('get_published_date',)

    def get_published_date(self, obj):                                       #auto_now_add and auto_now fields must be in read_only otherwise raise error (fill by django not user) and you cant control output of read_only fields with widget (from its form) so for this fiels you cant specify eny widget!!
        date = MiladiToShamsi(obj.published_date.year, obj.published_date.month, obj.published_date.day).result(str_month=True)
        return f'{date[2]} {date[1]} {date[0]}، ساعت {obj.published_date.hour}:{obj.published_date.minute}'
    get_published_date.allow_tags = True
    get_published_date.short_description = _('published date')
    
admin.site.register(Post, PostAdmin)


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
                 {'title': filter.name, 'parameter_name': 'filter_attribute', 'template': 'admin/filter_attribute_filter_custom.html',
                  'state_filter_id': f'state_filter-{i}', 'state_filter_link_id': f'state_filter-link-{i}', 'state_filter_h3_id': f'state_filter-h3-{i}', 'state_filter_more_id': f'state_filter-more-{i}', 'state_filter_less_id': f'state_filter-less-{i}', 'state_filter_icon_id': f'state_filter-icon-{i}',
                  'lookups': lookups, 'queryset': queryset, 'choices': choices}))
except:
    pass


class ImageInline(admin.StackedInline):
    model = Image
    form = myforms.ImageForm


class ProductAdmin(CustModelAdmin):
    search_fields = ['id', 'name__contains', 'slug', 'brand']                            #important: update manualy js file searchbar_help_text_product in class media.
    list_display = ['get_id', 'name', 'price', 'stock', 'rating', 'get_created_brief', 'get_updated_brief']                 #this line is for testing mode!!!
    list_filter = [*filters_list_filter, 'available', 'created', 'updated']
    exclude = ('visible',)
    prepopulated_fields = {'slug':('name',)}
    filter_horizontal = ('filter_attributes',)
    inlines = [ImageInline, CommentInline ]   
    readonly_fields = ('rating', 'get_created', 'get_updated')
    form = myforms.ProductForm
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'brief_description', 'detailed_description', 'price', 'available', 'image', 'alt', 'root', 'filter_attributes', 'rating', 'stock', 'brand', 'weight', 'get_created', 'get_updated')
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
    
    class Media:
        js = ('js/admin/searchbar_help_text_product.js',)                   #addres is in static folder
        
    def get_id(self, obj):
        return obj.id
    get_id.short_description = _('id')
    get_id.admin_order_field = 'id'
    def get_created_brief(self, obj):
        date = MiladiToShamsi(obj.created.year, obj.created.month, obj.created.day).result()
        return f'{date[0]}/{date[1]}/{date[2]}'
    get_created_brief.allow_tags = True
    get_created_brief.short_description = _('created date')
    def get_updated_brief(self, obj):             
        date = MiladiToShamsi(obj.updated.year, obj.updated.month, obj.updated.day).result()
        return f'{date[0]}/{date[1]}/{date[2]}'
    get_updated_brief.allow_tags = True
    get_updated_brief.short_description = _('updated date')
    
    def get_created(self, obj):
        date = MiladiToShamsi(obj.created.year, obj.created.month, obj.created.day).result(month_name=True)
        return f'{date[2]} {date[1]} {date[0]}، ساعت {obj.created.hour}:{obj.created.minute}'
    get_created.allow_tags = True
    get_created.short_description = _('created date')
    def get_updated(self, obj):             
        date = MiladiToShamsi(obj.updated.year, obj.updated.month, obj.updated.day).result(month_name=True)
        return f'{date[2]} {date[1]} {date[0]}، ساعت {obj.updated.hour}:{obj.updated.minute}'
    get_updated.allow_tags = True
    get_updated.short_description = _('updated date')
    
    def save_form(self, request, form, change):
        instance = form.save(commit=False)       
        if not instance.image_icon:             #in new product adding
            image_icon = Image_icon.objects.create(image=request.FILES.get('image'), alt=request.POST.get('alt'))
            instance.image_icon = image_icon
        else:                                   #in change page product we dont need create new Image_icone (it is created in add product page) we just need refresh image and alt of product.image_icone because maybe user changed image or alt!  
            if request.FILES.get('image'):
                instance.image_icon.image = request.FILES.get('image')
            if request.POST.get('alt'):
                instance.image_icon.alt = request.POST.get('alt')
            instance.image_icon.save()                                    #you must save image_icone seperatly, otherwise dont saved changes!!!
        return instance
    
    def get_queryset(self, request):
        queryset = Product.objects.exclude(visible=False)
        return queryset
    
    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):        
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        obj = None
        if object_id:                                   #in adding object in admin panel, object_id is none.
            obj = self.get_object(request, unquote(object_id), to_field)
        extra_context = {}

        selectname_filters, selectid_filters, selectname_filter_attributes, selectid_filter_attributes = [], [], [], []
        filters = list(Filter.objects.prefetch_related('filter_attributes'))               #if dont use list, using filters again, reevaluate filters and query again to database!
        filters_attributes = []
        for filter in filters:                 #in this part we want create dynamicly options inside <select ..> </select>  for field root.level depend on validators we define in PositiveSmallIntegerField(validators=[here]) for example if we have MinValueValidator(1) MaxValueValidator(3) we have 3 options: <option value="1"> 1 </option>   <option value="2"> 2 </option>   <option value="3"> 3 </option>                   
            filters_attributes += [json.dumps([serializer for serializer in myserializers.Filter_AttributeListSerializer(filter.filter_attributes.all(), many=True).data])]
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
        obj.visible = False
        obj.save()

class ProductAdminn(CustModelAdmin):
    filter_horizontal = ('filter_attributes',)
admin.site.register(Product, ProductAdmin)




class CommentAdmin(admin.ModelAdmin):
    list_display = ['get_id', 'author', 'get_published_date', 'confirm_status']
    #fields = ('confirm_status', 'content', 'author', 'confermer')
    #readonly_fields = ('author', 'confermer', 'get_published_date')
    #form = myforms.CommentForm

    def get_id(self, obj):
        return obj.id
    get_id.short_description = _('id')
    get_id.admin_order_field = 'id'
    
    def get_queryset(self, request):
        queryset = Comment.objects.exclude(confirm_status='4')
        return queryset
    
    def get_published_date(self, obj):                                       #auto_now_add and auto_now fields must be in read_only otherwise raise error (fill by django not user) and you cant control output of read_only fields with widget (from its form) so for this fiels you cant specify eny widget!!
        date = MiladiToShamsi(obj.published_date.year, obj.published_date.month, obj.published_date.day).result(month_name=True)
        return format_html(f'{date[2]} {date[1]} {date[0]}، ساعت {obj.published_date.hour}:{obj.published_date.minute}')
    get_published_date.allow_tags = True
    get_published_date.short_description = _('published date')
    '''
    def has_add_permission(self, request, obj=None):
        return False
    '''

    def save_form(self, request, form, change):
        try:
            current_confirm_status = form.instance.confirm_status                       #this is just for change page and in adding new comment this raise error so need try except.
            saved_confirm_status = Comment.objects.get(id=form.instance.id).confirm_status
            if current_confirm_status != saved_confirm_status and current_confirm_status != '2' and current_confirm_status != '4':
                form.instance.confermer = request.user
        except:
            pass
        return form.save(commit=False)

    def delete_model(self, request, obj):
        obj.confirm_status = '4'
        obj.save()
admin.site.register(Comment, CommentAdmin)




Root_level_CHOICES = ((1,'1'), (2,'2'), (3,'3'))               #value for send is first element (here like 1) and value for showing is second (here like '1')
class RootAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    #exclude = ('post_product',)
    form = myforms.RootForm
    list_display = ['str_ob', 'get_id']
    ordering = ['id']
    
    def str_ob(self, obj):
        return obj.__str__()
    str_ob.short_description = _('name')
    str_ob.admin_order_field = 'level'
    def get_id(self, obj):
        return obj.id
    get_id.short_description = _('id')
    get_id.admin_order_field = 'id'
    
    def delete_queryset(self, request, queryset):
        roots = list(queryset)
        dict_ids = [root.id for root in roots]
        queryset.delete()
        
        for id, root in zip(dict_ids, roots):
            previous_father_queryset = Root.objects.filter(id=root.father_root_id).select_related('father_root__'*5+'father_root') if root.father_root_id else None
            root.id, root.father_root, root.father_root_id = id, None, None
            roots_before_join, roots_after_join = set_levels_afterthis_all_childes_id(previous_father_queryset, [root], Root._meta.get_field('level').validators[1].limit_value, delete=True) 
            Root.objects.bulk_update(roots_before_join, ['levels_afterthis', 'all_childes_id']) if roots_before_join else None 
    
    '''
    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if request.POST:
            print('@@@@@@@@@@@@@@@@@@@@@@@@@@@', request.POST)
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
            root = Root.objects.get(id=object_id)
            for field in root._meta.fields:                 #in this part we want create dynamicly options inside <select ..> </select>  for field root.level depend on validators we define in PositiveSmallIntegerField(validators=[here]) for example if we have MinValueValidator(1) MaxValueValidator(3) we have 3 options: <option value="1"> 1 </option>   <option value="2"> 2 </option>   <option value="3"> 3 </option>                   
                if isinstance(field, models.PositiveSmallIntegerField):
                    level_field = field                                  #optain object PositiveSmallIntegerField of Root.level, note: root.level is not same with level_field (root.level.validators raise error) root.level is field value and some limited attributes and level_field is object PositiveSmallIntegerField created by root.level with full attrs of PositiveSmallIntegerField like validators (validators we definded in PositiveSmallIntegerFieldand argument and...)      
            limit_value_MinValueValidator, limit_value_MaxValueValidator = level_field.validators[0].limit_value,  level_field.validators[1].limit_value
            MinValue_MaxValue_range = list(range(limit_value_MinValueValidator, limit_value_MaxValueValidator+1))   #limit_value_MinValueValidator here is 1 because in validators we definded MinValueValidator(1)  and limit_value_MaxValueValidator here is 3 because we definded MaxValueValidator(3)   
            
            roots_seperated_by_level_jslist = []
            all_roots = Root.objects.all()
            for i in MinValue_MaxValue_range:
                roots_seperated_by_level_jslist += [json.dumps([serializer for serializer in myserializers.RootListSerializer(all_roots, many=True).data if serializer['level']==i-1])]           #1- we dont need other fields of root (so just use __str())   2- json.dumps is in fact aray of javascript, because python list can use as javascript aray. supose: L=[1,2,3],  L cant use in javascript as list(javascript dont understand that) but in js_L=json.dumps(L) we can use js_L in javascript ez.   3- we cant use list in list in json.dumps() for example json.dumps([[1,2], [3,4]]) isnt acceptable.                  
            return render(request, 'admin/change_root_template.html', {
                'root': root,
                'levelrange_roots': list(zip(MinValue_MaxValue_range, roots_seperated_by_level_jslist)),
                'range_1': '1:{}'.format(MinValue_MaxValue_range[-1])})      #why we used range_1?  because in django template we cant refere to last index by this way: L[1:]  so this is error: {% for i, j in levelrange_roots|slice:"1:" %}  so we need find last index here and send to template (like "1:3" that 3 is last index) but note using {{ }} will make work in django template like: {{ for i, j in levelrange_roots|slice:"1:" }}    this is work without eny error(i dont know why)
admin.site.register(Root, RootAdmin)




class Filter_RootsInline(admin.StackedInline):
    model = Filter_Roots
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        #kwargs["queryset"] = models.Testrelated.objects.all()
        kwargs["widget"] = forms.Select#(attrs={"style": "width:400px"},)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class FilterAdmin(admin.ModelAdmin):
    filter_horizontal = ('roots',)
    #inlines = [Filter_RootsInline]     
admin.site.register(Filter, FilterAdmin)


class Filter_AttributeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
admin.site.register(Filter_Attribute, Filter_AttributeAdmin)

'''
class ShopFilterItemAdmin(admin.ModelAdmin):
    filter_horizontal = ('filter_attributes',)
    form = myforms.ShopFilterItemForm
admin.site.register(ShopFilterItem, ShopFilterItemAdmin)
'''
admin.site.register(ShopFilterItem)


admin.site.register(Content)

admin.site.register(Image)
admin.site.register(Image_icon)
    
admin.site.register(SmallImage)



admin.site.register(State)


#admin.site.disable_action('delete_selected') 



#video note: myforms.ProductForm.base_fields you can eazy see django modelform chose whitch fields for you foreignkey for manytomany or ... mode fields.
