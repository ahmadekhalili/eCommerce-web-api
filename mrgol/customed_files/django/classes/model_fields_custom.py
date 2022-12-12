from django.db import models
from django.conf import settings
from django.db.models.fields.related import lazy_related_operation

import ast
import json
from datetime import datetime
from functools import partial

from customed_files import date_convertor



class TextFieldListed(models.TextField):                      #this field in save phase give list but save that as str in db and in display phase give str from db and convert to list again again for display. like: str: "[('39761', 'آبسرد'), ('39741', 'آبعلي')]"    list: [('39761', 'آبسرد'), ('39741', 'آبعلي')]  complete refrence: https://docs.djangoproject.com/en/3.2/howto/custom-model-fields/   one example: https://stackoverflow.com/questions/1110153/what-is-the-most-efficient-way-to-store-a-list-in-the-django-models
    def from_db_value(self, value, expression, connection):   #from_db_value optain data from db to display(jahate namaiesh)
        if isinstance(value, list) or value is None:
            return value
        return ast.literal_eval(value)                        #value is str
    
    def to_python(self, value):                               #to_python called in two pase 1- deserializing (from db to display)  2- clean data(saving, like from form to db)  so this method should word with three datatype of our field value:   one when displaying(here list)   two in saving to database(here str)    three  None
        if isinstance(value, list) or value is None:
            return value
        return ast.literal_eval(value)
    
    def get_prep_value(self, value):                          #this method save value to db.
        value = super().get_prep_value(value)
        return json.dumps(value)                              #json.dumps == str  but more safer.
    
    def value_to_string(self, obj):                           #this is used by rest_ramework (in task is like get_prep_value)
        value = self.value_from_object(obj)
        return self.get_prep_value(value)



'''
class DateTimeFieldShamsi(models.DateTimeField):
    def from_db_value(self, value, expression, connection):             #this method only show field value,  refrence: https://docs.djangoproject.com/en/3.1/howto/custom-model-fields/#converting-values-to-python-objects   
        if settings.LANGUAGE_CODE == 'fa' or settings.LANGUAGE_CODE == 'fa-ir':
            if value:
                shamsi_date = date_convertor.MiladiToShamsi(value.year, value.month, value.day).result()
                return datetime(shamsi_date[0], shamsi_date[1], shamsi_date[2], value.hour, value.minute, value.second)
            return value                                                 #from_db_value is not in django fields so super().from_db_value is error, this method should handdle by your value
'''
