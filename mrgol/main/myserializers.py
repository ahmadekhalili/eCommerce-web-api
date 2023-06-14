from django.contrib.auth.models import Group
#from django.template.defaultfilters import slugify      this  slugify has not allow_unicode argument(from git)    
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from modeltranslation.utils import get_translation_fields as g_t
from datetime import datetime
from pathlib import Path
import jdatetime
import re

from .models import *
from .mymethods import get_category_and_fathers
from users.models import User
from users.myserializers import UserNameSerializer
from users.myserializers import UserSerializer
from users.mymethods import user_name_shown




class CommentSerializer(serializers.ModelSerializer):
    published_date = serializers.SerializerMethodField()
    author = UserNameSerializer(read_only=True)                                # this field must be read_only otherwise can't save like: c=CommentSerializer(data={'content': 'aaaaa', 'author': 1, 'reviewer': 1, 'product_id': 1}) c.is_valid() c.save()
    class Meta:
        model = Comment
        fields = '__all__'

    def get_published_date(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.published_date).timestamp())
    
class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['rate']

class ImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  
    class Meta:
        model = Image
        fields = ['id', 'image', *g_t('alt')]
        
    def get_image(self, obj):
        request = self.context.get('request', None)
        try:
            url = request.build_absolute_uri(obj.image.url)                 #request.build_absolute_uri()  is like "http://127.0.0.1:8000/product_list/"     and   request.build_absolute_uri(obj.image_icon.url) is like:  "http://192.168.114.6:8000/product_list/media/3.jpg" (request.build_absolute_uri() + obj.image_icon.url)
        except:
            url = ''
        return url


class SmallImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  
    father = ImageSerializer()
    class Meta:
        model = SmallImage
        fields = ['id', 'image', *g_t('alt'), 'father']
        
    def get_image(self, obj):
        request = self.context.get('request', None)
        try:
            url = request.build_absolute_uri(obj.image.url)
        except:
            url = ''
        return url


class Image_iconSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  
    class Meta:
        model = Image_icon
        fields = ['id', 'image', *g_t('alt')]
        
    def get_image(self, obj):
        request = self.context.get('request', None)
        try:
            url = request.build_absolute_uri(obj.image.url)
        except:
            url = ''
        return url




class CategoryChainedSerializer(serializers.ModelSerializer):         #this is used for chane roost like: 'digital' > 'phone' > 'sumsung'
    class Meta:
        model = Category
        fields = [*g_t('name'), *g_t('slug')]
#'/products/categories/detail/{}/{}/'.format(obj.id, slugify(obj.name, allow_unicode=True))




class Sub2CategoryListSerializer(serializers.ModelSerializer):         #serialize categories with level=3
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    #child_categories = 'self'                                             #list just ids of childs.

    class Meta:
        model = Category
        fields = ['id', *g_t('name'), *g_t('slug'), 'level', 'post_product', 'father_category', 'str', 'url']

    def get_str(self, obj):
        return obj.__str__()

    def get_url(self, obj):
        if obj.post_product == 'product':
            return f'/products/{obj.slug}/'
        else:
            return f'/posts/{obj.slug}/'


class Sub1CategoryListSerializer(serializers.ModelSerializer):         #serialize categories with level=2
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    child_categories = Sub2CategoryListSerializer(many=True)
    
    class Meta:
        model = Category
        fields = ['id', *g_t('name'), *g_t('slug'), 'level', 'post_product', 'father_category', 'str', 'url', 'child_categories']      #for better displaying order we list all field.

    def get_str(self, obj):
        return obj.__str__()

    def get_url(self, obj):
        if obj.post_product == 'product':
            return f'/products/{obj.slug}/'
        else:
            return f'/posts/{obj.slug}/'


class CategoryListSerializer(serializers.ModelSerializer):         #urs for products should be like: /products/?slug  and for post should be likst /posts/?slug   note CategoryListSerializer should be before PostListSerializer
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    child_categories = Sub1CategoryListSerializer(many=True)
    
    class Meta:
        model = Category
        fields = ['id', *g_t('name'), *g_t('slug'), 'level', 'post_product', 'father_category', 'str', 'url', 'child_categories']      #for better displaying order we list all field.

    def get_str(self, obj):
        return obj.__str__()

    def get_url(self, obj):
        if obj.post_product == 'product':
            return f'/products/{obj.slug}/'
        else:
            return f'/posts/{obj.slug}/'




class ShopFilterItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopFilterItem
        fields = '__all__'

    def to_representation(self, obj):                 # supose: serializer1=ShopFilterItemSerializer(ShopFilterItem_1).data  we use this serializer at least in two places. 1- for showing to user ShopFilterItems of a product in website (exatly like popular websites) in this structure:   ShopFilterItem_1.filter_attribute.filterr.name: {serializer1['name'], serializer3['name']}  this is like: 'rangh': {'narenji', 'sefid', 'meshki'}   2- for filing html input is like(shematic): <input type="radio" name=serializer['name'] value=serializer['id']>  and this is like digikala  structure too!
        self.fields['name'] = serializers.SerializerMethodField()
        fields = super().to_representation(obj)
        del fields['product']
        del fields['filter_attribute']
        return fields

    def get_name(self, obj):
        return obj.filter_attribute.name




class Filter_AttributeListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Filter_Attribute
        fields = '__all__'
        
    def to_representation(self, obj):
        fields = super().to_representation(obj)
        del fields['filterr']
        return fields




class FilterSerializer(serializers.ModelSerializer):
    filter_attributes = Filter_AttributeListSerializer(many=True)
    class Meta:
        model = Filter
        fields = ['id', *g_t('name'), 'filter_attributes']




class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'




class PostListSerializer(serializers.ModelSerializer):
    published_date = serializers.SerializerMethodField()
    tags = serializers.ListField(child=serializers.CharField(max_length=30))
    image_icons = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()                                 #showing solo str datas like 'url' before dict/list type datas like image_icons, category, author  is more readable and clear.

    class Meta:
        model = Post
        fields = ['id', *g_t('title'), *g_t('slug'), *g_t('meta_title'), *g_t('meta_description'), *g_t('brief_description'), 'published_date', 'tags', 'image_icons', 'category', 'author', 'url']

    def get_image_icons(self, obj):                                     #we must create form like: <form method="get" action="/posts/?obj.category.slug"> .  note form must shown as link. you can put that form in above of that post.
        base_path, result = str(Path(__file__).resolve().parent.parent), {}
        for image_icon in obj.image_icon_set.all():
            size = re.split('[.-]', image_icon.image.path)[-2]
            result[size] = {'image': image_icon.image.path, 'alt': image_icon.alt}
        return result

    def get_published_date(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.published_date).timestamp())

    def get_category(self, obj):                                        #we must create form like: <form method="get" action="/posts/?obj.category.slug"> .  note form must shown as link.
        pk, slug = obj.id, obj.slug
        name, url = (obj.category.name, f'/posts/{obj.category.slug}/') if obj.category else ('', '')       #post.category has null=True so this field can be blank like when you remove and category.
        return {'name': name, 'url': url}

    def get_author(self, obj):
        pk, slug = obj.id, obj.slug
        return {'name': user_name_shown(obj.author), 'url': '/users/profile/admin/{}/'.format(obj.author.id)}
    
    def get_url(self, obj):
        pk, slug = obj.id, obj.slug
        return f'/posts/detail/{pk}/{slug}/'




class ProductListSerializer(serializers.ModelSerializer):
    image_icons = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField()                                        #RatingSerializer(read_only=True)
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', *g_t('name'), *g_t('slug'), *g_t('meta_title'), *g_t('meta_description'), *g_t('brief_description'), *g_t('price'), *g_t('available'), 'image_icons', 'rating', 'url']       #visible, filter_attributes, category are filtered(removed) here.

    def get_image_icons(self, obj):                                     #we must create form like: <form method="get" action="/posts/?obj.category.slug"> .  note form must shown as link. you can put that form in above of that post.
        base_path, result = str(Path(__file__).resolve().parent.parent), {}
        for image_icon in obj.image_icon_set.all():
            size = re.split('[.-]', image_icon.image.path)[-2]
            result[size] = {'image': image_icon.image.path, 'alt': image_icon.alt}
        return result

    def get_rating(self, obj):
        rate = obj.rating.rate
        return rate
    
    def get_url(self, obj):
        pk, slug = obj.id, obj.slug
        return f'/products/detail/{pk}/{slug}/'




class PostDetailSerializer(serializers.ModelSerializer):
    published_date = serializers.SerializerMethodField(read_only=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=30))
    comment_set = CommentSerializer(read_only=True, many=True)
    image_icons = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = '__all__'

    def to_representation(self, obj):
        fields = super().to_representation(obj)
        fields['author'] = UserNameSerializer(obj.author).data
        fields['category'] = self.get_category(obj)
        return fields

    def get_published_date(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.published_date).timestamp())
    
    def get_category(self, obj):                                     #we must create form like: <form method="get" action="/posts/?obj.category.slug"> .  note form must shown as link. you can put that form in above of that post.
        pk, slug = obj.id, obj.slug
        name, url = (obj.category.name, f'/posts/{obj.category.slug}/') if obj.category else ('', '')       #post.category has null=True so this field can be blank like when you remove and category.
        return {'name': name, 'url': url}

    def get_image_icons(self, obj):                                     #we must create form like: <form method="get" action="/posts/?obj.category.slug"> .  note form must shown as link. you can put that form in above of that post.
        base_path, result = str(Path(__file__).resolve().parent.parent), {}
        for image_icon in obj.image_icon_set.all():
            size = re.split('[.-]', image_icon.image.path)[-2]
            result[size] = {'image': image_icon.image.path, 'alt': image_icon.alt}
        return result


