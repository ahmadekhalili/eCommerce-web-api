from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxLengthValidator
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.urls import reverse

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

import re
import os
import pymongo
import environ
import datetime
import jdatetime
import urllib.parse
from urllib.parse import quote_plus
from modeltranslation.utils import get_translation_fields as g_t
from drf_extra_fields.fields import Base64ImageField
from pathlib import Path
from bson import ObjectId

from .models import *
from .methods import get_category_and_fathers, post_save_to_mongo, save_to_mongo, SaveProduct, DictToObject, \
    comment_save_to_mongo
from customed_files.rest_framework.classes.fields import *
from customed_files.rest_framework.classes.validators import MongoUniqueValidator

from users.models import User
from users.serializers import UserSerializer, UserNameSerializer
from users.methods import user_name_shown

env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))
username, password, db_name = quote_plus(env('MONGO_USERNAME')), quote_plus(env('MONGO_USERPASS')), env('MONGO_DBNAME')
host = env('MONGO_HOST')
uri = f"mongodb://{username}:{password}@{host}:27017/{db_name}?authSource={db_name}"
mongo_db = pymongo.MongoClient(uri)['akh_db']


class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply
        fields = ['id', 'comment']

    def to_representation(self, obj):
        self.fields['_id'] = IdMongoField(required=False)
        return super().to_representation(obj)


class CommentSerializer(serializers.ModelSerializer):
    published_date = TimestampField(jalali=True, required=False)
    author = UserNameSerializer(read_only=True)   # write handles in def to_internal_value. must overide default author field (here done)
    replies = serializers.SerializerMethodField(required=False)  # ReplySerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Comment
        fields = '__all__'

    def __init__(self, instance=None, request=None, mongo=False, **kwargs):
        # request use to fill .author (in writing), otherwise should provide author explicitly (in data)
        # in mongo=True, CommentSerializer is used like: validated = CommentSerializer(data={..}),
        # data = CommentSerializer(DictToObject(validated)).data
        self.request = request
        self.mongo = mongo
        super().__init__(instance, **kwargs)

    def to_representation(self, obj):
        self.fields['reviewer'] = UserNameSerializer(required=False)
        self.fields['_id'] = IdMongoField(required=False)
        fields = super().to_representation(obj)
        return fields

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        if data.get('author'):
            internal_value['author'] = get_object_or_404(User, id=data['author'])
        elif self.request and self.request.user:
            internal_value['author'] = self.request.user
        else:
            raise ValueError("please provide 'author' or login and request again")

        return internal_value

    def save(self, **kwargs):
        # here save only product (mongo&sql), post saves done manually in views
        change = bool(self.instance)
        instance = super().save(**kwargs)
        comment_save_to_mongo(mongo_db, instance, self, change, kwargs.get('request'))
        return instance

    def set_id(self, data):
        # receive list of comments and replies, add mongoid to them (to prepare saving in mongo). don't call in updating
        if data:
            if isinstance(data, list):      # list of comments
                for i, comment in enumerate(data):
                    data[i] = {'_id': ObjectId(), **comment}   # '-id' should be in first of dict
                    if comment.get('replies'):
                        for j, reply in enumerate(comment['replies']):
                            data[i][j] = {'_id': ObjectId, **reply}
            elif isinstance(data, dict):       # one comment
                data = {'_id': ObjectId(), **data}
                if data.get('replies'):
                    for j, reply in enumerate(data['replies']):
                        data[j] = {'_id': ObjectId, **reply}
        return data

    def field_filtering_for_update(self, input, output):  # input=request.data, output=serializer.data or..
        # keep only fields provided in request.data and remove unexpected which have been added in to_internal_value
        auto_now_fields = set()   # store 'auto_now=True' fields without duplicates
        for field_name, field in self.fields.items():
            if getattr(field, 'auto_now', False):
                auto_now_fields.add(field_name)

        model_class = self.Meta.model  # if there isn't any auto_now=True field in serializer, search it in model fields
        for field in model_class._meta.get_fields():
            if getattr(field, 'auto_now', False):
                auto_now_fields.add(field.name)

        for key in output.copy():
            if key not in input and key not in auto_now_fields:
                del output[key]
        return output

    def get_replies(self, obj):
        if not self.mongo:    # obj.replies.all works only in sql
            replies = obj.replies.all()
            if replies:
                return CommentSerializer(replies, many=True).data
        return []

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['rate']


class ImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    image = Base64ImageField(allow_null=True, label='تصویر', required=False)

    class Meta:
        model = Image
        fields = '__all__'

    def to_representation(self, obj):
        alts = g_t('alt')
        self.fields = {'id': self.fields['id'], 'image': serializers.SerializerMethodField(), **{alt: self.fields[alt] for alt in alts}}
        return super().to_representation(obj)

    def get_image(self, obj):
        try:
            url = obj.image.url
        except:
            url = ''
        return url

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        # below we remove UniqueValidator of 'all' fields (alt, all_fa, ..) to prevent 'error in updating' when using
        # mixins class based rest_framework.
        for name, field in self.fields.items():
            validators = field.validators.copy()
            for i in range(0, len(validators)):
                if name[:3] == 'alt' and isinstance(validators[i], UniqueValidator):
                    del field.validators[i]
        # note: field representation like 'print(field)' doesn't show validators truly, 'field.validators' is correct


class Image_iconSerializer(serializers.ModelSerializer):
    image = Base64ImageField(allow_null=True, required=False)

    class Meta:
        model = Image_icon
        # 'alt' must be here otherwise we will have problem in ProductDetailSerializer.save
        fields = ['id', 'image', *g_t('alt'), 'alt']

    def to_representation(self, obj):
        self.fields['image'] = serializers.SerializerMethodField()
        return super().to_representation(obj)

    def get_image(self, obj):
        self.context.get('request', None)
        try:
            url = obj.image.url
        except:
            url = ''
        return url


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# receive one cat list 'samsung', returns several cat: 'digital' > 'phone' > 'samsung'
class CategoryFathersChainedSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ['name', 'url']

    def __new__(cls, instance=None, revert=None, *args, **kwargs):
        if instance and kwargs.get('many'):
            cats = get_category_and_fathers(instance)
            if revert:
                cats.reverse()
            return super().__new__(cls, cats, **kwargs)
        return super().__new__(cls, *args, **kwargs)

    def get_url(self, obj):
        url = reverse('main:products-list-cat', args=[1, obj.slug]) if obj.post_product == 'products' else reverse('main:posts-list-cat', args=[1, obj.slug])
        return urllib.parse.unquote(url)
#'/products/categories/detail/{}/{}/'.format(obj.id, slugify(obj.name, allow_unicode=True))




class Sub2CategoryListSerializer(serializers.ModelSerializer):         #serialize categories with level=3
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    #child_categories = 'self'                                             #list just ids of childs.

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'level', 'post_product', 'father_category', 'str', 'url']

    def get_str(self, obj):
        return obj.__str__()

    def get_url(self, obj):
        if obj.post_product == 'product':
            url = reverse('main:products-list-cat', args=[1, obj.slug])
        else:
            url = reverse('main:posts-list-cat', args=[1, obj.slug])
        return urllib.parse.unquote(url)


class Sub1CategoryListSerializer(serializers.ModelSerializer):         #serialize categories with level=2
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    child_categories = Sub2CategoryListSerializer(many=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'level', 'post_product', 'father_category', 'str', 'url', 'child_categories']      #for better displaying order we list all field.

    def get_str(self, obj):
        return obj.__str__()

    def get_url(self, obj):
        if obj.post_product == 'product':
            url = reverse('main:products-list-cat', args=[1, obj.slug])
        else:
            url = reverse('main:posts-list-cat', args=[1, obj.slug])
        return urllib.parse.unquote(url)


class CategoryListSerializer(serializers.ModelSerializer):
    # representation like: {'name': 'digital', 'child_categories': {'name': 'PC', 'child_categories':
    # {'name': 'desktop', 'child_categories': {}}}
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    child_categories = Sub1CategoryListSerializer(many=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'level', 'post_product', 'father_category', 'str', 'url', 'child_categories']      #for better displaying order we list all field.

    def get_str(self, obj):
        return obj.__str__()

    def get_url(self, obj):
        if obj.post_product == 'product':
            url = reverse('main:products-list-cat', args=[1, obj.slug])
        else:
            url = reverse('main:posts-list-cat', args=[1, obj.slug])
        return urllib.parse.unquote(url)




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
        fields = ['id', *g_t('name'), *g_t('verbose_name'), 'genre', 'symbole', 'filter_attributes']




class FilterFromFilterAttribute(serializers.ModelSerializer):
    # here we receive filter_attribute and return filter fields +it's filter attributes like:
    # FilterFromFilterAttribute(some_filter_attributes, many=True).data and returns like:
    # [{'id': 1, 'verbose_name_fa': 'filter1'..., 'filter_attributes': [{'id': 1, 'name': 'filter_attr1'}, ...]},
    #  {'id': 2, 'verbose_name_fa': 'filter2'..., 'filter_attributes': [...]}]
    filter_attributes = serializers.SerializerMethodField()

    class Meta:
        model = Filter
        fields = ['id', *g_t('verbose_name'), 'genre', 'symbole', 'filter_attributes']

    def __new__(cls, *args, **kwargs):
        filter_attributes = next(iter(args), None) or kwargs.get('instance')
        if isinstance(filter_attributes[0], Filter_Attribute):           # __new__ calls several times recursively so statement(in below) like: super().__new__(cls, some_filters, **kwargs) can raise error if we don't put this condition.
            filter_filter_attribute = {}  # is like: {filter1: [filter_attribute1, filter_attribute2], filter2: [...]}
            for filter_attribute in filter_attributes:
                if filter_filter_attribute.get(filter_attribute.filterr):
                    filter_filter_attribute[filter_attribute.filterr] += [filter_attributes]
                else:
                    filter_filter_attribute[filter_attribute.filterr] = [filter_attribute]
            cls.filter_filter_attribute = filter_filter_attribute
            return super().__new__(cls, list(filter_filter_attribute.keys()), **kwargs)
        return super().__new__(cls, *args, **kwargs)

    def get_filter_attributes(self, obj):
        return Filter_AttributeListSerializer(self.filter_filter_attribute[obj], many=True).data


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'




class ProductListSerializer(serializers.ModelSerializer):
    image_icons = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField()                                        #RatingSerializer(read_only=True)
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', *g_t('name'), *g_t('slug'), *g_t('meta_title'), *g_t('meta_description'), *g_t('brief_description'), *g_t('price'), *g_t('available'), 'image_icons', 'rating', 'url']       #visible, filter_attributes, category are filtered(removed) here.

    def get_image_icons(self, obj):                                     #we must create form like: <form method="get" action="/posts/?obj.category.slug"> .  note form must shown as link. you can put that form in above of that post.
        result = {}
        for image_icon in obj.image_icon_set.all():
            size = re.split('[.-]', image_icon.image.url)[-2]
            result[size] = {'image': image_icon.image.url, 'alt': image_icon.alt}
        return result

    def get_rating(self, obj):
        rate = obj.rating.rate
        return rate
    
    def get_url(self, obj):
        pk, slug = obj.id, obj.slug
        return urllib.parse.unquote(reverse('main:product_detail', args=[pk, slug]))



