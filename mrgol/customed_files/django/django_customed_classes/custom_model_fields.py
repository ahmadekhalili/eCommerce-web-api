from django.db import models
from django.db.models.fields.related import lazy_related_operation
from datetime import datetime

from functools import partial

from customed_files import date_convertor



class ShamsiDateTimeField(models.DateTimeField):
    pass
    '''
    def from_db_value(self, value, expression, connection):             #this method only show field value,  refrence: https://docs.djangoproject.com/en/3.1/howto/custom-model-fields/#converting-values-to-python-objects   
        shamsi_date = date_convertor.MiladiToShamsi(value.year, value.month, value.day).result()
        shamsi_datetime = datetime(shamsi_date[0], shamsi_date[1], shamsi_date[2], value.hour, value.minute, value.second)
        return shamsi_datetime
    '''