class ProductDetailSerializer(serializers.ModelSerializer):       # important: for saving we should first switch to `en` language by:  django.utils.translation.activate('en').    comment_set will optained by front in other place so we deleted from here.   more description:  # all keys should save in database in `en` laguage(for showing data you can select eny language) otherwise it was problem understading which language should select to run query on them like in:  s = myserializers.ProductDetailMongoSerializer(form.instance, context={'request': request}).data['shopfilteritems']:     {'رنگ': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} it is false for saving, we should change language by  `activate('en')` and now true form for saving:  {'color': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} and query like: s['color']
    categories = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    smallimages = SmallImageSerializer(many=True)
    comment_count = serializers.SerializerMethodField()
    shopfilteritems = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', *g_t('name'), *g_t('slug'), *g_t('meta_title'), *g_t('meta_description'), *g_t('brief_description'), *g_t('detailed_description'), *g_t('price'), *g_t('available'), 'categories', 'brand', 'rating', *g_t('stock'), *g_t('weight'), 'smallimages', 'comment_count', 'shopfilteritems', 'related_products']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['smallimages'].context['request'] = request

    def get_categories(self, obj):
        category_and_fathers = get_category_and_fathers(obj.category)
        category_and_fathers.reverse()                           #to fixing display order in front we reversed!!
        return CategoryChainedSerializer(category_and_fathers, many=True).data

    def get_brand(self, obj):
        return obj.brand.name

    def get_rating(self, obj):
        rate = obj.rating.rate
        return rate

    def get_comment_count(self, obj):
        rate = obj.comment_set.count()
        return rate

    def get_shopfilteritems(self, obj):                                         # return value is like:  "shopfilteritems": { "رنگ": [ { "id": 3, "name": "سفید", "previous_stock": 12, ...}, { "id": 8, "name": "طلایی", "previous_stock": 8, ...}]}
        shopfilteritems, data = obj.shopfilteritems.all(), {}
        for shopfilteritem in shopfilteritems:
            filter_name = str(_(shopfilteritem.filter_attribute.filterr.name))                  # filter_name should be str not __proxy__,  otherwise can't be used as key in data[filter_name]
            data[filter_name] = [ShopFilterItemSerializer(shopfilteritem).data] if not data.get(filter_name) else [*data[filter_name], ShopFilterItemSerializer(shopfilteritem).data]
        return data

    def get_related_products(self, obj):
        request = self.context.get('request', None)
        related_products = Product.objects.filter(category=obj.category, visible=True).exclude(id=obj.id)[0:10] if obj.category else []
        if len(related_products) < 5 and obj.category and obj.category.father_category:                 #we must care obj.category had father_category
            child_categories = obj.category.father_category.child_categories.values_list('id')      #child_categories is like [(6,) , (7,)]
            child_categories_ids = [category[0] for category in child_categories]
            related_products = Product.objects.filter(category_id__in=child_categories_ids, visible=True).exclude(id=obj.id)[0:10-len(related_products)]

        related_serialized = []
        for product in related_products:
            name, price, image_icon = product.name, str(product.price), product.image_icon              #rest_framework for default convert decimal fields to str, so we convert to str too.
            url = '/products/detail/{}/{}/'.format(product.id, product.slug)
            image_icon_url = request.build_absolute_uri(image_icon.image.url) if image_icon else ''
            alt = image_icon.alt
            related_serialized.append({'name': name, 'price': price, 'url': url, 'image_icon': {'image': image_icon_url, 'alt': alt}})
        return related_serialized




class ProductDetailMongoSerializer(ProductDetailSerializer):    # we create/edit mongo product by receive data from this
    filters = serializers.SerializerMethodField()  
    comment_set = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Product
        fields = ProductDetailSerializer.Meta.fields + ['filters', 'comment_set']

    def get_filters(self, obj):
        filter_filter_attribute = {}                                              # is like: {'rang': ['abi', germez'], 'size': ['large'], ...}
        for filter_attribute in obj.filter_attributes.all():
            if filter_filter_attribute.get(filter_attribute.filterr.name):
                filter_filter_attribute[filter_attribute.filterr.name] += [filter_attribute.name]
            else:
                filter_filter_attribute[filter_attribute.filterr.name] = [filter_attribute.name]
        return filter_filter_attribute


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['key', *g_t('name')]                            #we use key instead id for saving of states and towns. (id can be change in next db but key is more stable)


class TownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Town
        fields = ['key', *g_t('name')]                            #key is unique so dont need to state or other fields for saving ProfileOrder or ...