# don't use this for representation like: PostMongoSerializer(DictToObject(post_col)).data
# in updating must be like: PostMongoSerializer(pk=1, data=data, partial=True, request=request)
# in creation: PostMongoSerializer(data=data, prequest=request)
class PostMongoSerializer(serializers.Serializer):
    # [title, brief_description, request.user/author required
    title = serializers.CharField(label=_('title'), validators=[MongoUniqueValidator(mongo_db.post, 'title')], max_length=255)
    slug = serializers.SlugField(label=_('slug'), required=False)    # slug generates from title (in to_internal_value)
    published_date = TimestampField(label=_('published date'), jalali=True, required=False)
    updated = TimestampField(label=_('updated date'), jalali=True, auto_now=True, required=False)
    tags = serializers.ListField(child=serializers.CharField(max_length=30), default=[])
    meta_title = serializers.CharField(allow_blank=True, max_length=60, required=False)
    meta_description = serializers.CharField(allow_blank=True, required=False, validators=[MaxLengthValidator(160)])
    brief_description = serializers.CharField(validators=[MaxLengthValidator(1000)])
    detailed_description = serializers.CharField(allow_blank=True, required=False)
    instagram_link = serializers.CharField(allow_blank=True, max_length=255, required=False)
    visible = serializers.BooleanField(default=True)
    author = UserNameSerializer()  # author can fill auto in to_internal_value, otherwise must input
    icons = OneToMultipleImage(sizes=[240, 420, 640, 720, 960, 1280, 'default'], upload_to='post_images/icons/', required=False)
    category_fathers = serializers.SerializerMethodField()
    category = CategorySerializer(required=False, read_only=True)  # it's validated_data fill in 'to_internal_value'
    comments = CommentSerializer(many=True, required=False)

    def __init__(self, instance=None, pk=None, *args, **kwargs):
        # instance and pk should not conflict in updating and retrieving like: updating: serializer(pk=1, data={..}),
        # retrieving: serializer(instance).data
        self.request = kwargs.pop('request', None)
        self.pk = pk
        if kwargs.get('partial'):      # in updating only provided fields should validate
            for key in self.fields:
                self.fields[key].required = False
        super().__init__(instance=instance, *args, **kwargs)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        rep2 = representation.copy()
        if self.partial:
            for key in rep2:    # can't change dictionary (representation) size during iteration
                if representation.get(key) is None:
                    representation.pop(key)
        return representation

    def to_internal_value(self, data):
        if not data.get('slug') and data.get('title'):  # correct updating, required change data['slug'] here.
            data['slug'] = slugify(data['title'], allow_unicode=True)  # data==request.data==self.initial_data mutable
        internal_value = super().to_internal_value(data)

        now = datetime.datetime.now()
        if not self.pk:         # in creation
            internal_value['published_date'] = self.fields['published_date'].to_internal_value(now.timestamp())
        internal_value['updated'] = self.fields['updated'].to_internal_value(now.timestamp())

        if data.get('category'):
            level = Category.objects.filter(id=data['category']).values_list('level', flat=True)[0]
            related = 'father_category'
            # '__father_category' * -1 == '', prefetch_related('child_categories') don't need because of single category
            i = Category._meta.get_field('level').validators[1].limit_value-1-level  # raise error when use directly!
            related += '__father_category' * i
            cat = Category.objects.filter(id=data['category']).select_related(related)[0]
            internal_value['category_fathers'] = cat
            internal_value['category'] = cat

        if self.request:
            if self.request.user:
                internal_value['author'] = self.request.user
            else:
                raise ValidationError({'author': 'please login to fill post.author'})
        elif data.get('author'):
            internal_value['author'] = get_object_or_404(User, id=data['author'])
        else:
            raise ValidationError({'author': "please login and pass 'request' parameter or add user id manually"})

        return internal_value

    def is_valid(self, *, raise_exception=False):  # separate is_valid behaviour in updating / creation
        validated_data, errors = {}, {}
        if self.pk:   # in updating phase, run validation for only provided fields (in data)
            for field_name in self.initial_data:  # self.initial_data == data passed to serialize
                try:
                    field = self.fields[field_name]
                    validated_data[field_name] = field.run_validation(self.initial_data[field_name])
                except ValidationError as exc:
                    validated_data = {}
                    errors[field_name] = exc.detail
                else:     # in creation, do DRF default behaviour
                    errors = {}
                if errors and raise_exception:
                    raise ValidationError(errors)
            validated_data = {**validated_data, **self.to_internal_value(self.initial_data)}
            return validated_data

        else:         # in creation, do DRF default behaviour
            return super().is_valid(raise_exception=raise_exception)

    # only save in mongo db
    def save(self, **kwargs):
        change = True if self.pk else False
        if not change:
            return self.create(self.validated_data)
        else:
            return self.update(self.pk, kwargs['validated_data'])

    def create(self, validated_data):
        data = PostMongoSerializer(DictToObject(validated_data)).data
        PostMongoSerializer().fields['comments'].child.set_id(data.get('comments'))
        return post_save_to_mongo(post_col=mongo_db.post, data=data, change=False)

    def update(self, pk, validated_data):
        # because partial=True don't raise error when 'validated_data' doesn't provide required fields
        data = PostMongoSerializer(DictToObject(validated_data), partial=True).data
        data = self.field_filtering_for_update(self.initial_data, data)
        return post_save_to_mongo(mongo_db.post, pk, data, change=True)

    def field_filtering_for_update(self, input, output):  # 'input', 'output' is dict
        # keep only fields provided in request.data and remove unexpected which have been added in to_internal_value
        auto_now_fields = dict(self.fields).copy()   # store 'auto_now=True' fields
        for key in self.fields:
            if not getattr(auto_now_fields[key], 'auto_now', None):
                del auto_now_fields[key]
        for key in output.copy():
            if key not in input and key not in auto_now_fields:
                del output[key]
        return output

    def get_category_fathers(self, obj):
        if getattr(obj, 'category', None):
            return CategoryFathersChainedSerializer(obj.category, revert=True, many=True).data


