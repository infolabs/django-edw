from django import forms
from django.db.models.fields.related import ForeignKey

from django.contrib.admin.views.main import TO_FIELD_VAR
try:
    from salmonella.widgets import SalmonellaIdWidget
except ImportError:
    from dynamic_raw_id.widgets import DynamicRawIDWidget as SalmonellaIdWidget

from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

from edw.admin.base_actions import BaseActionAdminForm


#==============================================================================
# ModelRel
#==============================================================================
class Field(object):
    def __init__(self, name):
        self.name =  name


class ModelRel(object):
    def __init__(self, model):
        self.to = model
        self.limit_choices_to = {}
        self.model = model

    def get_related_field(self):
        return Field('customer')


#==============================================================================
# CustomerIdWidget
#==============================================================================
class ModelIdWidget(SalmonellaIdWidget):
    def __init__(self, admin_site, rel, to_field, attrs=None, using=None):
        self.to_field = to_field
        super(ModelIdWidget, self).__init__(rel, admin_site, attrs, using)

    def url_parameters(self):
        params = self.base_url_parameters()
        params.update({TO_FIELD_VAR: self.to_field})
        return params


class SetForeignKeyInEntitiesActionAdminForm(BaseActionAdminForm):

    def __init__(self, *args, **kwargs):
        """
        Конструктор для корректного отображения объектов
        """
        super(SetForeignKeyInEntitiesActionAdminForm, self).__init__(*args, **kwargs)

        for field in [x for x in self.opts.fields if (isinstance(x, ForeignKey) and x.editable and
                                                      x.get_internal_type() == 'ForeignKey')]:

            self.fields[field.name] = forms.ModelChoiceField(
                queryset=field.related_model.objects.all(), required=False, to_field_name=field.related_model._meta.pk.name,
                widget=ModelIdWidget(admin.site, ModelRel(field.related_model), field.related_model._meta.pk.name),
                label=_(field.verbose_name))
