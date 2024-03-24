from django import forms
from django.conf import settings

import json

from . import serializers as my_serializers
from .models import Category, Filter
from .methods import make_next


class QuestionMark:
    """
    this class add question mark to inherited class. widget classes has to inherites this class at first like:
    TextInputQuesMark(QuestionMark, forms.widgets.TextInput), now if you use TextInputQuesMark in a form field,
    question mark will be shown for that field in admin panel. this TextInputQuesMark has three in puts: 1- qus_text
    2- input  3- self.template that should define inside TextInputQuesMark when need extra template.
    """
    main_template = 'main/widgets/field_question_mark.html'

    def __init__(self, attrs=None, qus_text='', input="django/forms/widgets/input.html", *args, **kwargs):
        self.qus_text = qus_text
        self.input = input                # this cause we use 'QuestionMark' widget in different fields (default CharField) like FileField, DateField...
        super().__init__(attrs, *args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['extra_template'] = type(self).mro()[0].__dict__.get('template_name')  # don't get inherited template_name (return None if current class has not 'template_name').
        context['input'] = self.input
        context['aria_control'] = f'tab_id_{name}'
        context['htmlFor'] = f'id_{name}'
        lang_code = name[name.rfind('_') + 1:] if name.rfind('_') > 0 else ''
        context['required'] = 1 if lang_code == settings.LANGUAGES[0][0] else 0
        context['qus_text'] = self.qus_text
        return context

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        return self._render(self.main_template, context, renderer)




class TextInputQuesMark(QuestionMark, forms.widgets.TextInput):
    pass

class NumberInputQuesMark(QuestionMark, forms.widgets.NumberInput):
    pass



class image_icon_QuesMark(QuestionMark, forms.widgets.FileInput):
    template_name = 'main/widgets/product/image_icon_file.html'



class filter_attributes_widget(forms.Select):
    template_name = 'main/widgets/filter_attributes_two_select.html'
    
    def get_context(self, name, value, attrs):
        two_select_context = super().get_context(name, value, attrs)

        filters = list(Filter.objects.prefetch_related('filter_attributes'))               #if dont use list, using filters again, reevaluate filters and query again to database!
        filters_attributes = []
        for filter in filters:                 #in this part we want create dynamicly options inside <select ..> </select>  for field category.level depend on validators we define in PositiveSmallIntegerField(validators=[here]) for example if we have MinValueValidator(1) MaxValueValidator(3) we have 3 options: <option value="1"> 1 </option>   <option value="2"> 2 </option>   <option value="3"> 3 </option>
            filters_attributes += [json.dumps([serializer for serializer in my_serializers.Filter_AttributeListSerializer(filter.filter_attributes.all(), many=True).data])]
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




class product_category_widget(forms.Select):
    template_name = 'main/widgets/product/category_two_select.html'
    
    def get_context(self, name, value, attrs):
        two_select_context = super().get_context(name, value, attrs)

        categories = list(Category.objects.all())
        categories_level_range = list(range(categories[0].level, categories[-1].level+1)) if categories else []        #if we have not eny category in db return [].
        categories_by_level = []
        for i in categories_level_range:
            same_categories = []
            for category in categories:
                if category.level == i:
                    same_categories += [category]
            categories_by_level += [same_categories]
        categoriesbyleveljs_levels = []
        for same_categories in categories_by_level:
            categoriesbyleveljs_levels += [[json.dumps([serializer for serializer in my_serializers.CategoryListSerializer(same_categories, many=True).data]), same_categories[0].level]]
        two_select_context['categories_level_range'] = categories_level_range
        two_select_context['categoriesbyleveljs_levels'] = categoriesbyleveljs_levels
        two_select_context['range_1'] = '1:{}'.format(len(categoriesbyleveljs_levels))
        two_select_context['selected_level_range'] = -1
        two_select_context['selected_category_id'] = -1
            
        if value.id and value.category:
            two_select_context['selected_level_range'] = value.category.level
            two_select_context['selected_category_id'] = value.category.id
            
        return two_select_context




class status_widget(forms.Select):
    template_name = 'main/widgets/comment_status.html'
    
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


class reviewer_widget(forms.widgets.Input):
    template_name = 'main/widgets/comment_reviewer.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['obj'] = value
        return context




class level_widget(forms.Select):
    template_name = 'main/widgets/category_level.html'

    def get_context(self, name, value, attrs):
        categories = list(Category.objects.all())
        context = super().get_context(name, value, attrs)
        if categories:
            max_level = Category._meta.get_field('level').validators[1].limit_value
            highest_level = categories[-1].level
            if highest_level < max_level:
                categories_level_range = list(range(categories[0].level, highest_level+2))           #why we choiced this type structure? supose we want add this tree: <kala barqi>(level=1)  >>  <kala digital>(level=2)  >>  <mobai>(level=3)  >>  <samsung>(level=4)   and now we added <kala barqi>(level=1) via panle admin and want add three others, panel admin in this time in level field show us 1, 2  in fact our program prevent user from creation objects with jumping level!!!
            else:
                categories_level_range = list(range(1, max_level+1))                            #when program come to here? when you created category with latest posible level, for example if max_level=1  after creating first category program come to here or when max_level=3 after creating these: <kala digital>(level=1)  >>  <mobai>(level=2)  >>  <samsung>(level=3)    program come to this so it should list complete levels for us.
        else:
            categories_level_range = [1]                                                        #if we have not eny category in db return [1].
        context['categories_level_range'] = categories_level_range
        context['selected_level_range'] = -1

        if value.id:
            context['selected_level_range'] = value.level
            
        return context


class father_category_widget(forms.Select):
    template_name = 'main/widgets/category_father_category.html'

    def get_context(self, name, value, attrs):
        two_select_context = super().get_context(name, value.father_category_id, attrs)

        categories = list(Category.objects.exclude(id=value.id))
        categories_level_range = list(range(categories[0].level, categories[-1].level+1)) if categories else []        #we we have not eny category in db return [].
        categories_by_level = []
        for i in categories_level_range:
            same_categories = []
            for category in categories:
                if category.level == i:
                    same_categories += [category]
            if same_categories:                                                  #note it is possible empty same_categories(when  like you have not categories level=2 but categories_level_range is [1, 2, 3, 4]) and we must avoid adding empty same_categories because in like: same_categories[0] raise error.
                categories_by_level += [same_categories]
        categoriesbyleveljs_levels = []
        for same_categories in categories_by_level:
            categoriesbyleveljs_levels += [[json.dumps([serializer for serializer in my_serializers.CategoryListSerializer(same_categories, many=True).data]), same_categories[0].level+1]]
        two_select_context['categoriesbyleveljs_levels'] = categoriesbyleveljs_levels
        two_select_context['selected_category_id'] = -1

        if value.father_category_id:
            two_select_context['selected_category_id'] = value.father_category_id

        return two_select_context




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
        context['inputs_ids']
        return context