class PostListSerializer(serializers.Serializer):
    title = serializers.CharField(label=_('title'), max_length=255)
    slug = serializers.SlugField(label=_('slug'), required=False)    # slug generates from title (in to_internal_value)
    published_date = TimestampField(label=_('published date'), jalali=True, required=False)
    updated = TimestampField(label=_('updated date'), jalali=True, required=False)
    tags = serializers.ListField(child=serializers.CharField(max_length=30), default=[])
    meta_title = serializers.CharField(allow_blank=True, max_length=60, required=False)
    meta_description = serializers.CharField(allow_blank=True, required=False, validators=[MaxLengthValidator(160)])
    brief_description = serializers.CharField(validators=[MaxLengthValidator(1000)])
    url = serializers.SerializerMethodField()  # show simple str before data/list (in serializer(...).data)
    author = serializers.SerializerMethodField()  # author will fill auto from request.user, otherwise must input
    icons = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()  # it's validated_data fill in 'to_internal_value'

    def get_url(self, obj):
        pk, slug = str(obj._id), obj.slug
        return urllib.parse.unquote(reverse('main:post_detail', args=[pk, slug]))

    def get_author(self, obj):
        if getattr(obj, 'author', None):
            author = obj.author
            if author:
                url = urllib.parse.unquote(reverse('users:admin-profile', args=[author.id]))
                return {'url': url, 'user_name': author.user_name}

    def get_icons(self, obj):
        if getattr(obj, 'icons', None):
            icons, result = obj.icons, {}
            if icons:
                for size in icons:
                    icon = icons[size]
                    result[size] = {'image': icon.image, 'alt': icon.alt}
                return result

    def get_category(self, obj):
        if getattr(obj, 'category', None):
            cat = obj.category
            name = cat.name
            url = urllib.parse.unquote(reverse('main:posts-list-cat', args=[1, cat.slug]))
        else:
            name, url = ('', '')
        return {'name': name, 'url': url}


