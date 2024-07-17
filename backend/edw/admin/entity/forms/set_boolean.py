from django import forms
from django.db.models import fields

from django.utils.translation import ugettext_lazy as _

from edw.admin.base_actions import BaseActionAdminForm


SET_MODE = (
    ("", _("-"*9)),
    ('False', _("False")),
    ('True', _("True")),
    ('Toggle', _("Toggle")),
)

class SetBooleanInEntitiesActionAdminForm(BaseActionAdminForm):


    def __init__(self, *args, **kwargs):
        """
        Конструктор для корректного отображения объектов
        """
        super(SetBooleanInEntitiesActionAdminForm, self).__init__(*args, **kwargs)

        # get boolean fields list
        bool_fields = [field for field in self.opts.fields if isinstance(field, fields.BooleanField) and not getattr(
            field, 'protected', False)]
        for field in bool_fields:
            self.fields[field.name] = forms.TypedChoiceField(label=f"""{field.verbose_name} - {_("Set field value to")}""",
                                    choices=SET_MODE, initial="",
                                    coerce=str, required=False,
                                    widget=forms.Select())
