from django.contrib.auth.models import Group
#from django.template.defaultfilters import slugify      this  slugify has not allow_unicode argument(from git)    
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.validators import UniqueValidator

from modeltranslation.utils import get_translation_fields as g_t
from drf_extra_fields.fields import Base64ImageField
from datetime import datetime
from pathlib import Path
import jdatetime
import re

from .models import *
from .methods import get_category_and_fathers, ImageCreationSizes, save_to_mongo, save_product
from users.models import User
from users.serializers import UserNameSerializer, UserSerializer
from users.methods import user_name_shown




class CommentSerializer(serializers.ModelSerializer):
    published_date = serializers.SerializerMethodField()
    author = UserNameSerializer(read_only=True)                                # this field must be read_only otherwise can't save like: c=CommentSerializer(data={'content': 'aaaaa', 'author': 1, 'reviewer': 1, 'product_id': 1}) c.is_valid() c.save()

    class Meta:
        model = Comment
        fields = '__all__'

    def to_representation(self, obj):
        self.fields['reply_comments'] = serializers.SerializerMethodField()
        return super().to_representation(obj)

    def get_published_date(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.published_date).timestamp())

    def get_reply_comments(self, obj):
        return CommentSerializer(obj.reply_comments.all(), many=True).data#ReplyCommentSerializer(obj.reply_comments.all(), many=True).data


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
            url = obj.image.url                 #request.build_absolute_uri()  is like "http://127.0.0.1:8000/product_list/"     and   request.build_absolute_uri(obj.image_icon.url) is like:  "http://192.168.114.6:8000/product_list/media/3.jpg" (request.build_absolute_uri() + obj.image_icon.url)
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
    image = serializers.SerializerMethodField()

    class Meta:
        model = Image_icon
        fields = ['id', 'image', *g_t('alt')]
        
    def get_image(self, obj):
        request = self.context.get('request', None)
        try:
            url = obj.image.url
        except:
            url = ''
        return url




class CategoryChainedSerializer(serializers.ModelSerializer):         #this is used for chane roost like: 'digital' > 'phone' > 'sumsung', also used in CategoryAdmin > category_save_to_mongo
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ['name', 'url']

    def get_url(self, obj):
        return reverse('main:products-list-cat', args=[1, obj.slug]) if obj.post_product == 'products' else reverse('main:posts-list-cat', args=[1, obj.slug])
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
            return reverse('main:products-list-cat', args=[1, obj.slug])
        else:
            return reverse('main:posts-list-cat', args=[1, obj.slug])


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
            return reverse('main:products-list-cat', args=[1, obj.slug])
        else:
            return reverse('main:posts-list-cat', args=[1, obj.slug])


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
            return reverse('main:products-list-cat', args=[1, obj.slug])
        else:
            return reverse('main:posts-list-cat', args=[1, obj.slug])




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
        result = {}
        for image_icon in obj.image_icon_set.all():
            size = re.split('[.-]', image_icon.image.url)[-2]
            result[size] = {'image': image_icon.image.url, 'alt': image_icon.alt}
        return result

    def get_published_date(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.published_date).timestamp())

    def get_category(self, obj):                                        #we must create form like: <form method="get" action="/posts/?obj.category.slug"> .  note form must shown as link.
        pk, slug = obj.id, obj.slug
        name, url = (obj.category.name, reverse('main:posts-list-cat', args=[1, obj.category.slug])) if obj.category else ('', '')       #post.category has null=True so this field can be blank like when you remove and category.
        return {'name': name, 'url': url}

    def get_author(self, obj):
        pk, slug = obj.id, obj.slug
        url = reverse('users:admin-profile', args=[obj.author.id]) if obj.author else ''
        return {'name': user_name_shown(obj.author), 'url': url}
    
    def get_url(self, obj):
        pk, slug = obj.id, obj.slug
        return reverse('main:post_detail', args=[pk, slug])




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
        return reverse('main:product_detail', args=[pk, slug])




class PostDetailSerializer(serializers.ModelSerializer):
    published_date = serializers.SerializerMethodField(read_only=True)
    updated = serializers.SerializerMethodField(read_only=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=30))
    comment_set = serializers.SerializerMethodField(read_only=True)
    image_icons = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = '__all__'

    def to_representation(self, obj):
        fields = super().to_representation(obj)
        fields['author'] = UserNameSerializer(obj.author).data
        fields['categories'] = CategoryChainedSerializer(get_category_and_fathers(obj.category), many=True).data
        return fields

    def get_published_date(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.published_date).timestamp())

    def get_updated(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.updated).timestamp())

    def get_comment_set(self, obj):
        # for every post, comments should be like:
        # [{'id':1,'content':'first comment', 'reply': None, 'reply_comments': [comment20, comment21,..]}, 'id': 2, ...
        return CommentSerializer(obj.comment_set.filter(reply=None), many=True).data

    def get_image_icons(self, obj):                                     #we must create form like: <form method="get" action="/posts/?obj.category.slug"> .  note form must shown as link. you can put that form in above of that post.
        result = {}
        for image_icon in obj.image_icon_set.all():
            size = re.split('[.-]', image_icon.image.url)[-2]
            result[size] = {'image': image_icon.image.url, 'alt': image_icon.alt}
        return result


