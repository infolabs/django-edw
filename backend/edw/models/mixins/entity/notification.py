# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from jsonfield.fields import JSONField

from edw.models.mixins import ModelMixin


class NotificationMixin(ModelMixin):
    """
    RUS: Для хранения данных в кодировке JSON.
    """
    stored_request = JSONField(verbose_name=_("stored_request"), default={},
        help_text=_("Parts of the Request objects on the moment of submit."))

    @property
    def customer(self):
        """
        RUS: Возбуждает исключение,
        когда абстрактные методы класса Customer требуют переопределения в дочерних классах.
        """
        raise NotImplementedError(
            '{cls}.customer must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )