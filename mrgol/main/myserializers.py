from django.contrib.auth.models import Group
#from django.template.defaultfilters import slugify      this  slugify has not allow_unicode argument(from git)    
from django.utils.text import slugify

from rest_framework import serializers

from datetime import datetime

from customed_files.date_convertor import MiladiToShamsi
from .models import *
from .mymethods import get_root_and_fathers
from users.models import User
from users.myserializers import UserNameSerializer
from users.myserializers import UserSerializer
from users.mymethods import user_name_shown




class CommentSerializer(serializers.ModelSerializer):
    #author = UserNameSerializer()                                #puting author here we cant write comment like this: c=CommentSerializer(data={'content': 'aaaaa', 'author': 1, 'confermer': 1, 'product_id': 1}) c.is_valid() c.save()    so we put this field only in reading show by puting that in method to_representation
    class Meta:
        model = Comment
        fields = '__all__'
        
    def to_representation(self, obj):
        self.fields['author'] = UserNameSerializer(read_only=True)                
        return super().to_representation(obj)
    
class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['rate']

class ImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  
    class Meta:
        model = Image
        fields = ['id', 'image', 'alt']
        
    def get_image(self, obj):
        request = self.context.get('request', None)
        try:
            url = request.build_absolute_uri(obj.image.url)                 #request.build_absolute_uri()  is like "http://127.0.0.1:8000/product_list/"     and   request.build_absolute_uri(obj.image_icon.url) is like:  "http://192.168.114.6:8000/product_list/media/3.jpg" (request.build_absolute_uri() + obj.image_icon.url)
        except:
            url = ''                                                        #if obj have not image(obj.image_icone was blank) this line will run. 
        return url

    
class SmallImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  
    father = ImageSerializer()
    class Meta:
        model = SmallImage
        fields = ['id', 'image', 'alt', 'father']
        
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
        fields = ['id', 'image', 'alt']
        
    def get_image(self, obj):
        request = self.context.get('request', None)
        try:
            url = request.build_absolute_uri(obj.image.url)
        except:
            url = ''
        return url




class RootChainedSerializer(serializers.ModelSerializer):         #this is used for chane roost like: 'digital' > 'phone' > 'sumsung'    
    class Meta:
        model = Root
        fields = ['name', 'slug']
#'/products/roots/detail/{}/{}/'.format(obj.id, slugify(obj.name, allow_unicode=True))




class Sub2RootListSerializer(serializers.ModelSerializer):         #serialize roots with level=3
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    #root_childs = 'self'                                             #list just ids of childs.

    class Meta:
        model = Root
        fields = ['id', 'name', 'slug', 'level', 'post_product', 'father_root', 'str', 'url']

    def get_str(self, obj):
        return obj.__str__()

    def get_url(self, obj):
        if obj.post_product == 'product':
            return f'/products/{obj.slug}/'
        else:
            return f'/posts/{obj.slug}/'


class Sub1RootListSerializer(serializers.ModelSerializer):         #serialize roots with level=2
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    root_childs = Sub2RootListSerializer(many=True)
    
    class Meta:
        model = Root
        fields = ['id', 'name', 'slug', 'level', 'post_product', 'father_root', 'str', 'url', 'root_childs']      #for better displaying order we list all field.

    def get_str(self, obj):
        return obj.__str__()

    def get_url(self, obj):
        if obj.post_product == 'product':
            return f'/products/{obj.slug}/'
        else:
            return f'/posts/{obj.slug}/'


class RootListSerializer(serializers.ModelSerializer):         #urs for products should be like: /products/?slug  and for post should be likst /posts/?slug   note RootListSerializer should be before PostListSerializer
    str = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    root_childs = Sub1RootListSerializer(many=True)
    
    class Meta:
        model = Root
        fields = ['id', 'name', 'slug', 'level', 'post_product', 'father_root', 'str', 'url', 'root_childs']      #for better displaying order we list all field.

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

    def to_representation(self, obj):  #supose: serializer=ShopFilterItemSerializer(ShopFilterItem).data  we use this serializer at least in two places. 1- for showing to user ShopFilterItems of a product in website (exatly like digikala) in this structure:  serializer['name']: serializer['filter_name'] this is like: rangh: narenji   2- for filing html input is like(shematic): <input type="radio" name=serializer['filter_name'] value=serializer['id']>  and this is like digikala  structure too!
        self.fields['name'] = serializers.SerializerMethodField()
        self.fields['filter_name'] = serializers.SerializerMethodField() 
        fields = super().to_representation(obj)
        del fields['product']
        del fields['filter_attribute']
        return fields

    def get_name(self, obj):
        return obj.filter_attribute.name

    def get_filter_name(self, obj):
        return obj.filter_attribute.filterr.name




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
        fields = ['id', 'name', 'filter_attributes']




class PostListSerializer(serializers.ModelSerializer):
    published_date = serializers.SerializerMethodField() 
    root = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()                                 #showing solo str datas like 'url' before dict/list type datas like image_icone, root, author  is more readable and clear.
    image_icon = Image_iconSerializer()
    root = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug',  'meta_title', 'meta_description', 'brief_description', 'published_date', 'url', 'image_icon', 'root', 'author']

    def get_image_icon(self, obj):
        request = self.context.get('request', None)
        try:
            url = request.build_absolute_uri(obj.image_icon.image.url)               
        except:
            url = ''                                                         
        return url

    def get_published_date(self, obj):
        d_t = obj.published_date
        shamsi_date = date_convertor.MiladiToShamsi(d_t.year, d_t.month, d_t.day).result(month_name=True)
        return f'{shamsi_date[2]} {shamsi_date[1]} {shamsi_date[0]}، ساعت {d_t.hour}:{d_t.minute}'
    
    def get_root(self, obj):                                        #we must create form like: <form method="get" action="/posts/?obj.root.slug"> .  note form must shown as link.
        pk, slug = obj.id, obj.slug
        name, url = (obj.root.name, f'/posts/{obj.root.slug}/') if obj.root else ('', '')       #post.root has null=True so this field can be blank like when you remove and root.
        return {'name': name, 'url': url}

    def get_author(self, obj):
        pk, slug = obj.id, obj.slug
        return {'name': user_name_shown(obj.author), 'url': 'profile/admin/{}/'.format(obj.author.id)}
    
    def get_url(self, obj):
        pk, slug = obj.id, obj.slug
        return f'/posts/detail/{pk}/{slug}/'




