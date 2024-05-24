from rest_framework.response import Response

import json
from bson.objectid import ObjectId


class ObjectIdJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


class ResponseMongo(Response):    # ResponseMongo(data), convert all nested ObjectId('...') of 'data' to serialized str
    def __init__(self, data=None, status=None, template_name=None, headers=None, content_type=None):
        if data is not None:
            # Convert the data to JSON using the custom encoder
            data = json.loads(json.dumps(data, cls=ObjectIdJSONEncoder))
        super().__init__(data=data, status=status, template_name=template_name, headers=headers, content_type=content_type)