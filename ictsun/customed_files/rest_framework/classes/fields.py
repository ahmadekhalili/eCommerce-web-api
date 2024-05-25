from rest_framework import serializers

import jdatetime, datetime
from bson.objectid import ObjectId

from main.methods import ImageCreationSizes
from main.models import Image_icon
from main.methods import ImageCreationSizes


class TimestampField(serializers.Field):
    # 'jalali' means Solar date instead of Gregorian
    def __init__(self, jalali=False, auto_now=False, auto_now_add=False, *args, **kwargs):
        self.jalali = jalali
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        # when take value from like instance.updated or validated_data
        if isinstance(value, (datetime.datetime, jdatetime.datetime)):
            return int(value.timestamp())      # value.timestamp() returns float
        else:                 # when take value from mongo db
            return value

    def get_value(self, dictionary):
        update_phase = getattr(self.parent, 'pk', False) or getattr(self.parent, 'instance', False)
        if self.auto_now_add and not update_phase:
            return True
        elif self.auto_now and update_phase:
            return True
        else:
            return super().get_value(dictionary)

    def to_internal_value(self, data):
        if self.auto_now_add or self.auto_now:
            if self.jalali:
                return jdatetime.datetime.now()
            return datetime.datetime.now()
        else:
            try:
                if self.jalali:
                    return jdatetime.datetime.fromtimestamp(int(data))
                return datetime.datetime.fromtimestamp(int(data))
            except ValueError:
                raise ValueError("you have to input in timestamp format, but provided: {{ data }}")


class DateTimeFieldMongo(serializers.DateTimeField):
    def __init__(self, auto_now=False, auto_now_add=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

    def to_internal_value(self, data):
        def get_datetime():
            if self.jalali:
                jdatetime.datetime.now()
            else:
                datetime.datetime.now()

        update_phase = getattr(self.parent, 'pk', False) or getattr(self.parent, 'instance', False)
        if self.auto_now_add and not update_phase:
            return get_datetime()
        elif self.auto_now and update_phase:
            return get_datetime()
        else:
            return super().to_internal_value(data)


class IdMongoField(serializers.Field):
    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        if type(data) == str:
            return ObjectId(data)


class OneToMultipleImage(serializers.Serializer):
    def __init__(self, sizes=None, upload_to=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance:      # in writing, sizes and upload_to required
            if not sizes and not upload_to:
                raise ValueError("both of 'sizes' and 'upload_to' arguments must be provided")
            self.sizes = sizes
            self.upload_to = upload_to

    def to_representation(self, value):
        result = {}
        for image_icon in value:
            size = image_icon.size
            result[size] = {'image': image_icon.url, 'alt': getattr(image_icon, 'alt', '')}
        return result

    def to_internal_value(self, data):
        obj = ImageCreationSizes(data=data, sizes=self.sizes)
        instances = obj.upload(upload_to=self.upload_to)
        return instances
