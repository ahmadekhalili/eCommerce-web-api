from django.db import models
from django.db.models.fields.json import KeyTransform
from django.core.exceptions import ValidationError

import json
import ast


class TextFieldListed(models.TextField):                      # this field in save phase give list but save that as str in db and in display phase give str from db and convert to list again again for display. like: str: "[('39761', 'آبسرد'), ('39741', 'آبعلي')]"    list: [('39761', 'آبسرد'), ('39741', 'آبعلي')]  complete refrence: https://docs.djangoproject.com/en/3.2/howto/custom-model-fields/   one example: https://stackoverflow.com/questions/1110153/what-is-the-most-efficient-way-to-store-a-list-in-the-django-models
    def from_db_value(self, value, expression, connection):   # from_db_value obtain data from db to display
        if isinstance(value, list) or value is None:
            return value
        if value == '' or value == json.dumps(''):
            return []
        if isinstance(expression, KeyTransform) and not isinstance(value, str):
            return value
        try:
            return ast.literal_eval(value)                       # value is str. value between '[1,2, "a",3]' or '[1, 2, "a", 3]' has not difference.
        except json.JSONDecodeError:
            return value                                   # method from_db_value should return value in eny way, so client can fix inputed wrong value.

    def to_python(self, value):                               # to_python called in two phase 1- deserializing (from db to display)  2- clean data(saving, like from form to db)  so this method should work with three datatype of our field value:   one when displaying(here list)   two in saving to database(here str)    three  None
        if isinstance(value, list) or value is None:
            return value
        if value == '' or value == json.dumps(''):
            return []
        if not isinstance(value, str):
            return value
        try:
            L = ast.literal_eval(value)                       # value is str. value between '[1,2, "a",3]' or '[1, 2, "a", 3]' has not difference.
            if isinstance(L, list):
                return L
            else:
                raise ValidationError(f'add list, value type: {type(value)}')
        except json.JSONDecodeError:
            raise ValidationError(f'cant run json.loads value type: {type(value)}')

    def get_prep_value(self, value):                          # this method save value to db.
        if value and isinstance(value, str):
            return value
        return json.dumps(value)                              # json.dumps == str  but more safer.

    def value_to_string(self, obj):                           # this is used by rest_ramework (in task is like get_prep_value)
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
