from rest_framework import serializers

from main.myserializers import Image_iconSerializer
from main.models import Product




class CartProductSerializer(serializers.ModelSerializer):
    image_icon = Image_iconSerializer()
    rating = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'meta_title', 'price', 'available', 'created', 'updated', 'image_icon', 'rating', 'brand', 'weight', 'url']

    def get_rating(self, obj):
        rate = obj.rating.rate
        return rate

    def get_url(self, obj):
        pk, slug = obj.id, obj.slug
        return f'/products/detail/{pk}/{slug}/'
