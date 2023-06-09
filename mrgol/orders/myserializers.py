from rest_framework import serializers

import jdatetime

from main.myserializers import StateSerializer, TownSerializer
from cart.myserializers import CartProductSerializer
from users.myserializers import UserNameSerializer
from .models import ProfileOrder, Order, OrderItem




class ProfileOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileOrder
        exclude = ['visible']

    def to_representation(self, obj):
        self.fields['phone'] = serializers.SerializerMethodField()
        self.fields['state'] = serializers.SerializerMethodField()
        self.fields['town'] = TownSerializer(read_only=True)
        self.fields['user'] = UserNameSerializer(read_only=True)
        fields =  super().to_representation(obj)
        return fields

    def get_phone(self, obj):
        return f'{obj.phone.national_number}'

    def get_state(self, obj):
        return StateSerializer(obj.town.state, read_only=True).data



class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ['visible']

    def to_representation(self, obj):
        self.fields['order_status'] = serializers.SerializerMethodField()
        self.fields['delivery_date'] = serializers.SerializerMethodField()
        self.fields['created'] = serializers.SerializerMethodField()
        self.fields['profile_order'] = ProfileOrderSerializer(read_only=True)
        self.fields['items'] = OrderItemSerializer(many=True, read_only=True)
        return super().to_representation(obj)

    def get_order_status(self, obj):
        return obj.get_order_status_display()

    def get_delivery_date(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.delivery_date).timestamp())

    def get_created(self, obj):
        return round(jdatetime.datetime.fromgregorian(datetime=obj.created).timestamp())




class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        exclude = ['visible']

    def to_representation(self, obj):
        self.fields['product'] = CartProductSerializer(read_only=True)
        fields =  super().to_representation(obj)
        fields.pop('order')
        return fields
