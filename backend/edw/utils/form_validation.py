# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_russian_name(name):
    if not re.match(r'^[а-яёА-ЯЁ\.\ ]+$', name):
        msg = _("Name should not contain characters other than"
                " characters from Russian alphabet, dots and spaces")
        raise ValidationError(msg)

    if name.isspace():
        msg = _("Name should not be empty")
        raise ValidationError(msg)

    if not re.sub(r'[\.\ ]', '', name):
        # '.... .... ...абв' => ok
        # '.... .... ...' => Error
        msg = _('Name should not contain only spaces or dots')
        raise ValidationError(msg)

    return name
