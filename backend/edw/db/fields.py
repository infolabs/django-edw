# -*- coding: utf-8 -*-
import sys

from django import VERSION

from django.db import models
from django.utils.text import capfirst
from django.core import exceptions

from edw.forms.notification import MultiSelectFormField


if sys.version_info < (3,):
    string_type = unicode
else:
    string_type = str

BLANK_CHOICE_DASH = [("", "---------")]
from django.core import validators

class MSFList(list):

    def __init__(self, choices, *args, **kwargs):
        self.choices = choices
        super(MSFList, self).__init__(*args, **kwargs)

    def __str__(msgl):
        msg_list = [msgl.choices.get(int(i)) if i.isdigit() else msgl.choices.get(i) for i in msgl]
        return u', '.join([string_type(s) for s in msg_list])

    if sys.version_info < (3,):
        def __unicode__(self, msgl):
            return self.__str__(msgl)


class MaxValueMultiFieldValidator(validators.MaxLengthValidator):
    code = 'max_multifield_value'

    def clean(self, x):
        return len(','.join(x))


class MultiSelectField(models.CharField):
    """
    RUS: MultiSelect поле с динамическим choices
    dinamic_choices_model_attr = строка с наименованием функции модели возвращающей choices
    """

    def __init__(self, *args, **kwargs):
        self.dinamic_choices_model_attr = kwargs.pop('dinamic_choices_model_attr', None)

        super(MultiSelectField, self).__init__(*args, **kwargs)
        self.validators[0] = MaxValueMultiFieldValidator(self.max_length)

    def _get_flatchoices(self):
        flat_choices = super(MultiSelectField, self)._get_flatchoices()

        class MSFFlatchoices(list):
            # Used to trick django.contrib.admin.utils.display_for_field into
            # not treating the list of values as a dictionary key (which errors
            # out)
            def __bool__(self):
                return False
            __nonzero__ = __bool__
        return MSFFlatchoices(flat_choices)
    flatchoices = property(_get_flatchoices)

    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH, limit_choices_to=None):
        """Returns choices with a default blank choices included, for use
        as SelectField choices for this field."""

        if self.dinamic_choices_model_attr and hasattr(self, 'model'):
            dinamic_choices = getattr(self.model, self.dinamic_choices_model_attr)
            self.choices = dinamic_choices()

        return self.choices

    def get_choices_default(self):
        return self.get_choices(include_blank=False)

    def get_choices_selected(self, arr_choices):

        named_groups = arr_choices and isinstance(arr_choices[0][1], (list, tuple))
        choices_selected = []
        if named_groups:
            for choice_group_selected in arr_choices:
                for choice_selected in choice_group_selected[1]:
                    choices_selected.append(string_type(choice_selected[0]))
        else:
            for choice_selected in arr_choices:
                choices_selected.append(string_type(choice_selected[0]))
        return choices_selected

    def value_to_string(self, obj):
        try:
            value = self._get_val_from_obj(obj)
        except AttributeError:
            value = super(MultiSelectField, self).value_from_object(obj)
        return self.get_prep_value(value)

    def validate(self, value, model_instance):
        arr_choices = self.get_choices_selected(self.get_choices_default())
        for opt_select in value:
            if (opt_select not in arr_choices):
                if VERSION >= (1, 6):
                    raise exceptions.ValidationError(self.error_messages['invalid_choice'] % {"value": value})
                else:
                    raise exceptions.ValidationError(self.error_messages['invalid_choice'] % value)

    def get_default(self):
        default = super(MultiSelectField, self).get_default()
        if isinstance(default, int):
            default = string_type(default)
        return default

    def formfield(self, **kwargs):

        defaults = {'required': not self.blank,
                    'label': capfirst(self.verbose_name),
                    'help_text': self.help_text,
                    'choices': self.choices}

        if self.has_default():
            defaults['initial'] = self.get_default()
        defaults.update(kwargs)

        return MultiSelectFormField(**defaults)

    def get_prep_value(self, value):
        return '' if value is None else ",".join(map(str, value))

    def get_db_prep_value(self, value, connection, prepared=False):
        if not prepared and not isinstance(value, string_type):
            value = self.get_prep_value(value)
        return value

    def to_python(self, value):
        choices = dict(self.flatchoices)

        if value:
            if isinstance(value, list):
                return value
            elif isinstance(value, string_type):
                value_list = map(lambda x: x.strip(), value.replace(u"，", ",").split(","))
                return MSFList(choices, value_list)
            elif isinstance(value, (set, dict)):
                return MSFList(choices, list(value))
        return MSFList(choices, [])

    if VERSION < (2, ):
        def from_db_value(self, value, expression, connection, context):
            if value is None:
                return value
            return self.to_python(value)
    else:
        def from_db_value(self, value, expression, connection):
            if value is None:
                return value
            return self.to_python(value)

    def contribute_to_class(self, cls, name):

        super(MultiSelectField, self).contribute_to_class(cls, name)

        if self.choices:
            def get_list(obj):
                fieldname = name
                choicedict = dict(self.choices)
                display = []
                if getattr(obj, fieldname):
                    for value in getattr(obj, fieldname):
                        item_display = choicedict.get(value, None)
                        if item_display is None:
                            try:
                                item_display = choicedict.get(int(value), value)
                            except (ValueError, TypeError):
                                item_display = value
                        display.append(string_type(item_display))
                return display

            def get_display(obj):
                return ", ".join(get_list(obj))
            get_display.short_description = self.verbose_name

            setattr(cls, 'get_%s_list' % self.name, get_list)
            setattr(cls, 'get_%s_display' % self.name, get_display)
