from django.utils.translation import gettext_lazy as _

from modeltranslation.admin import TranslationAdmin


class ModelAdminCust(TranslationAdmin):
    def _delete_view(self, request, object_id, extra_context):                      #we want change delete page title (in deleting an object delete page shown)
        template_response = super()._delete_view(request, object_id, extra_context)
        opts = self.model._meta
        object_name = str(opts.verbose_name)
        template_response.context_data['title'] = _('delete') + ' ' + object_name + ' ' + str(object_id)
        return template_response
