# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from jsonfield.fields import JSONField

from edw.models.mixins import ModelMixin
from edw.rest.serializers.customer import CustomerSerializer


class NotificationMixin(ModelMixin):

    _notification_classes = {}
    _notification_transitions = None
    NOTIFICATION_RECIPIENTS_ROLES_CHOICES = () # Example: ('0', _("Nobody")),
    NOTIFICATION_RECIPIENT_SERIALAIZER_CLASS = CustomerSerializer

    """
    RUS: Ограничение на отправку уведомлений для категорий пользователей по состоянию
    example: {'draft_to_published': ['1', '3']} разрешает отправлять уведомления о смене 
    состояния зи черновика в опубликовано только для типов '1' и '3' определенных в NOTIFICATION_PERSONS_TYPE_CHOICES.
    По умолчанию можно отправлять всем из NOTIFICATION_PERSONS_TYPE_CHOICES
    """
    AVALIBLE_PECIPIENTS_ROLES_FOR_TRANSITION = {}

    """
    RUS: Для хранения данных в кодировке JSON.
    """
    stored_request = JSONField(verbose_name=_("stored_request"), default={},
        help_text=_("Parts of the Request objects on the moment of submit."))


    def __new__(cls, *args, **kwargs):
        """
        RUS: перекрыт для регистрации класса в списке доступных для уведомлений
        """
        if not NotificationMixin._notification_classes.get(cls.__name__):
            NotificationMixin._notification_classes[cls.__name__] = cls

        return super(NotificationMixin, cls).__new__(cls)

    def send_notification(self, source, target):
        """
        RUS: Главная функция для подписки на сигналы
        Отправка уведомлений по подписанным событиям
        :param source: начальное состояние
        :param target: конечное состояние
        """

        from edw.models.notification import Notification
        Notification.send_notification(self, source, target)

    def get_email_notification_recipients(self, recipients):
        """
        RUS: Получение списка пользователей для email уведомления по полю Copy To
        По умолчанию recipient объект класса Customer
        :param recipients: - список объектов получателей
        :return: Список [(email, recipient_object, serialaizer_cls),...]
        """

        return [(customer.email, customer.customer, CustomerSerializer) for customer in recipients if customer.email]

    def get_email_notification_recipients_by_roles(self, recipient_roles):
        """
        RUS: Получение списка пользователей для email уведомления по ролям
        :param recipient_roles: - список id типов пользователей NOTIFICATION_RECIPIENTS_ROLES_CHOICES
        :return: Список [(email, recipient_object, serialaizer_cls),...]
        """

        return []

    def get_push_notification_recipients(self, recipients):
        """
        RUS: Получение списка пользователей для push уведомления по полю Copy To
        :param recipients: - список пользователей
        :return: Список [(push_id, recipient_object, serialaizer_cls),...]
        """

        return []

    def get_push_notification_recipients_by_roles(self, recipients_roles):
        """
        RUS: Получение списка пользователей для push уведомления по ролям
        :param recipients_roles: - список id типов пользователей NOTIFICATION_RECIPIENTS_ROLES_CHOICES
        :return: Список [(push_id, customer_object, serialaizer_cls),...]
        """

        return []

    @classmethod
    def get_notification_transitions(cls):
        """
        RUS: Получение состояний модели по которым можно отправлять уведомления
        :return: Список имен состояний
        """

        if not hasattr(cls,'_notification_transitions') or cls._notification_transitions == None:

            cls._notification_transitions = []
            status_fields = [f for f in cls._meta.fields if f.name == 'status']
            if status_fields:
                for field in status_fields:
                    cls._notification_transitions.extend(field.get_all_transitions(cls))
            else:
                raise NotImplementedError(
                    '{cls}.status must be implemented for using NotificationMixin.'.format(
                        cls=cls.__name__
                    )
                )

        return cls._notification_transitions

    @classmethod
    def get_serialaizer_class(cls):
        """
        RUS: Переопределить для каждой модели,
        по умолчанию используется EntityDetailSerializer
        :return: Возвращает класс сериалайзера для передачи данных в шаблон уведомления
        """

        from edw.rest.serializers.entity import EntityDetailSerializer
        return EntityDetailSerializer

    @classmethod
    def get_notification_recipients_roles_choices(cls):
        """
        RUS: Получение типов персон доступных для уведомления для модели
        :return:
        (('id', _("title")), ...)
        """

        return cls.NOTIFICATION_RECIPIENTS_ROLES_CHOICES

    @classmethod
    def get_avalible_recipients_roles_for_notifications(cls):
        """
        RUS: Получение ограничений по ролям получателей для состояний
        В случае если ограничений нет то устанавливаются все доступные для модели
        :return:
            {'draft:published': ['1', '3']} словарь разрешений
        """

        if not hasattr(cls, '_notification_roles_dict') or cls._notification_roles_dict == None:
            cls._notification_roles_dict = {}
            all_roles = [item[0] for item in cls.NOTIFICATION_RECIPIENTS_ROLES_CHOICES]
            transitions = cls.get_notification_transitions()

            for transition in transitions:
                roles = cls.AVALIBLE_PECIPIENTS_ROLES_FOR_TRANSITION.get(transition.name, None)
                cls._notification_roles_dict["%s:%s" % (transition.source, transition.target)] = roles if roles else all_roles

        return cls._notification_roles_dict

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