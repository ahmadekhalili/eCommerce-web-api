from rest_framework import serializers

from main.methods import ImageCreationSizes


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
