from django.conf import settings
from django.db import transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import activate, get_language
from django.db.models.query import QuerySet

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.serializers import Serializer

from onetomultipleimage.methods import ImageCreationSizes

import os
import io
import uuid
import pymongo
import jdatetime
from datetime import datetime
from decimal import Decimal
from bs4 import BeautifulSoup
from bson.objectid import ObjectId
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context
from collections.abc import Iterable
from PIL import Image as PilImage
from pathlib import Path
from itertools import cycle
from math import ceil
from .models import Product, Category, Image_icon




def get_products(first_index, last_index, queryset=None, orderings=None):    #orderings should be list like: ['slug']
    orderings = orderings if orderings else []
    if queryset != None:                                                     #this dont evaluate queryset and if queryset was blank queryset like <queryset ()> condition 'queryset!=None' will be true and this is what we want.
        return queryset.filter(visible=True).order_by('-available', *orderings, '-id')[first_index: last_index]      #[first: last]is flexible means if we have not enogh product, return fewer product.      we can count by: 1: Product.objects.count()  2: Product.objects.aggregate(product_counts=Max('id') - Min('id'))['product_counts']

    try:                                                                                 
        return Product.objects.filter(visible=True).order_by('-available', *orderings, '-id')[first_index: last_index]        #dont have different beetwen Product.objects.filter(visible=True).order_by('-available', '-id')[first_index:last_index]   or    Product.objects.filter(id__in=list(range(first_index:last_index)), visible=True).order_by('-available', '-id')   they run same query in db.
    except:                                                #when we have no eny products.
        return []


def get_posts(post_col, query=None, first_index=None, last_index=None):
    # query as dict like: {'category': 1}
    if not query:
        query = {}
    query['visible'] = True
    data = list(post_col.find(query).skip(first_index).limit(last_index).sort('_id', pymongo.DESCENDING))
    for d in data:
        d['_id'] = str(d['_id'])
    return data

'''
def childest_category(category, childs=[]):                 
    for child_category in category.child_categories.all():
        childs.append(childest_category(child_category))
    return category
def get_childs_and_category(category, return_self=True):                    
    childs = childest_category(category)
    if return_self:
        return [*childs, category]
    return childs
'''


def get_category_and_fathers(category):
    if category:
        if isinstance(category, QuerySet):
            category = category[0]
        category_and_fathers = [category]
        for i in range(category.level-1):
            category = category.father_category
            if category:
                category_and_fathers += [category]
        return category_and_fathers
    raise AttributeError('category is None')


def get_category_and_children(category):      # obtain category and children by queries (very heavy)
    for_query = [category]
    children = [category]
    while(for_query):
        categories = list(for_query.pop(-1).father_category_set.all())
        if categories:
            for_query += [*categories]                 # `for_query` and `children` are not mutable
            children += [*categories]
    return children


def get_posts_products_by_category(category):
    if category.level < Category._meta.get_field('level').validators[1].limit_value:
        # why we used filter? category.all_childes_id.split(',') may return: [''] that raise error in statements like  filter(in__in=['']) so we ez remove blank str of list by filter.
        category_children_ids = [category.id] + list(filter(None, category.all_childes_id.split(',')))
    else:
        category_children_ids = [category.id]
    if category.post_product == 'product':
        return Product.objects.filter(category__id__in=category_children_ids)
    else:
        return get_posts(query={'category': {'$in': category_children_ids}})




def get_mt_input_classes(name):         # configure md==modeltranslation with QuestionMark widget. in fact if we want question mark icon shown when we use modeltranslation admin tabbed. we have to add these classes. otherwise, modeltranslation admin can't be shown in 'tabbed' mod.
    indx = name.rfind('_')              # if rfind not found result, indx will be -1
    name, lng_cd = (name[:indx], name[indx+1:]) if indx > 0 else ('', '')
    default = ' mt-bidi mt-default' if settings.LANGUAGES[0][0] == lng_cd else ''   # for first language we should add default classes to. to be selected by default in admin pannel.
    return f'vTextField mt mt-field-{name}-{lng_cd}' + default




def get_unique_list(items):       # remove duplicates from list and return list
    no_duplicate = []
    for item in items:
        if item not in no_duplicate:
            no_duplicate.append(item)
    return no_duplicate


