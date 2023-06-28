from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.serializers import Serializer

import io


def circle_categories(category=None, previous_category=None):          #only one of category / previous_category should provide.
    first_category = category                                     #first_category is first "category" we came to circle_categories with it.
    first_child_categories = first_category.child_categories.all()
    categories = []
    
    if category and previous_category:
        category = previous_category
        ids_list = []
        changed_category = None
        while(True):
            child_categories = [rot for rot in category.child_categories.all()]
            for i in range(len(child_categories)):
                if child_categories[i] == changed_category:
                    child_categories[i] = changed_category
            category.all_childes_id = ','.join(list(dict.fromkeys([s for child in child_categories for s in child.all_childes_id.split(',') if s] + [str(child.id) for child in child_categories]))) if child_categories else ''
            changed_category = category
            categories.append(category)
            category = category.father_category
            if category == first_category:
                break
            
    else:
        category = category
        ids_list = category.all_childes_id.split(',') + [f'{category.id}']
        while(True):
            category = category.father_category
            cleared_ids_list = list(dict.fromkeys(list(filter(None, ids_list))))
            cleared_ids_list.remove(str(category.id))
            category.all_childes_id = ','.join(cleared_ids_list)
            categories.append(category)
            if category in first_child_categories:
                break
         
    return categories


def is_circle(category):
    if category and category.father_category_id:
        if str(category.father_category_id) in category.all_childes_id.split(','):                              #str(category.father_category_id) in category.all_childes_id is worse because supose category.father_category_id=='7' now  '7' in '17,19,20' return return true!!!
            return True
        else:
            return False
    else:
        return False

        
def set_levels_afterthis_all_childes_id(previous_father_queryset, category_queryset, max_limit_value, delete=False):
    category = category_queryset[0]
    previous_category = previous_father_queryset[0] if previous_father_queryset else None              #if previous_father_queryset, previous_father_queryset[0] raise error.  dont change previous_category variabe name, "recursive effect".
    if category:                        #for example in creating firt category.
        list_childes_id = [category.all_childes_id + f',{category.id}' if category.all_childes_id else f'{category.id}'][0].split(',')
        previous_categories, categories = [], []
        if previous_category:
            updated_to_1level_category = True if category.level==1 and previous_category.level>1 else False                  #this will true when supose you have a category with level=4, now convert it to level=1, now category.category.father_category is None so we should handle program with this instead "previous_category.id != category.father_category.id"
            if delete or updated_to_1level_category or previous_category.id != category.father_category.id:                  #updated_to_1level_category must be before previous_category.id != category.father_category.id otherwise raise error
                if is_circle(previous_category):
                    previous_categories = circle_categories(category=category, previous_category=previous_category)
                else:
                    upper_category_levels_afterthis, changed_category = category.levels_afterthis, category
                    while(True):
                        previous_category.all_childes_id = ','.join([s for s in previous_category.all_childes_id.split(',') if s and s not in list_childes_id])
                        if previous_category.levels_afterthis == upper_category_levels_afterthis + 1:
                            childs = previous_category.child_categories.all().values('id', 'levels_afterthis')
                            for child in childs:
                                if child['id'] == changed_category.id:
                                    child['levels_afterthis'] = changed_category.levels_afterthis
                            levels_afterthis_list = sorted([c['levels_afterthis'] for c in childs], reverse=True)
                            biggest_levels_afterthis = levels_afterthis_list[0]+1 if levels_afterthis_list else 0
                            upper_category_levels_afterthis = previous_category.levels_afterthis                                   #why we used previous_category_father_levels_afterthis and upper_category together? and dont remove previous_category_father_levels_afterthis? because in upper_category = previous_category  objects are mutable and upper_category.levels_afterthis will change after changing previous_category.levels_afterthis
                            previous_category.levels_afterthis = biggest_levels_afterthis
                            changed_category = previous_category

                        previous_categories += [previous_category]
                        previous_category = previous_category.father_category                                                                                #note: select_related doesnt lost in recursive and work completly fine(doesnt run additional query)
                        if not previous_category:
                            break    

        
        first_category_id = category.id
        if category.father_category:                                                                           #if creating a category failed, we have not category and we dont want showing erros of set_levels_afterthis_all_childes_id   (we want show error of model Category)
            if is_circle(category):
                categories = circle_categories(category=category)
                
            else:
                adder = category.levels_afterthis+1
                non_dublicate_childes_id = [s for s in list_childes_id if s not in category.father_category.all_childes_id.split(',')]       #if we dont put non_dublicate_childes_id, in every saving of category objects, all_childes_id of that category will increase repitly with same ids in every saving!!  like this(after several blank saving in admin panel): in '1,3,4,1,3,4,1,3,4,1,3,4,1,3,4,1,3,4,'
                if non_dublicate_childes_id:
                    while(True):
                        child = category
                        category = category.father_category
                        if category:
                            category.all_childes_id = ','.join(list(dict.fromkeys(list(filter(None, category.all_childes_id.split(',') + list_childes_id)))))               #list(dict.fromkeys(L)) remove dublicates of list L  and list(filter(None, ['', '1', '2'])) remove empty str and none from list convert to >> ['1', '2']   note: category.all_childes_id.split(',') if was blank produce [''] that ','.join([''] + ['1', '2']) is like '1,2,' !!
                            if child.levels_afterthis >= category.levels_afterthis:
                                category.levels_afterthis = adder
                                adder += 1
                            categories += [category]
                        else:
                            break
        return [previous_categories, categories]
    return [None, None]




