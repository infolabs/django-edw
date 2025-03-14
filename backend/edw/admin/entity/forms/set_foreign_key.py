from django import forms
from django.db.models.fields.related import ForeignKey

from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

from edw.admin.base_actions import BaseActionAdminForm
from edw.admin.entity.widgets.dynamic_raw_id import ModelIdWidget, ModelRel

from edw.admin.customer import CustomerProxy
from edw.models.customer import BaseCustomer



class SetForeignKeyInEntitiesActionAdminForm(BaseActionAdminForm):

    def __init__(self, *args, **kwargs):
        """
        Конструктор для корректного отображения объектов
        """
        super(SetForeignKeyInEntitiesActionAdminForm, self).__init__(*args, **kwargs)

        for field in [x for x in self.opts.fields if (isinstance(x, ForeignKey) and x.editable and
                                                      x.get_internal_type() == 'ForeignKey')]:
            model_rel = ModelRel(CustomerProxy, 'customer') if issubclass(field.related_model, BaseCustomer) else (
                ModelRel(field.related_model, field.related_model._meta.pk.name))
            self.fields[field.name] = forms.ModelChoiceField(
                queryset=field.related_model.objects.all(), required=False, to_field_name=field.related_model._meta.pk.name,
                widget=ModelIdWidget(admin.site, model_rel),
                label=_(field.verbose_name))