def get_parsed_data(data):
    # data type is dict
    content = JSONRenderer().render(data)
    stream = io.BytesIO(content)
    return JSONParser().parse(stream)


def get_page_count(count, step, **kwargs):  # count can be a model class or instances of model class
    if isinstance(count, int):
        return ceil(count / step)
    import inspect
    if inspect.isclass(count):    # count is like: Product or other model class
        ceil(count.objects.filter(visible=True, **kwargs).count() / step)
    else:        # count is like <Queryset Product(1), Product(2), ....> or other model instances
        # ceil round up number, like: ceil(2.2)==3 ceil(3)==3
        return ceil(count.count() / step)


def save_to_mongo(mongo_col, instance, serializer, change, request=None):
    # mongo_col like pymongo.MongoClient("...")['db_name']['product_detail'], instance like product1
    # serializer like ProductDetailSerializer or ProductDetailSerializer()
    # below serializer calls inside ModelSerializer like save_to_mongo(mongo_db, instance, self, ..)
    if isinstance(serializer, Serializer):    # serializer instance, like: ProductSerializer(..)
        serializer.request, serializer.instance = request, instance
        serialized = serializer.data
    else:                                     # serializer class
        serialized = serializer(instance, context={'request': request}).data
    data = {}
    if request:             # when Modeladmin use form request is None (admin calls form without request)
        for tuple in request.POST.items():                              # find all additional fields added in admin panel and add to 'data' in order to save them to db
            if len(tuple[0]) > 6 and tuple[0][:6] == 'extra_':
                data[tuple[0]] = tuple[1]
    language_code = get_language()
    activate('en')                                                     # all keys should save in database in `en` laguage(for showing data you can select eny language) otherwise it was problem understading which language should select to run query on them like in:  s = my_serializers.ProductDetailMongoSerializer(form.instance, context={'request': request}).data['shopfilteritems']:     {'رنگ': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} it is false for saving, we should change language by  `activate('en')` and now true form for saving:  {'color': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} and query like: s['color']
    if not change:
        data = {**get_parsed_data(serialized), **data}                 # s is like: {'id': 12, 'name': 'test2', 'slug': 'test2', ...., 'categories': [OrderedDict([('name', 'Workout'), ('slug', 'Workout')])]} and 'OrderedDict' will cease raise error when want save in mongo so we fixed it in data, so data is like:  {'id': 12, 'name': 'test', 'slug': 'test', ...., 'categories': [{'name': 'Workout', 'slug': 'Workout'}]}   note in Response(some_serializer) some_serializer will fixed auto by Response class like our way
        mongo_col.insert_one(data)
    else:
        data = {**get_parsed_data(serialized), **data}
        mongo_col.update_one({'id': data['id']}, {"$set": data})
    activate(language_code)


def post_save_to_mongo(post_col, pk=None, data=None, change=None):
    # 'pk' is pk of post in mongo db used in updating, 'data' type is dict
    language_code = get_language()
    activate('en')
    if not change:
        data = get_parsed_data(data)
        post_col.insert_one(data)
    else:
        data = get_parsed_data(data)
        post_col.update_one({'_id': ObjectId(pk)}, {"$set": data})
    activate(language_code)
    return data


def brand_save_to_mongo(shopdb_mongo, brand, change, request=None):
    if change:
        products_ids = list(Product.objects.filter(brand=brand).values_list('id', flat=True))  # doc in Filter_AttributeAdmin.save_related
        mycol = shopdb_mongo[settings.MONGO_PRODUCT_COL]
        mycol.update_many({'id': {'$in': products_ids}}, {'$set': {'brand': brand.name}})


def comment_save_to_mongo(mongo_db, comment, serializer, change, request=None):
    comment = comment
    serializer.instance = comment
    data = get_parsed_data(serializer.data)
    if comment.post:
        post_col = mongo_db.post
        if not change:
            post_col.update_one({'_id': ObjectId(comment.post)}, {'$push': {'comments': data}})
        else:
            post_col.update_one({'_id': ObjectId(comment.post), 'comments.id': comment.id}, {'$set': {'comments.$': data}})

    elif comment.product_id:
        product_col, foreignkey = settings.MONGO_PRODUCT_COL, comment.product_id
        if not change:
            product_col.update_one({'id': foreignkey}, {'$push': {'comments': data}})
        else:
            product_col.update_one({'id': foreignkey, 'comments.id': comment.id}, {'$set': {'comments.$': data}})
    else:      # this will prevent error in comment editing when there is not any post/product
        return None


