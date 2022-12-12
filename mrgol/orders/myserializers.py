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
        self.fields['state'] = StateSerializer(read_only=True)
        self.fields['town'] = TownSerializer(read_only=True)
        self.fields['user'] = UserNameSerializer(read_only=True)
        fields =  super().to_representation(obj)
        return fields

    def get_phone(self, obj):
        return f'{obj.phone.national_number}'




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
        d_t = obj.delivery_date
        shamsi_date = jdatetime.datetime.fromgregorian(datetime=d_t).strftime('%Y %B %-d').split() if d_t else None
        return f'{shamsi_date[2]} {shamsi_date[1]} {shamsi_date[0]}، ساعت {d_t.hour}:{d_t.minute}' if d_t else None

    def get_created(self, obj):
        d_t = obj.created
        shamsi_date = jdatetime.datetime.fromgregorian(datetime=d_t).strftime('%Y %B %-d').split()
        return f'{shamsi_date[2]} {shamsi_date[1]} {shamsi_date[0]}، ساعت {d_t.hour}:{d_t.minute}'




class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        exclude = ['visible']

    def to_representation(self, obj):
        self.fields['product'] = CartProductSerializer(read_only=True)
        fields =  super().to_representation(obj)
        fields.pop('order')
        return fields
