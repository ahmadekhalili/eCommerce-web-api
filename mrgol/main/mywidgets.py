from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminTextInputWidget, RelatedFieldWidgetWrapper

import json

from . import myserializers
from .models import Product, Root, Filter, Filter_Attribute
from .mymethods import make_next

    
class filter_attributes_widget(forms.Select):
    template_name = 'main/widgets/filter_attributes_two_select.html'
    
    def get_context(self, name, value, attrs):
        two_select_context = super().get_context(name, value, attrs)

        filters = list(Filter.objects.prefetch_related('filter_attributes'))               #if dont use list, using filters again, reevaluate filters and query again to database!
        filters_attributes = []
        for filter in filters:                 #in this part we want create dynamicly options inside <select ..> </select>  for field root.level depend on validators we define in PositiveSmallIntegerField(validators=[here]) for example if we have MinValueValidator(1) MaxValueValidator(3) we have 3 options: <option value="1"> 1 </option>   <option value="2"> 2 </option>   <option value="3"> 3 </option>                   
            filters_attributes += [json.dumps([serializer for serializer in myserializers.Filter_AttributeListSerializer(filter.filter_attributes.all(), many=True).data])]
        two_select_context['filters_filters_attributes'] = list(zip(filters, filters_attributes))
        two_select_context['range_filters'] = '1:{}'.format(len(filters)) if len(filters)>=1 else '1:1'            #ff len(filter)==0  '1:0' will make error in our program.
        two_select_context['selected_filter_attributes'] = make_next([type('type', (), {'id':-1})])                #we create blank class with attribute id=-1 so in our template dont raise error: {{ selected_filter_attributes.next.id }}
        two_select_context['selected_filters'] = make_next([])

        if value.id:
            selected_filter_attributes = value.filter_attributes.select_related('filterr')      #value is current product.  
            selected_filters = [filter_attribute.filterr for filter_attribute in selected_filter_attributes if filter_attribute]             #if value.filter_attributes.all() was blank, filter_attribute.id  raise error so we need check with if filter_attribute
            selectname_filters, selectid_filters, selectname_filter_attributes, selectid_filter_attributes = [], [], [], []
            for i in range(1, len(selected_filters)):
                selectname_filters += ['filters'+str(i+1)]
                selectid_filters += ['id_filters'+str(i+1)]
                selectname_filter_attributes += ['filter_attributes'+str(i+1)]
                selectid_filter_attributes += ['id_filter_attributes'+str(i+1)]
            two_select_context['selected_filter_attributes'] = make_next(selected_filter_attributes)  
            two_select_context['selected_filters'] = make_next(selected_filters)
            two_select_context['selectname_filters'], two_select_context['selectid_filters'] = make_next(selectname_filters), make_next(selectid_filters)
            two_select_context['selectname_filter_attributes'], two_select_context['selectid_filter_attributes'] = make_next(selectname_filter_attributes), make_next(selectid_filter_attributes)
        return two_select_context




class product_root_widget(forms.Select):
    template_name = 'main/widgets/product/root_two_select.html'
    
    def get_context(self, name, value, attrs):
        two_select_context = super().get_context(name, value, attrs)

        roots = list(Root.objects.all())
        roots_level_range = list(range(roots[0].level, roots[-1].level+1)) if roots else []        #if we have not eny root in db return [].
        roots_by_level = []
        for i in roots_level_range:
            same_roots = []
            for root in roots:                             
                if root.level == i:
                    same_roots += [root]
            roots_by_level += [same_roots]
        rootsbyleveljs_levels = []
        for same_roots in roots_by_level:
            rootsbyleveljs_levels += [[json.dumps([serializer for serializer in myserializers.RootListSerializer(same_roots, many=True).data]), same_roots[0].level]]
        two_select_context['roots_level_range'] = roots_level_range
        two_select_context['rootsbyleveljs_levels'] = rootsbyleveljs_levels
        two_select_context['range_1'] = '1:{}'.format(len(rootsbyleveljs_levels))
        two_select_context['selected_level_range'] = -1
        two_select_context['selected_root_id'] = -1
            
        if value.id and value.root:
            two_select_context['selected_level_range'] = value.root.level
            two_select_context['selected_root_id'] = value.root.id
            
        return two_select_context


