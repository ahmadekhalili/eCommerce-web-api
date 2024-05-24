from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from bson import ObjectId


class MongoUniqueValidator(UniqueValidator):
    def __init__(self, collection, field, message=None):
        self.queryset = None      # provide value None for default attribute
        self.collection = collection
        self.field = field
        self.message = message or f'The {field} must be unique.'

    def __call__(self, value, serializer_field):
        self.pk = getattr(serializer_field.parent, 'pk', None)
        query = {self.field: value}
        if self.pk:
            # in updating, search all collections (for validating unique) except current collection
            query['_id'] = {'$ne': ObjectId(self.pk)}
        if self.collection.find_one(query):
            raise serializers.ValidationError(self.message)