def category_save_to_mongo(mongo_db, form, category_chain_serializer, category_serializer=None, change=False):
    # we can't import CategoryFathersChainedSerializer due to 'circle import error'
    if change:
        category = form.instance
        children_ids = category.all_childes_id.split(',') if category.all_childes_id else []
        category_children_ids = [category.id] + list(Category.objects.filter(id__in=children_ids).values_list('id', flat=True))   # why we need children of category?  suppose we edit `digital` category in admin, we should update all products with category digital or child of `digital`.  for example: product1.category = <Smart phone...>,  product1 in mongo db: product1['categories'] is like [{ name: 'digital', slug: 'digital' }, { name: 'phone', slug: 'phone'}, { name: 'smart phone', slug: 'smart_phone'}],  now if we edit digital product1 should update!

        if category.post_product == 'post':
            mycol = mongo_db['post']
            ids = mongo_db.post.find({'category.id': {'$in': category_children_ids}}, {'_id': 1})
            ids, id_key = [post['_id'] for post in ids], '_id'
            if ids:
                mycol.update_many({'_id': {'$in': ids}},
                                  {'$set': {'category': category_serializer(category).data}})
        elif category.product_set.exists():
            ids = list(Product.objects.filter(category_id__in=category_children_ids).values_list('id', flat=True))
            mycol, id_key = mongo_db[settings.MONGO_PRODUCT_COL], 'id'
        else:            # this will prevent error in category editing when there is not any post/product
            return None
        mycol.update_many({id_key: {'$in': ids}},
                          {'$set': {'category_fathers.$[element]': category_chain_serializer(category).data}},
                          array_filters=[{'element': category_chain_serializer(form.previouse_cat).data}])
        del form.previouse_cat


def filter_attribute_save_to_mongo(shopdb_mongo, form, change):
    if change:
        filter_attribute = form.instance
        filter_name, filterattribute_name = filter_attribute.filterr.name, filter_attribute.name
        products_ids = list(filter_attribute.product_set.values_list('id', flat=True))                 # products_ids is like ['1', '2', '5', ...]
        mycol = shopdb_mongo[settings.MONGO_PRODUCT_COL]
        mycol.update_many({'id': {'$in': products_ids}}, {'$set': {'filters.{}.$[element]'.format(filter_name): filterattribute_name}},
                          array_filters=[{'element': form.previouse_name}])      # note1: form.previouse_name should be in databse otherwise comment will not work       2:  we can't use like:  mycol.update_many({'id': {'$in': products_ids}}, {'$set': {'filters.{}.{}'.format(filter_name, form.previouse_name): filterattribute_name}})  because filters.filter_name is list not dict  also can't use string type f: f'...' and should use ''.fromat
        del form.previouse_name


def shopfilteritem_save_to_mongo(shopdb_mongo, form, serializer, change):
    if change:
        shopfilteritem = form.instance
        product_id, filter_name = shopfilteritem.product.id, shopfilteritem.filter_attribute.filterr.name  # doc in Filter_AttributeAdmin.save_related
        mycol = shopdb_mongo[settings.MONGO_PRODUCT_COL]
        mycol.update_many({'id': product_id}, {'$set': {'shopfilteritems.{}.$[element]'.format(filter_name): serializer(shopfilteritem).data}}, array_filters=[{'element.id': shopfilteritem.id}])


def image_save_to_mongo(shopdb_mongo, image, serializer, change):
    if change:
        image_id = image.id
        data = get_parsed_data(serializer(image).data)
        mycol = shopdb_mongo[settings.MONGO_PRODUCT_COL]
        mycol.update_one({'images.id': image_id}, {'$set': {'images.$': data}})