class ProductListSerializer(serializers.ModelSerializer):
    image_icon = Image_iconSerializer()
    rating = serializers.SerializerMethodField()                                        #RatingSerializer(read_only=True)
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'meta_title', 'meta_description', 'brief_description', 'price', 'available', 'image_icon', 'rating', 'url']       #visible, filter_attributes, root are filtered(removed) here.

    def get_rating(self, obj):
        rate = obj.rating.rate
        return rate
    
    def get_url(self, obj):
        pk, slug = obj.id, obj.slug
        return f'/products/detail/{pk}/{slug}/'




class PostDetailSerializer(serializers.ModelSerializer):
    published_date = serializers.SerializerMethodField() 
    author = UserNameSerializer()
    root = serializers.SerializerMethodField() 
    comment_set = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Post
        fields = '__all__'

    def get_published_date(self, obj):
        d_t = obj.published_date
        shamsi_date = date_convertor.MiladiToShamsi(d_t.year, d_t.month, d_t.day).result(month_name=True)
        return f'{shamsi_date[2]} {shamsi_date[1]} {shamsi_date[0]}، ساعت {d_t.hour}:{d_t.minute}'
    
    def get_root(self, obj):                                     #we must create form like: <form method="get" action="/posts/?obj.root.slug"> .  note form must shown as link. you can put that form in above of that post.
        pk, slug = obj.id, obj.slug
        name, url = (obj.root.name, f'/posts/{obj.root.slug}/') if obj.root else ('', '')       #post.root has null=True so this field can be blank like when you remove and root.
        return {'name': name, 'url': url}




class ProductDetailSerializer(serializers.ModelSerializer):       #comment_set will optained by front in other place so we deleted from here.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['smallimages'].context['request'] = request

    roots = serializers.SerializerMethodField()   
    rating = serializers.SerializerMethodField()
    smallimages = SmallImageSerializer(many=True)
    comment_count = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'meta_title', 'meta_description', 'brief_description', 'detailed_description', 'price', 'available', 'roots', 'rating', 'stock', 'brand', 'weight', 'smallimages', 'comment_count', 'related_products']

    def get_roots(self, obj):
        root_and_fathers = get_root_and_fathers(obj.root)
        root_and_fathers.reverse()                           #to fixing display order in front we reversed!!
        return RootChainedSerializer(root_and_fathers, many=True).data           
    
    def get_rating(self, obj):
        rate = obj.rating.rate
        return rate

    def get_comment_count(self, obj):
        rate = obj.comment_set.count()
        return rate

    def get_related_products(self, obj):
        request = self.context.get('request', None)
        related_products = Product.objects.filter(root=obj.root, visible=True).exclude(id=obj.id)[0:10] if obj.root else []
        if len(related_products) < 5 and obj.root and obj.root.father_root:                 #we must care obj.root had father_root 
            child_roots = obj.root.father_root.root_childs.values_list('id')      #child_roots is like [(6,) , (7,)]
            child_roots_ids = [root[0] for root in child_roots]
            related_products = Product.objects.filter(root_id__in=child_roots_ids, visible=True).exclude(id=obj.id)[0:10-len(related_products)]

        related_serialized = []
        for product in related_products:
            name, price, image_icon = product.name, str(product.price), product.image_icon              #rest_framework for default convert decimal fields to str, so we convert to str too.
            url = '/products/detail/{}/{}/'.format(product.id, product.slug)
            image_icon_url = request.build_absolute_uri(image_icon.image.url) if image_icon else ''
            alt = image_icon.alt
            related_serialized.append({'name': name, 'price': price, 'url': url, 'image_icon': {'image': image_icon_url, 'alt': alt}})
        return related_serialized




class ProductMongoSerializer(ProductDetailSerializer):
    filters = serializers.SerializerMethodField()  
    comment_set = CommentSerializer(read_only=True, many=True)

    def get_filters(self, obj):
        filter_filter_attribute = {}                                              # is like: {'rang': 'abi', 'rang': germez', 'size': 'large', ...}
        for filter_attribute in obj.filter_attributes.all():
            if filter_filter_attribute.get(filter_attribute.filterr.name):        # this line make prevent overiding filter_attribute of a product that have same filter for example if product1.filter_attributes = ['abi', 'narenji', ..],  abi narenji ave same filter 'color'    if we dont want saving filter_attributes of same filter in a product we should prevent it in saving product but now i don't feel any needs to that.
                filter_filter_attribute[filter_attribute.filterr.name] += [filter_attribute.name]
            else:
                filter_filter_attribute[filter_attribute.filterr.name] = [filter_attribute.name]
        return filter_filter_attribute

    class Meta:
        model = Product
        fields = ProductDetailSerializer.Meta.fields + ['filters', 'comment_set']


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['key', 'name']                            #we use key instead id for saving of states and towns. (id can be change in next db but key is more stable)


class TownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Town
        fields = ['key', 'name']                            #key is unique so dont need to state or other fields for saving ProfileOrder or ...
