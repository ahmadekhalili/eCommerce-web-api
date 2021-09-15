from django.forms import boundfield

class CustomBoundField(boundfield.BoundField):
    def value(self, return_instance=False):
        return self.form.instance
