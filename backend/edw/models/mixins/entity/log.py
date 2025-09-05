# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


class CommonLoggingMixin(object):
    """
    RUS: Добавляет логгирование
    """
    def make_log(self, user_id, message, type=CHANGE):
        """
        Логирует изменения, используя встроенный механизм логирования Джанго
        """

        try:

            LogEntry.objects.log_action(
                user_id=user_id,
                content_type_id=ContentType.objects.get_for_model(self).pk,
                object_id=self.pk,
                object_repr=force_text(self),
                change_message=message,
                action_flag=type,
            )

        except:
            pass

    def change_log(self, user_id, attribute, old_state, new_state, additional_message=""):
        message = _('Change "{attribute}" -> "{old_state}" -> "{new_state}"').format(
            **{'attribute': attribute,
             'old_state': old_state,
             'new_state': new_state,
             }
        )
        if additional_message:
            message += " ({})".format(additional_message)

        self.make_log(user_id, message, CHANGE)

    def add_log(self, user_id, attribute, new_state, additional_message=""):
        message = _('Add "{attribute}" -> "{new_state}"').format(
            **{'attribute': attribute,
             'new_state': new_state,
             }
        )
        if additional_message:
            message += " ({})".format(additional_message)

        self.make_log(user_id, message, ADDITION)

    def del_log(self, user_id, attribute, old_state, additional_message=""):
        message = _('Delete "{attribute}" -> "{old_state}"').format(
            **{'attribute': attribute,
             'old_state': old_state,
             }
        )
        if additional_message:
            message += " ({})".format(additional_message)

        self.make_log(user_id, message, DELETION)
