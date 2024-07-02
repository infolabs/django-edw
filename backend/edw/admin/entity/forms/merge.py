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

    joiner = forms.CharField(label=_("Joiner"), initial=';', max_length=5)

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
