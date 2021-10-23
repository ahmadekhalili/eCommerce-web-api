from rest_framework import serializers

from customed_files.date_convertor import MiladiToShamsi
from cart.myserializers import CartProductSerializer
from users.myserializers import UserNameSerializer
from .models import ProfileOrder, Order, OrderItem





class ProfileOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileOrder
        exclude = ['visible']
        
    def to_representation(self, obj):
        self.fields['name'] = serializers.SerializerMethodField()
        self.fields['user'] = UserNameSerializer()
        fields =  super().to_representation(obj)
        fields.pop('first_name'), fields.pop('last_name')
        return fields
    
    def get_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

     




class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ['visible']

    def to_representation(self, obj):
        self.fields['order_status'] = serializers.SerializerMethodField() 
        self.fields['created'] = serializers.SerializerMethodField()
        self.fields['profile_order'] = ProfileOrderSerializer()
        self.fields['items'] = OrderItemSerializer(many=True)
        return super().to_representation(obj)

    def get_order_status(self, obj):
        return obj.get_order_status_display()
    
    def get_created(self, obj):
        created = obj.created
        y, m, d= created.year, created.month, created.day
        y, m, d = MiladiToShamsi(y, m, d).result()
        return f'{y}/{m}/{d}'



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        exclude = ['visible']

    def to_representation(self, obj):
        self.fields['product'] = CartProductSerializer()
        fields =  super().to_representation(obj)
        fields.pop('order')
        return fields