def update_product_stock(self, product, saving):         # self is ShopFilterItem obj. this method update stock of product when its ShopFilterItem changes for example supose <shopfilteritem object(2)>.stock -= 2   now <shopfilteritem object(2)>.product.stock should decrease 2 and this method does that for us.
    diff = self.stock - (self.previous_stock or 0)
    if not self.id:                    # creating new ShopFilterItem
        product.stock += self.stock
        if saving:
            product.save()
    else:                              # no difference between diff>0 and diff<0 because if diff>0  += diff  will add and if diff<0  += diff will decrease.
        product.stock += diff
        if saving:
            product.save()

    if not saving:
        return product




def save_to_mongo(model, instance, serializer, change, request=None):
    # model like Post, instance like post1, serializer like PostDetailSerializer or PostDetailSerializer()
    # below serializer calls inside ModelSerializer like PostDetailMongoSerializer
    if isinstance(serializer, Serializer):
        serializer.request, serializer.instance = request, instance
        serialized = serializer.data
    else:                                     # here serializer is like: PostDetailMongoSerializer
        serialized = serializer(instance, context={'request': request}).data
    from django.utils.translation import activate, get_language
    data = {}
    if request:             # when Modeladmin use form request is None (admin calls form without request)
        for tuple in request.POST.items():                              # find all additional fields added in admin panel and add to 'data' in order to save them to db
            if len(tuple[0]) > 6 and tuple[0][:6] == 'extra_':
                data[tuple[0]] = tuple[1]
    language_code = get_language()                                  # get current language code
    activate('en')                                                  # all keys should save in database in `en` laguage(for showing data you can select eny language) otherwise it was problem understading which language should select to run query on them like in:  s = my_serializers.ProductDetailMongoSerializer(form.instance, context={'request': request}).data['shopfilteritems']:     {'رنگ': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} it is false for saving, we should change language by  `activate('en')` and now true form for saving:  {'color': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} and query like: s['color']
    if not change:
        content = JSONRenderer().render(serialized)
        stream = io.BytesIO(content)
        data = {**JSONParser().parse(stream), **data}                           # s is like: {'id': 12, 'name': 'test2', 'slug': 'test2', ...., 'categories': [OrderedDict([('name', 'Workout'), ('slug', 'Workout')])]} and 'OrderedDict' will cease raise error when want save in mongo so we fixed it in data, so data is like:  {'id': 12, 'name': 'test', 'slug': 'test', ...., 'categories': [{'name': 'Workout', 'slug': 'Workout'}]}   note in Response(some_serializer) some_serializer will fixed auto by Response class like our way
        model(id=data['id'], json=data).save(using='mongo')
    else:
        content = JSONRenderer().render(serialized)
        stream = io.BytesIO(content)
        data = {**JSONParser().parse(stream), **data}
        mongo_model = model.objects.using('mongo').get(id=data['id'])
        mongo_model.json = data
        mongo_model.save(using='mongo')
    activate(language_code)





















'''
note:deprecated method find_levels_afterthis
def find_levels_afterthis(previous_father_queryset, max_limit_value):  #this method find lelevls_afterthis handy
    prefetch_query = 'child_categories'
    for i in range(max_limit_value-1):
        prefetch_query += 'child_categories'
    category = previous_father_queryset.prefetch_related(prefetch_query)[0]
    x = 0
    for category in category.child_categories.all():
        x = 1 if x<=1 else x                     #when program return from post loops(lop haie badi) to here with upper x value (like 5) we must dont change x value to lower like 1!!!
        for category in category.child_categories.all():
            x = 2 if x<=2 else x
            for category in category.child_categories.all():
                x = 3 if x<=3 else x
                for category in category.child_categories.all():
                    x = 4 if x<=4 else x
                    for category in category.child_categories.all():
                        x = 5 if x<=5 else x
                        for category in category.child_categories.all():
                            x = 6 if x<=6 else x
                            for category in category.child_categories.all():
                                x = 7 if x<=7 else x
                                for category in category.child_categories.all():
                                    x = 8
    return x

'''
