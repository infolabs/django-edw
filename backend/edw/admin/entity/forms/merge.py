from django import forms
from django.db.models import fields

from django.utils.translation import ugettext_lazy as _

from edw.admin.base_actions import BaseActionAdminForm


ORDER = (
    ("", _("-"*9)),
    ('ASC', _("Ascending")),
    ('DESC', _("Descending"))
)

class MergeEntitiesActionAdminForm(BaseActionAdminForm):

    order = forms.TypedChoiceField(label=_("Join order by `ID`"), choices=ORDER, initial="",
                                           coerce=lambda x: x == 'ASC',
                                           widget=forms.Select())

    terms = forms.BooleanField(label=f'{_("Do merge")} {_("Terms")}', initial=True, required=False)
    characteristics_or_marks = forms.BooleanField(label=f'{_("Do merge")} {_("Characteristics or Marks")}',
                                                  initial=True, required=False)

    related_datamarts = forms.BooleanField(label=f'{_("Do merge")} {_("Related Datamarts")}',
                                                  initial=True, required=False)

    joiner = forms.CharField(label=_("Strings joiner"), initial=';', max_length=5)

    def __init__(self, *args, **kwargs):
        """
        Конструктор для корректного отображения объектов
        """
        super(MergeEntitiesActionAdminForm, self).__init__(*args, **kwargs)

        # get char fields list
        char_fields = [field for field in self.opts.fields if isinstance(field, fields.CharField) and not getattr(
            field, 'protected', False)]
        for field in char_fields:
            self.fields[field.name] = forms.BooleanField(label=f'{_("Do merge")} {field.verbose_name}',
                                                         initial="", required=False)

        # get related objects list
        for related_object in self.opts.related_objects:
            if not related_object.remote_field.name.startswith('_'):
                field_name = f"{related_object.related_model._meta.model_name}__{related_object.remote_field.name}"

                self.fields[field_name] = forms.BooleanField(
                    label=f"""{_("Update related objects")} """
                          f"""{related_object.related_model._meta.verbose_name} <{related_object.related_model.__name__}>: """
                          f"""{related_object.field.verbose_name} → {related_object.model._meta.verbose_name} <{related_object.model.__name__}>""",
                    initial=True, required=False)