class PostDetailMongoSerializer(PostDetailSerializer):
    # .save() require kwarg request
    # if for any reason we pot save_to_mongo to PostAdminForm.save instead here error will raise when save new post, because
    # post.published_date required, but form.instance.published_date only available after return instance in form.save
    def save(self, **kwargs):
        change = bool(self.instance)
        instance = super().save(**kwargs)
        obj = ImageCreationSizes(sizes=[240, 420, 640, 720, 960, 1280, 'default'], model=Image_icon, model_fields={'path': 'posts', 'post': instance})
        paths, instances = obj.create_images(file=self.data['file'], path='/media/posts_images/icons/')
        if instances:
            Image_icon.objects.bulk_create(instances)
        save_to_mongo(PostDetailMongo, instance, self, change, kwargs['request'])
        return instance


class ProductDetailSerializer(serializers.ModelSerializer):       # important: for saving we should first switch to `en` language by:  django.utils.translation.activate('en').    comment_set will optained by front in other place so we deleted from here.   more description:  # all keys should save in database in `en` laguage(for showing data you can select eny language) otherwise it was problem understading which language should select to run query on them like in:  s = my_serializers.ProductDetailMongoSerializer(form.instance, context={'request': request}).data['shopfilteritems']:     {'رنگ': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} it is false for saving, we should change language by  `activate('en')` and now true form for saving:  {'color': [{'id': 3, ..., 'name': 'سفید'}, {'id': 8, ..., 'name': 'طلایی'}]} and query like: s['color']
    categories = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    images = ImageSerializer(many=True, required=False)
    comment_count = serializers.SerializerMethodField()
    shopfilteritems = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', *g_t('name'), *g_t('slug'), *g_t('meta_title'), *g_t('meta_description'), *g_t('brief_description'), *g_t('detailed_description'), *g_t('price'), *g_t('available'), 'categories', 'category', 'brand', 'rating', *g_t('stock'), *g_t('weight'), 'images', 'comment_count', 'shopfilteritems', 'related_products']

    def get_categories(self, obj):
        category_and_fathers = get_category_and_fathers(obj.category)
        category_and_fathers.reverse()                           # to fixing display order in front we reversed!!
        return CategoryChainedSerializer(category_and_fathers, many=True).data

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
        request = self.context.get('request', None)
        related_products = Product.objects.filter(category=obj.category, visible=True).exclude(id=obj.id)[0:10] if obj.category else []
        if len(related_products) < 5 and obj.category and obj.category.father_category:                 #we must care obj.category had father_category
            child_categories = obj.category.father_category.child_categories.values_list('id')      #child_categories is like [(6,) , (7,)]
            child_categories_ids = [category[0] for category in child_categories]
            related_products = Product.objects.filter(category_id__in=child_categories_ids, visible=True).exclude(id=obj.id)[0:10-len(related_products)]

        related_serialized = []
        for product in related_products:
            name, price, image_icons = product.name, str(product.price), product.image_icon_set.all()              #rest_framework for default convert decimal fields to str, so we convert to str too.
            url = reverse('main:product_detail', args=[product.id, product.slug])
            image_icons = [{'image': im.image.url, 'alt': im.alt} for im in image_icons]
            related_serialized.append({'name': name, 'price': price, 'url': url, 'image_icons': image_icons})
        return related_serialized

    def save(self, **kwargs):
        # you can't call self.data in save(), 'validated_data' have to be used instead
        images = self.validated_data.pop('images') if self.validated_data.get('images') else None
        self.images = images
        return save_product(self.validated_data, super().save, super_func_args={**kwargs}, pre_instance=self.instance)

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
        if self.partial:        # update via api
            images_ids, data_images = [image['id'] for image in self.images], {image.pop('id'): image for image in self.images}
            for image in product.images.filter(id__in=images_ids):
                image_data = data_images[image.id]   # image_date is like: {'image': <SimpleUploadedFile...>, 'alt_fa': '..', ..}
                for key in image_data:
                    setattr(image, key, image_data[key])
                image.save()
        else:           # update with django api (generated when using serializer.mixins)
            data_images, product_images = {image.pop('id'): image for image in self.images}, product.images.all()
            instances = []
            for image in product_images:
                for attr, value in data_images[image.id].items():
                    setattr(image, attr, value) if getattr(image, attr) != value else None
                instances.append(image)

            if data_images:
                fields = list(data_images[product_images[0].id].keys())
                Image.objects.bulk_update(instances, fields)
        return product


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

    # .save() require kwarg request
    def save(self, **kwargs):
        # we save product in mongo in place: 1- admin.
        change = bool(self.instance)
        instance = super().save(**kwargs)
        save_to_mongo(ProductDetailMongo, instance, self, change, kwargs['request'])
        return instance


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['key', *g_t('name')]                            #we use key instead id for saving of states and towns. (id can be change in next db but key is more stable)


class TownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Town
        fields = ['key', *g_t('name')]                            #key is unique so dont need to state or other fields for saving ProfileOrder or ...
