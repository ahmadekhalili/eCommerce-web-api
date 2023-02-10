from rest_framework import serializers

from main.myserializers import Image_iconSerializer
from main.models import Product

from collections.abc import Mapping




class BaseCartProductSerializer(serializers.ModelSerializer):          # suppose 'item' in: for item in Cart(request),  BaseCartProductSerializer serialize item['product']
    image_icon = Image_iconSerializer()
    rating = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'meta_title', 'price', 'available', 'created', 'updated', 'image_icon', 'rating', 'stock', 'brand', 'weight', 'url']

    def get_rating(self, obj):
        rate = obj['rating'] if isinstance(obj, Mapping) else obj.rating.rate        # Mapping==dict, why not obj['rating'].rate? in CartProductSerializer.to_represantation(), BaseCartProductSerializer called two time, in first optained rating by get_rating() method as Decimal, so in second (second run because CartProductSerializer inherited from BaseCartProductSerializer) rating is decimal like: Decimal('10.00')
        return rate

    def get_url(self, obj):
        pk, slug = (obj['id'], obj['slug']) if isinstance(obj, Mapping) else (obj.id, obj.slug)
        return f'/products/detail/{pk}/{slug}/'

    def get_brand(self, obj):
        return obj['brand'] if isinstance(obj, Mapping) else obj.brand.id


class CartProductSerializer(BaseCartProductSerializer):             # suppose 'item' in: for item in Cart(request),  CartProductSerializer serialize most attributes of 'item' like item['product'] (helped by BaseCartProductSerializer), item['price'], item['total_price']
    #price = serializers.SerializerMethodField()                     # impotant: price here is difference from product.price. price here can be shopfilteritem.price
    quantity = serializers.IntegerField()
    total_price = serializers.CharField()                           # total_price shoud be str, this field convert decimal inputed total_price to str total_price.

    class Meta:
        model = Product
        fields = BaseCartProductSerializer.Meta.fields + ['quantity', 'total_price']

    def to_representation(self, obj):            # obj == cart item
        item = {**BaseCartProductSerializer(obj['product']).data, 'price': obj['price'], 'quantity': obj['quantity'], 'total_price': obj['total_price']}
        return super().to_representation(item)

    def get_price(self, obj):
        return 'hhhhhhh'