class ProductDetailSerializer(serializers.ModelSerializer):       # important: for saving we should first switch to `en` language by:  django.utils.translation.activate('en').    comment_set will optained by front in other place so we deleted from here.   more description:  # all keys should save in database in `en` laguage(for showing data you can select eny language) otherwise it was problem understading which language should select to run query on them like in:  s = my_serializers.ProductDetailMongoSerializer(form.instance, context={'request': request}).data['shopfilteritems']:     {'رنگ': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} it is false for saving, we should change language by  `activate('en')` and now true form for saving:  {'color': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} and query like: s['color']
    slug = serializers.SlugField(required=False)
    category_fathers = CategoryFathersChainedSerializer(many=True, revert=True)
    brand = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    images = ImageSerializer(many=True, required=False)
    icon = Image_iconSerializer(write_only=True, required=False)
    comment_count = serializers.SerializerMethodField()
    shopfilteritems = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', *g_t('name'), *g_t('slug'), *g_t('meta_title'), *g_t('meta_description'), *g_t('brief_description'), *g_t('detailed_description'), *g_t('price'), *g_t('available'), 'category_fathers', 'category', 'brand', 'rating', *g_t('stock'), *g_t('weight'), 'images', 'icon', 'comment_count', 'shopfilteritems', 'related_products']

    def get_brand(self, obj):
        try:
            return obj.brand.name
        except:
            return ''

    def get_rating(self, obj):
        rate = obj.rating.rate
        return rate

    def get_comment_count(self, obj):
        count = obj.comment_set.count()
        return count

    def get_shopfilteritems(self, obj):                                         # return value is like:  "shopfilteritems": { "رنگ": [ { "id": 3, "name": "سفید", "previous_stock": 12, ...}, { "id": 8, "name": "طلایی", "previous_stock": 8, ...}]}
        shopfilteritems, data = obj.shopfilteritems.all(), {}
        for shopfilteritem in shopfilteritems:
            filter_name = str(_(shopfilteritem.filter_attribute.filterr.name))                  # filter_name should be str not __proxy__,  otherwise can't be used as key in data[filter_name]
            data[filter_name] = [ShopFilterItemSerializer(shopfilteritem).data] if not data.get(filter_name) else [*data[filter_name], ShopFilterItemSerializer(shopfilteritem).data]
        return data

    def get_related_products(self, obj):
        self.context.get('request', None)
        related_products = Product.objects.filter(category=obj.category, visible=True).exclude(id=obj.id)[0:10] if obj.category else []
        if len(related_products) < 5 and obj.category and obj.category.father_category:                 #we must care obj.category had father_category
            child_categories = obj.category.father_category.child_categories.values_list('id')      #child_categories is like [(6,) , (7,)]
            child_categories_ids = [category[0] for category in child_categories]
            related_products = Product.objects.filter(category_id__in=child_categories_ids, visible=True).exclude(id=obj.id)[0:10-len(related_products)]

        related_serialized = []
        for product in related_products:
            name, price, image_icons = product.name, str(product.price), product.image_icon_set.all()              #rest_framework for default convert decimal fields to str, so we convert to str too.
            url = urllib.parse.unquote(reverse('main:product_detail', args=[product.id, product.slug]))
            image_icons = [{'image': im.image.url, 'alt': im.alt} for im in image_icons]
            related_serialized.append({'name': name, 'price': price, 'url': url, 'image_icons': image_icons})
        return related_serialized

    def save(self, **kwargs):
        # save_product calls in both serializer and admin
        # you can't call self.data in save(), 'validated_data' have to be used instead. it is important save_product
        # runs in both update, create. so in updating: product.images[0].image, we are sure image sizes will change too.
        self.images = self.validated_data.pop('images') if self.validated_data.get('images') else None
        if not self.validated_data.get('slug'):
            self.validated_data['slug'] = slugify(self.validated_data['name'], allow_unicode=True)
        return SaveProduct.save_product(save_func=super().save, save_func_args={**kwargs}, instance=self.instance,
                                            data=self.validated_data)

    def create(self, validated_data):
        product = super().create(validated_data)
        if self.images:
            images = [Image(**image) for image in self.images]
            Image.objects.bulk_create(images)
        return product

    def update(self, instance, validated_data):
        # images (in request.data) must specify 'id' (to retrieve an update that image)
        # bulk_update can't be done because fields to update are not constant
        # (we can specify different field for every image)
        product = super().update(instance, validated_data)
        self.update_images(product)   # update product images
        return product

    def update_images(self, product):
        if self.partial and self.images:       # update via api (send only specefic field of Image model)
            images_ids, data_images = [image['id'] for image in self.images], {image.pop('id'): image for image in self.images}
            for image in product.images.filter(id__in=images_ids):
                image_data = data_images[image.id]   # image_date is like: {'image': <SimpleUploadedFile...>, 'alt_fa': '..', ..}
                for key in image_data:
                    setattr(image, key, image_data[key])
                image.save()
        elif self.images:  # update when send all images of product with all fields (using mixins.RetrieveModelMixin)
            data_images, product_images = {image.pop('id'): image for image in self.images}, product.images.all()
            instances = []
            for image in product_images:
                for attr, value in data_images[image.id].items():
                    setattr(image, attr, value) if getattr(image, attr) != value else None
                instances.append(image)

            if data_images:
                fields = list(data_images[product_images[0].id].keys())
                Image.objects.bulk_update(instances, fields)


class ProductDetailMongoSerializer(ProductDetailSerializer):
    # here is for representing data in /products/detail/ page. so purpose in here is not creating product in mongo, it
    # is for data providing for product_detail page.
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

    # .save() require kwarg request
    def save(self, **kwargs):
        # we save product in mongo in places: 1- admin 2- serializer
        change = bool(self.instance)
        instance = super().save(**kwargs)
        save_to_mongo(mongo_db[settings.MONGO_PRODUCT_COL], instance, self, change, kwargs.get('request'))
        return instance


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['key', *g_t('name')]                            #we use key instead id for saving of states and towns. (id can be change in next db but key is more stable)


class TownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Town
        fields = ['key', *g_t('name')]                            #key is unique so dont need to state or other fields for saving ProfileOrder or ...