class PostDispatchPrice:                       # weight in gram, and length in mm.
    def __init__(self, weight, dimensions):    # weight must be int, dimensions is like ["200,200,150", "300,250,200"]
        self.weight = int(weight)
        self.dimensions = dimensions
        post_cartons_dimensions = {'1': [150, 100, 100], '2': [200, 150, 100], '3': [200, 200, 150], '4': [300, 200, 200], '5': [350, 250, 200], '6': [450, 250, 200], '7': [400, 300, 250], '8': [450, 400, 300], '9': [550, 450, 350]}

    @property
    def carton_size(self):
        post_cartons_volumes = {'1': 1500000, '2': 3000000, '3': 6000000, '4': 12000000, '5': 17500000, '6': 22500000, '7': 30000000, '8': 54000000, '9': 86625000}
        goods_volume = 0                 #in mm3(mm*mm*mm)
        for size_str in self.dimensions:
            L = [float(i) for i in size_str.split(',')]
            goods_volume += L[0] * L[1] * L[2]
        for volume in post_cartons_volumes:
            if volume in ['4', '6', '7', '9']:                #we limited post cartons to only 4 size ('4', '6', '7', '9')
                if goods_volume < post_cartons_volumes[volume]:
                    return volume
                
    def get_price(self, from_state, from_town, to_state, to_town):                       #from_state and others is str (like '1')
        CIPHERS = ('DEFAULT:!DH')
        class DESAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                context = create_urllib3_context(ciphers=CIPHERS)
                kwargs['ssl_context'] = context
                return super(DESAdapter, self).init_poolmanager(*args, **kwargs)
            def proxy_manager_for(self, *args, **kwargs):
                context = create_urllib3_context(ciphers=CIPHERS)
                kwargs['ssl_context'] = context
                return super(DESAdapter, self).proxy_manager_for(*args, **kwargs)
        session = requests.Session()
        session.mount('https://parcelprice.post.ir', DESAdapter())
        
        data1 = {"__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "",
                 "__VIEWSTATE": "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htqv2YTYp9iv2LQI2KjZhtmK2YYK2KjZiNiq2KfZhhDYqNmI2KrYs9mI2KfZhtinFtio2YjYsdqv2YrZhtin2YHYp9iz2Ygf2KjZiNiz2YbZiiDZiCDZh9ix2LLZhyDar9mI2YrZhgzYqNmI2YTZitmI2YoO2KjZitmE2KfYsdmI2LMQ2b7Yp9ix2Kfar9mI2KbZhwzZvtin2YbYp9mF2KcO2b7Yp9qp2LPYqtin2YYM2b7Ysdiq2LrYp9mEBtm+2LHZiA3ZvtmE2Yog2YbYstmKEtiq2KfYrNmK2qnYs9iq2KfZhhDYqtin2YbYstin2YbZitinDNiq2KfZitmE2YbYrwzYqtin2YrZiNin2YYe2KrYsdmK2YbZitiv2KfYr9mI2KrZiNio2KfaqdmIEtiq2LHaqdmF2YbYs9iq2KfZhgrYqtix2qnZitmHCtiq2Yjar9mI2YYI2KrZiNmG2LMK2KrZiNmG2q/YpwzYqtmI2YjYp9mE2YgT2KrZitmF2YjYsSDYtNix2YLZihDYrNin2YXYp9im2YraqdinE9is2KjZhCDYp9mE2LfYp9ix2YIV2KzYstin2YrYsSDYotmG2KrZitmEF9is2LLYp9mK2LEg2LPZhNmK2YXYp9mGDNis2YrYqNmI2KrZigbahtin2K8G2obZitmGBNqG2qkO2K/Yp9mG2YXYp9ix2qkO2K/ZiNmF2YrZhtmK2qkQ2K/ZiNmF2YrZhtmK2qnZhgzYsdmI2KfZhtiv2KcK2LHZiNiz2YrZhwzYsdmI2YXYp9mG2YoI2LLYptmK2LEM2LLYp9mF2KjZitinDtiy2YrZhdio2KfZiNmHCNqY2KfZvtmGDtiz2KfYptmI2KrZhdmHEdiz2KfYrdmE4oCM2LnYp9isFdiz2KfZhdmI2KfZiiDYutix2KjZihDYs9ix2YrZhNin2YbaqdinE9iz2YYg2b7YsdmI2YXZitqv2YgP2LPZhiDZhNmI2KbZitizDdiz2YYg2YbZvtin2YQL2LPZhiDZh9mE2YYT2LPZhiDaqdix2YrYs9iq2YjZgQ7Ys9mG2q/Yp9m+2YjYsQrYs9mG2q/Yp9mECNiz2YjYptivCtiz2YjYptmK2LMS2LPZiNin2YrYstmK2YTZhtivCtiz2YjYr9in2YYO2LPZiNix2YrZhtin2YUK2LPZiNix2YrZhwzYs9mI2YXYp9mE2YoQ2LPZitix2KfZhNim2YjZhgjYs9mK2LTZhAjYtNmK2YTZig7Ytdix2KjYs9iq2KfZhgjYudix2KfZgg7Yudix2KjYs9iq2KfZhgjYudmF2KfZhgbYutmG2KcM2YHYsdin2YbYs9mHDNmB2YbZhNin2YbYrwjZgdmK2KzZig7ZgdmK2YTZitm+2YrZhgjZgtio2LHYsxLZgtix2YLZitiy2LPYqtin2YYQ2YLYstin2YLYs9iq2KfZhgbZgti32LEK2q/Yp9io2YjZhgzar9in2YXYqNmK2KcO2q/Ysdin2YbYp9iv2KcO2q/Ysdis2LPYqtin2YYQ2q/ZiNin2KrZhdin2YTYpxDar9mI2KfYr9in2YTZiNm+Ctqv2YjZitin2YYZ2q/ZiNmK2KfZhuKAjNmB2LHYp9mG2LPZhwjar9mK2YbZhxnar9mK2YbZh+KAjNin2LPYqtmI2KfZitmKF9qv2YrZhtmH4oCM2KjZitiz2KfYptmICtmE2KfYptmI2LMK2YTYqNmG2KfZhgrZhNiq2YjZhtmKCtmE2LPZiNiq2YgM2YTZh9iz2KrYp9mGFNmE2Yjaqdiy2KfZhdio2YjYsdqvDNmE2YrYqNix2YrYpwjZhNmK2KjZig7ZhNmK2KrZiNin2YbZihfZhNmK2K7YqtmGINin2LTYqtin2YrZhhTZhdin2K/Yp9qv2KfYs9qp2KfYsRDZhdin2LHYqtmK2YbZitqpDNmF2KfZhNin2YjZigjZhdin2YTYqgzZhdin2YTYr9mK2YgK2YXYp9mE2LLZigjZhdin2YTZigzZhdin2qnYp9im2YgQ2YXYrNin2LHYs9iq2KfZhgrZhdix2Kfaqdi0BtmF2LXYsRDZhdi62YjZhNiz2KrYp9mGDtmF2YLYr9mI2YbZitmHENmF2YjYsdmK2KrYp9mG2YoK2YXZiNix2YrYsxDZhdmI2LLYp9mF2KjZitqpDtmF2YjZhNiv2KfZiNmKDNmF2YjZhtin2qnZiA7ZhdmI2YbYqtix2KfYqhjZhdmK2KfZhtmF2KfYsSjYqNix2YXZhykK2YXaqdiy2YraqQjZhtin2LHZiA7Zhtin2YXZitio2YrYpwjZhtm+2KfZhAjZhtix2YjamAjZhtmK2KzYsQzZhtmK2KzYsdmK2YcQ2YbZitmI2LLZitmE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",
                  "__EVENTVALIDATION": "/wEWGwL2gPj1DwKa78W2DwK3792fCgKi79mfCgLixem4DQKAy5njBQLugq82Apbs76AOAtiWlokLAvTEvGMC75LX6QkC8JLX6QkC8ZLX6QkC8pLX6QkC85LX6QkC9JLX6QkC9ZLX6QkC9pLX6QkC55LX6QkC6JLX6QkC8JKX6gkC8JKb6gkCzs262AwCn4j0wQ8Cn4jcmw0CteHziQoC7N2XU2cEmlx9IBG5LlhNWRuVZovt1Slp",
                  "g1": "rdoEMS", "g2": "rdoPackage", "txtWeight": self.weight, "cbopackageSize": self.carton_size,
                  "g4": "rdoSPS22", "btnnext": "مرحله بعد"}    
        form2 = session.post('https://parcelprice.post.ir/default.aspx', data=data1)
        soup = BeautifulSoup(form2.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']

        #g3 can be: "rdoCity"(shahri) or "rdoBetweenCity"(beinshahri), but dont differrent in price at all, so we dont use "rdoCity".
        data2_2 = {"__EVENTTARGET": "cboFromState", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "g3": "rdoBetweenCity", "tlsDropDown": "0",
                   "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation, "cboFromState": from_state, "cboToState": ""}
        form2 = session.post('https://parcelprice.post.ir/default.aspx', data=data2_2)
        soup = BeautifulSoup(form2.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']
        
        data2_4 = {"__EVENTTARGET": "cboToState", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "g3": "rdoBetweenCity", "tlsDropDown": "0",
                   "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation, "cboFromState": from_state, "cboFromCity": from_town, "cboToState": to_state}
        form2 = session.post('https://parcelprice.post.ir/default.aspx', data=data2_4)
        soup = BeautifulSoup(form2.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']
        
        data2_5 = {"__EVENTTARGET": "cboToCity", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "g3": "rdoBetweenCity", "tlsDropDown": "0",
                   "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation, "cboFromState": from_state, "cboFromCity": from_town, "cboToState": to_state, "cboToCity": to_town}
        form2 = session.post('https://parcelprice.post.ir/default.aspx', data=data2_5)
        soup = BeautifulSoup(form2.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']

        data2_6 = {"__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "g3": "rdoBetweenCity", "tlsDropDown": "0", "btnnext": "مرحله بعد",
                   "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation, "cboFromState": from_state, "cboFromCity": from_town, "cboToState": to_state, "cboToCity": to_town}#g3 can be: "rdoCity"(shahri) or "rdoBetweenCity"(beinshahri) not for rdoCity you must not put cboToState and cboToCity 
        form3 = session.post('https://parcelprice.post.ir/default.aspx', data=data2_6)
        soup = BeautifulSoup(form3.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']

        data3 = {"__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "cboInsurType": "1", "DropDown_extra": "0", "btnnext": "مرحله بعد",
                 "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation}                                                                     #g3 can be: "rdoCity"(shahri) or "rdoBetweenCity"(beinshahri) not for rdoCity you must not put cboToState and cboToCity 
        form4 = session.post('https://parcelprice.post.ir/default.aspx', data=data3)
        soup = BeautifulSoup(form4.content.decode('UTF-8'), 'html.parser')

        try:
            price = soup.find('font', face="PostFont", color="Red", size="5").get_text()                              # if all thing was good soup contain price as: <font size="5" ..> price </font>  but if post didn't return price and raise error could be as: <font size="2" ..> error text </font>   as you see sizes are different
            price = ''.join(price[:-1].split(','))     #price is like: '199,545', we conver rial to toman (price[:-1]) and remove all ',' from number
            return Decimal(price)
        except:
            error_text = soup.find('font', face="PostFont", color="Red").get_text()
            return error_text


class make_next:                             #for adding next to list you shold use iter like:  list_with_next = iter(L) but for using that you should call like: next(list_with_next) or list_with_next.__init__() and you cant next of use list_with_next in template like next(list_with_next) or list_with_next.__next__ or list_with_next.__init__() is error you must define simple method as def next(self) insinde list_with_next for using intemplate like: list_with_next.next
    def __init__(self, list):
        self.list = iter(list)
    def next(self):
        try:                                                
            nex = next(self.list)
        except:                            #if we input blank list in make_next like:   ob = make_next([])  now ob.next or ob.next()  dont raise error and return blank list instead or loop more than len(L) like: L=[1,2,3] ob=make_next(L) now [ob.next() for i in range(30}] doesnt raise error and return blank list instead.                           
            nex = []
        return nex


# convert dict to object like: DictToObject({'spec': {'age': 22}}).spec.age==22, can also use list
class DictToObject:
    # 'data' can be dict or list of dicts (pass many=True)
    # if a serializer fields are 'a', 'b' and only 'a' provided in data, all_fields make b=None to prevent error
    def __init__(self, data, many=None, all_fields=None):
        self.items = None     # used in repr
        instance = CallBack(data=data)
        # we set self.sub_counter and self.data, to DictToObject (need in def repr, ...)
        for attr_name, attr_value in instance.__dict__.items():
            setattr(self, attr_name, attr_value)
        if isinstance(data, dict):   # data is dict
            if all_fields:
                # {'_id': None} will cause saving _id=None is db (in PostMongoSerializer)
                if all_fields.get('_id'):
                    del all_fields['_id']
                [setattr(instance, field, None) for field in all_fields if field not in data]
        # manage list and MongoDB cursor (col.find(....))
        elif isinstance(data, Iterable) and not isinstance(data, (str, bytes)):
            if not many:
                raise ValueError("class DictToObject: Iterable data type, pass 'many=True' to fix")
            if all_fields:
                for obj, dic in zip(instance, list(data)):
                    [setattr(obj, field, None) for field in all_fields if field not in dic]
            self.items = instance.items
        else:
            raise ValueError("Unsupported data type for conversion: must be dict or list of dicts")

    def __getitem__(self, key):
        if hasattr(self, "items"):
            return self.items[key]
        else:
            raise TypeError("Index access is not supported on this object")

    def __repr__(self):
        if self.sub_counter == 1:
            # in mongo cursor (.find()) self.data don't show actual data and needs to self.items
            data = self.items if self.items else self.data
            return f'Class {self.__class__.__name__}: ' + repr(data)
        return repr(self.data)


class CallBack:
    # sub_counter counts calls of CallBack like: CallBack(data) sub_counter==1 for use in __repr__
    def __init__(self, data, sub_counter=None):
        self.data = data
        self.sub_counter = 1 if not sub_counter else sub_counter
        if isinstance(data, dict):
            self.items = {}
            for key, value in data.items():
                # for keys like '240' now we can: obj['240'] and even obj['240'].image, instead obj.240 (error)
                if isinstance(key, int) or isinstance(key, str) and key.isdigit():
                    self.items[key] = self._convert(value)
                else:
                    setattr(self, key, self._convert(value))
        # manage list and MongoDB cursor (doc.find(....))
        elif isinstance(data, Iterable) and not isinstance(data, (str, bytes)):
            self.items = [self._convert(item) for item in data]

    def _convert(self, value):
        if isinstance(value, dict):
            return self.__class__(value, self.sub_counter + 1)
        elif isinstance(value, list):
            return [self._convert(item) for item in value]
        else:
            return value

    def __getitem__(self, key):
        if hasattr(self, "items"):
            return self.items[key]
        else:
            raise TypeError("Index access is not supported on this object")

    def __iter__(self):
        if self.items:
            return iter(self.items)

    def __repr__(self):
        if self.sub_counter == 1:
            return f'Class {self.__class__.__name__}: ' + repr(self.data)
        return repr(self.data)


class SaveProduct:
    # calls inside admin or serializer to create/update product and all it's relational fields in sql integrally
    def create_icon(data):
        if data.get('image'):
            obj = ImageCreationSizes(data=data, sizes=['240', '420', '640', '720', '960', '1280', 'default'])
            instances = obj.build(model=Image_icon, upload_to='products_images/icons/')
            Image_icon.objects.bulk_create(instances) if instances else None

    def update_icon(product, data, partial):
        instances, changed = [], False
        if not partial:  # here is for admin panel, we have to update icon only when it's really changes.
            fields = ['image', 'alt', 'path']
            first_icon = product.image_icon_set.first()
            for field in fields:
                if getattr(first_icon, field) != data[field]:
                    changed = True
                    alt = data['alt']
                    data['alt'] = alt[:alt.rfind('-')]
                    break
        # partial is True when sending data via api, 'changed' true when in admin panel one of icon fields are changed
        if partial or changed:
            instances = list(product.image_icon_set.all())
            obj = ImageCreationSizes(data=data, sizes=['240', '420', '640', '720', '960', '1280', 'default'])
            instances = obj.update(instances=instances, upload_to='products_images/icons/')
        with transaction.atomic():  # bulk_update doesn't work for 'image' field. this may improve speed a bit.
            for instance in instances:
                instance.save()

    def save_icon(data, product, partial=True):  # 'product' is product instance
        # data = {'image': InMemoryUploadFIle(...), 'alt': ..}, 'alt' is not required
        data['path'], data['product'] = 'products', product if not data.get('product') else data['product']
        image_icon_exits = product.image_icon_set.exists()
        if not image_icon_exits:
            SaveProduct.create_icon(data=data)
        else:
            SaveProduct.update_icon(product, data=data, partial=partial)

    def save_product(save_func, save_func_args, instance=None, data=None, partial=True):
        data = {} if not data else data
        length, width, height = data.get('length'), data.get('width'), data.get('height')
        if length and width and height:
            data['size'] = str(length) + ',' + str(width) + ',' + str(height)  # data is mutable with validated_data
        if data.get('size') and instance:  # in update, we have pre_instance
            instance.size = data['size']
        icon = data.pop('icon') if data.get('icon') else None
        product = save_func(**save_func_args)
        product = product if product else instance
        if icon:
            SaveProduct.save_icon(data=icon, product=product, partial=partial)
        return product