class image_icon_widget(forms.widgets.FileInput):
    template_name = 'main/widgets/product/image_icon_file.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['value'] = value
        return context


class weight_widget(forms.widgets.NumberInput):
    template_name = 'main/widgets/product/weight_file.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['value'] = value
        return context


class length_widget(forms.widgets.NumberInput):
    template_name = 'main/widgets/product/length_file.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['value'] = value
        return context




class confirm_status_widget(forms.Select):
    template_name = 'main/widgets/comment_confirm_status.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['obj'] = value
        return context


class published_date_widget(forms.widgets.Input):
    template_name = 'main/widgets/comment_published_date.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['obj'] = value
        return context


class confermer_widget(forms.widgets.Input):
    template_name = 'main/widgets/comment_confermer.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['obj'] = value
        return context




class level_widget(forms.Select):
    template_name = 'main/widgets/root_level.html'

    def get_context(self, name, value, attrs):
        roots = list(Root.objects.all())
        context = super().get_context(name, value, attrs)
        if roots:
            max_level = Root._meta.get_field('level').validators[1].limit_value
            highest_level = roots[-1].level
            if highest_level < max_level:
                roots_level_range = list(range(roots[0].level, highest_level+2))           #why we choiced this type structure? supose we want add this tree: <kala barqi>(level=1)  >>  <kala digital>(level=2)  >>  <mobai>(level=3)  >>  <samsung>(level=4)   and now we added <kala barqi>(level=1) via panle admin and want add three others, panel admin in this time in level field show us 1, 2  in fact our program prevent user from creation objects with jumping level!!!
            else:
                roots_level_range = list(range(1, max_level+1))                            #when program come to here? when you created root with latest posible level, for example if max_level=1  after creating first root program come to here or when max_level=3 after creating these: <kala digital>(level=1)  >>  <mobai>(level=2)  >>  <samsung>(level=3)    program come to this so it should list complete levels for us.
        else:
            roots_level_range = [1]                                                        #if we have not eny root in db return [1].
        context['roots_level_range'] = roots_level_range
        context['selected_level_range'] = -1

        if value.id:
            context['selected_level_range'] = value.level
            
        return context


class father_root_widget(forms.Select):
    template_name = 'main/widgets/root_father_root.html'

    def get_context(self, name, value, attrs):
        two_select_context = super().get_context(name, value.father_root_id, attrs)

        roots = list(Root.objects.exclude(id=value.id))
        roots_level_range = list(range(roots[0].level, roots[-1].level+1)) if roots else []        #we we have not eny root in db return [].
        roots_by_level = []
        for i in roots_level_range:
            same_roots = []
            for root in roots:                             
                if root.level == i:
                    same_roots += [root]
            if same_roots:                                                  #note it is possible empty same_roots(when  like you have not roots level=2 but roots_level_range is [1, 2, 3, 4]) and we must avoid adding empty same_roots because in like: same_roots[0] raise error.
                roots_by_level += [same_roots]
        rootsbyleveljs_levels = []
        for same_roots in roots_by_level:
            rootsbyleveljs_levels += [[json.dumps([serializer for serializer in myserializers.RootListSerializer(same_roots, many=True).data]), same_roots[0].level+1]]
        two_select_context['rootsbyleveljs_levels'] = rootsbyleveljs_levels
        two_select_context['selected_root_id'] = -1

        if value.father_root_id:
            two_select_context['selected_root_id'] = value.father_root_id

        return two_select_context




class filter_name_widget(forms.widgets.TextInput):
    template_name = 'main/widgets/filter_name.html'

class filter_verbose_name_widget(forms.widgets.TextInput):
    template_name = 'main/widgets/filter_verbose_name.html'




class image_widget(forms.widgets.FileInput):
    template_name = 'main/widgets/image_file.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        
        images_ids = []
        inputs_ids = []
        for i in range(50):
            images_ids += ['image-{}-'.format(i)]
            inputs_ids += ['image_set-{}-image'.format(i)]
        context['value'] = value
        context['images_ids'] = make_next(images_ids)
        context['inputs_ids'] = make_next(inputs_ids)
        a = context['inputs_ids']
        return context
