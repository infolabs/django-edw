# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from django_filters.fields import BaseCSVField
from django_filters.widgets import CSVWidget


class BaseListField(BaseCSVField):
    # Force use of text input, а Field that aggregates the logic of multiple Fields.

    widget = CSVWidget

    default_error_messages = {
        'invalid_values': _('List query expects minimum {} and maximum {} values.'),
        'incomplete': _('Enter a complete value.'),
    }

    def __init__(self, fields=(), min_len=0, *args, **kwargs):
        # fields -- list of Field's
        # min_len -- minimal length of input
        self.min_len, self.max_len = min_len, len(fields)
        self.require_all_fields = kwargs.pop('require_all_fields', self.min_len == self.max_len)
        super(BaseListField, self).__init__(*args, **kwargs)
        for f in fields:
            f.error_messages.setdefault('incomplete',
                                        self.error_messages['incomplete'])
            if self.require_all_fields:
                # Set 'required' to False on the individual fields, because the
                # required validation will be handled by BaseListField, not
                # by those individual fields.
                f.required = False
        self.fields = fields

    def __deepcopy__(self, memo):
        result = super(BaseListField, self).__deepcopy__(memo)
        result.fields = tuple(x.__deepcopy__(memo) for x in self.fields)
        return result

    def validate(self, value):
        pass

    def clean(self, value):
        """
        Validates every value in the given list. A value is validated against
        the corresponding Field in self.fields.

        For example, if this BaseListField was instantiated with
        fields=(DateField(), TimeField()), clean() would call
        DateField.clean(value[0]) and TimeField.clean(value[1]).
        """
        clean_data = []
        errors = []

        if not value or not [v for v in value if v not in self.empty_values]:
            if self.required:
                raise ValidationError(self.error_messages['required'], code='required')
            else:
                return self.compress([])

        if value is not None and not self.min_len <= len(value) <= self.max_len:
            raise forms.ValidationError(
                self.error_messages['invalid_values'].format(self.min_len, self.max_len),
                code='invalid_values')

        for i, field in enumerate(self.fields):
            try:
                field_value = value[i]
            except IndexError:
                field_value = None
            if field_value in self.empty_values:
                if self.require_all_fields:
                    # Raise a 'required' error if the MultiValueField is
                    # required and any field is empty.
                    if self.required:
                        raise ValidationError(self.error_messages['required'], code='required')
                elif field.required:
                    # Otherwise, add an 'incomplete' error to the list of
                    # collected errors and skip field cleaning, if a required
                    # field is empty.
                    if field.error_messages['incomplete'] not in errors:
                        errors.append(field.error_messages['incomplete'])
                    continue
            try:
                clean_data.append(field.clean(field_value))
            except ValidationError as e:
                # Collect all validation errors in a single list, which we'll
                # raise at the end of clean(), rather than raising a single
                # exception for the first error we encounter. Skip duplicates.
                errors.extend(m for m in e.error_list if m not in errors)
        if errors:
            raise ValidationError(errors)

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out

    def compress(self, data_list):
        """
        Returns a value for the given list of values. The values can be
        assumed to be valid.

        For example, if this BaseListField was instantiated with
        fields=(DateField(), TimeField()), this might return a datetime
        object created by combining the date and time in data_list.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def has_changed(self, initial, data):
        if self.disabled:
            return False
        if initial is None:
            initial = ['' for x in range(0, len(data))]
        else:
            if not isinstance(initial, list):
                initial = self.widget.decompress(initial)
        for field, initial, data in zip(self.fields, initial, data):
            try:
                initial = field.to_python(initial)
            except ValidationError:
                return True
            if field.has_changed(initial, data):
                return True
        return False
