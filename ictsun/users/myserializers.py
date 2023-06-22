from django.db import models
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError, ErrorDetail

import jdatetime

from customed_files import date_convertor
from orders.models import ProfileOrder
from .models import User
from .mymethods import user_name_shown



        
class UserSerializer(serializers.ModelSerializer):    
    class Meta:
        model = User
        fields = '__all__'
    
    def to_representation(self, obj):
        self.fields['phone'] = serializers.SerializerMethodField()
        self.fields['date_joined'] = serializers.SerializerMethodField()  
        self.fields['last_login'] = serializers.SerializerMethodField()
        self.fields['postal_code'] = serializers.SerializerMethodField()
        fields = super().to_representation(obj)
        [fields.pop(key, None) for key in ['groups', 'password', 'user_permissions', 'visible']]        #fields.pop(key, None)  this None means if dont find key for removing dont raise error return None instead.
        return fields

    def is_valid(self, raise_exception=False):
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )

        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail


                errors_dic = exc.detail.copy()
                for field_name in exc.detail:
                    for i in range(len(exc.detail[field_name])):
                        details_list = exc.detail[field_name].copy()          #exc.detail[field_name] is list and mutable with details, su we use .copy to stop changing exc.detail
                        details_list[i] = {exc.detail[field_name][i].code: exc.detail[field_name][i]}   #exc.detail[field_name][i] is object of ErrorDetail class
                    errors_dic[field_name] = details_list
                self._errors = {'error': exc.detail}


            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise ValidationError(errors_dic)

        return not bool(self._errors)
    
    def get_phone(self, obj):
        return str(obj.phone.national_number)

    def get_date_joined(self, obj):
        return str(jdatetime.datetime.fromgregorian(datetime=obj.date_joined))

    def get_last_login(self, obj):
        if obj.last_login:                              # in first of user creation is None
            return str(jdatetime.datetime.fromgregorian(datetime=obj.last_login))

    def get_postal_code(self, obj):
        request = self.context.get('request', None)
        profile_order = ProfileOrder.objects.filter(user=request.user, main=True).values_list('postal_code', flat=True) if request else None 
        postal_code = profile_order[0] if profile_order else ''
        return postal_code
#UserSerializer.serializer_field_mapping[models.EmailField] = serializerfields.EmailFieldCustom

 


    
class UserChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']
        



class UserNameSerializer(serializers.ModelSerializer):         #UserName = NAme of User for shown in site.
    user_name = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'user_name']
        
    def get_user_name(self, obj):
        return user_name_shown(obj, _('admin'))
