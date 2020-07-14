# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bitfield import BitField
from bitfield.types import Bit
from filer.fields.file import FilerFileField
from post_office import mail
from post_office.models import EmailTemplate
from rest_framework.request import Request
from rest_framework.settings import api_settings

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpRequest
from django.utils.six.moves.urllib.parse import urlparse
from django.utils import translation

from edw.models.mixins.notification import NotificationMixin
from edw.models.fields.notification import MultiSelectField
from edw.settings import APP_LABEL

if getattr(settings, 'FIREBASE_KEY_PATH', None):
    from fcm_async import push
else:
    push = None

email_validator = EmailValidator()


class EmulateHttpRequest(HttpRequest):
    """
    Use this class to emulate a HttpRequest object, when templates must be rendered
    asynchronously, for instance when an email must be generated out of an Notification object.
    """
    def __init__(self, customer, stored_request):
        super(EmulateHttpRequest, self).__init__()
        parsedurl = urlparse(stored_request.get('absolute_base_uri'))
        self.path = self.path_info = parsedurl.path
        self.environ = {}
        self.META['PATH_INFO'] = parsedurl.path
        self.META['SCRIPT_NAME'] = ''
        self.META['HTTP_HOST'] = parsedurl.netloc
        self.META['HTTP_X_FORWARDED_PROTO'] = parsedurl.scheme
        self.META['QUERY_STRING'] = parsedurl.query
        self.META['HTTP_USER_AGENT'] = stored_request.get('user_agent')
        self.META['REMOTE_ADDR'] = stored_request.get('remote_ip')
        self.method = 'GET'
        self.LANGUAGE_CODE = self.COOKIES['django_language'] = stored_request.get('language')
        self.customer = customer
        if customer is not None:
            self.user = customer.is_anonymous() and AnonymousUser or customer.user
        else:
            self.user = AnonymousUser()


class Notification(models.Model):
    """
    ENG: A task executed on receiving a signal.
    RUS: Диспетчер сигналов. Задача выполняется при получении сигнала.
    """
    MODES = {
        0: ('email', _('By Email')),
        1: ('push', _('By Push Notification')),
    }

    RECIPIENTS_EMPTY_CHOICES_VALUE = ('0', _("Nobody"))

    """
        "1":  "owner",
        "2": "moderate_person",
        "3": "responsible_person",
        "4": "private_person",
        "5": "auditory_persons",
        "6": "regional_persons"
    """
    RECIPIENTS_ROLES_CHOICES = (
        RECIPIENTS_EMPTY_CHOICES_VALUE,

    )


    SPLIT_CHARSET = ','

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    transition = MultiSelectField(verbose_name=_('Transition'), max_length=400,
                                       dinamic_choices_model_attr='get_transition_choices', blank=True)

    notify_to_roles = MultiSelectField(verbose_name=_('Notify to roles'), max_length=255, default='0',
                                       dinamic_choices_model_attr='get_notification_recipients_roles_choices')

    copy_to = models.ManyToManyField('CustomerProxy', blank=True, limit_choices_to={'is_staff':  True})
    template = models.ForeignKey(EmailTemplate, verbose_name=_("Template"),
                                 limit_choices_to=Q(language__isnull=True) | Q(language=''))

    mode = BitField(flags=MODES, verbose_name=_('Mode'), default=Bit(0).mask)
    active = models.BooleanField(verbose_name=_("Active"), default=True)

    #TODO: удалить
    transition_target = models.CharField(max_length=255, verbose_name=_("Event"))
    notify_to = models.IntegerField(verbose_name=_("Notify to"), null=True,
                                    blank=True, default=None)

    class Meta:
        app_label = APP_LABEL
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ('transition',)

    def __str__(self):
        return self.name

    @staticmethod
    def get_senders_objects():
        """
        RUS: Получение списка моделей для которых можно отправлять уведомления
        :return: [ список моделей, ... ]
        """

        return NotificationMixin._notification_classes.values()

    @staticmethod
    def get_transition_name(object_model, source, target):
        """
        RUS: Получение форматированного наименования состояния

        :param object_model: модель объекта
        :param source: наименование начального состояния
        :param target: наименование конечного состояния
        :return: форматированную строку модель:начальное состояние: конечное состояние
        """

        return '{}:{}:{}'.format(object_model.__name__.lower(), source, target)

    @classmethod
    def get_notification_recipients_roles_choices(cls):
        """
        RUS: Получение типов получателей доступных для уведомления для всех моделей
        :return: ((id:  _("title")), ...)
        """
        choices = list(cls.RECIPIENTS_ROLES_CHOICES)
        senders_objects = cls.get_senders_objects()

        for sender in senders_objects:
            for obj in sender.get_notification_recipients_roles_choices():
                if obj not in choices:
                    choices.append(obj)

        return choices

    @classmethod
    def get_transition_choices(cls):
        """
        RUS: Получение доступных вариантов переходов состояний для всех моделей
        :return:
            [(ransition_choice_name, transition_choice_title),...]
        """
        choices = {}
        for clazz in cls.get_senders_objects():
            for transition in clazz.get_notification_transitions():
                transition_choice_name = cls.get_transition_name(clazz, transition.source, transition.target)
                transition_choice_title = "{}: {} - {} ({} - {})".format(
                    clazz._meta.verbose_name,
                    clazz.get_transition_name(transition.source),
                    clazz.get_transition_name(transition.target),
                    transition.source,
                    transition.target
                )
                choices[transition_choice_name] = transition_choice_title

        return sorted(choices.items(), key=lambda item: item[1])

    @classmethod
    def get_avalible_recipients_roles_for_notifications(cls):
        """
        RUS: Получение всех доступных ролей для состояниий
        :return: словарь {'модель:начальное состояние:конечное состояние': [ ид роли, ...]}
        """
        roles_dict = {}
        senders_objects = cls.get_senders_objects()
        empty_value = cls.RECIPIENTS_EMPTY_CHOICES_VALUE[0]
        for sender in senders_objects:
            sender_name = sender.__name__.lower()
            for key, value in sender.get_avalible_recipients_roles_for_notifications().items():
                if not empty_value in value:
                    value.append(empty_value)
                roles_dict["%s:%s" % (sender_name, key)] = value

        return roles_dict

    @classmethod
    def send_notification(cls, object, source, target, **kwargs):
        """
        RUS: Главная функция для подписки на сигналы
        Отправка уведомлений по подписанным событиям
        :param object: объект уведомления
        :param source: начальное состояние
        :param target: конечное состояние
        :param kwargs:

        """

        transition_name = cls.get_transition_name(type(object), source, target)

        for n in Notification.objects.filter(transition__contains=transition_name, active=True):
            if n.mode.email:
                n.notify_by_email(object, source, target)
            if n.mode.push:
                n.notify_by_push(object, source, target)



    def get_notify_recipients_roles(self):
        """
        RUS: Получение списка ролей персон для уведомления из модели
        :return: [Идентивикатор роли,...]
        """

        return [recipient_id for recipient_id in self.notify_to_roles if recipient_id!=self.RECIPIENTS_ROLES_CHOICES[0][0]]

    def notify_by_email(self, object, source, target, **kwargs):
        """
        RUS: Отправка уведомлениий по email
        :param object: Объект уведомления Entity
        :param source - имя начального состояния
        :param target - имя конечного состояния

        recipients - список сосотящий из (email, пользователя, класс сериализации пользователя)
        example: [(root@root.ru, customer_object, CustomerSerializer), ...]
        """

        recipients = [] #  - list of tuples (recipient_email, recipient_object, recipient_serialaizer_cls)
        if self.copy_to:
            recipients.extend(object.get_email_notification_recipients(self.copy_to.all()))


        recipients_roles = self.get_notify_recipients_roles()
        if recipients_roles:
            recipients.extend(object.get_email_notification_recipients_by_roles(recipients_roles))

        if recipients:
            self.notify(recipients, object, source, target, 'email')

    def notify_by_push(self, object, source, target, **kwargs):
        """
        RUS: Отправка push уведомлениий
        :param object: Объект уведомления Entity
        :param source - имя начального состояния
        :param target - имя конечного состояния

        recipients - список сосотящий из (id пользователя, пользователя, класс сериализации пользователя)
        example: [(key, customer_object, CustomerSerializer), ...]
        """

        if push is not None:
            recipients = []  # - list of tuples (recipient_key, recipient_object, recipient_serialaizer_cls)
            if self.copy_to:
                recipients.extend(object.get_push_notification_recipients(self.copy_to.all()))

            recipients_roles = self.get_notify_recipients_roles()
            if recipients_roles:
                recipients.extend(object.get_push_notification_recipients_by_roles(recipients_roles))

            if recipients:
                self.notify(recipients, object, source, target, 'push')

    def notify(self, recipients, object, source, target, mode='email',**kwargs):
        """
        RUS: Подготовка и отправка сообщений по списку получателей

        :param recipients: список сосотящий из [(email или push_id, пользователь, класс сериализации пользователя),...]
        :param object: объект уведомления
        :param source - имя начального состояния
        :param target - имя конечного состояния
        :param mode: 'email' или 'push'

        """

        # подготовка общего контекста
        stored_request = object.stored_request[0] if isinstance(
            object.stored_request, (tuple, list)) else object.stored_request

        emulated_request = EmulateHttpRequest(object.customer, stored_request)
        authenticators = [auth() for auth in api_settings.DEFAULT_AUTHENTICATION_CLASSES]

        serialaizer_cls = object.get_serialaizer_class()
        entity_serializer = serialaizer_cls(
            object,
            context={'request': Request(emulated_request, authenticators=authenticators)}
        )

        language = stored_request.get('language')
        translation.activate(language)

        try:
            template = self.template.translated_templates.get(language=language)
        except EmailTemplate.DoesNotExist:
            template = self.template
        attachments = {}
        for notiatt in self.notificationattachment_set.all():
            attachments[notiatt.attachment.original_filename] = notiatt.attachment.file.file


        context = {
            'data': entity_serializer.data,
            'ABSOLUTE_BASE_URI': emulated_request.build_absolute_uri().rstrip('/'),
            'render_language': language,
            'transition': {
                'source': {
                    'name': source,
                    'title': object.get_transition_name(source)
                },
                'target': {
                    'name': target,
                    'title': object.get_transition_name(target)
                },
            }
        }

        # отправка уведомления пользователям
        if mode=='email':
            for recipient in recipients:
                try:
                    email_validator(recipient[0])
                except ValidationError:
                    pass
                else:
                    # подготовка контекста получателя
                    recipient_serialaizer_cls = recipient[2]
                    context['recipient'] = recipient_serialaizer_cls(recipient[1]).data

                    mail.send(recipient[0], template=template, context=context,
                              attachments=attachments, render_on_delivery=True)

        elif mode=='push' and push is not None:

            for recipient in recipients:
                # подготовка контекста получателя
                recipient_serialaizer_cls = recipient[2]
                context['recipient'] = recipient_serialaizer_cls(recipient[1]).data

                push.send(recipient[0], template=template, context=context, render_on_delivery=True)


class NotificationAttachment(models.Model):
    """
    RUS: Приложение для уведомлений.
    Определяет поле для хранения файлов-уведомлений.
    """
    notification = models.ForeignKey(Notification)
    attachment = FilerFileField(null=True, blank=True, related_name='email_attachment', verbose_name=_("Attachment"))

    class Meta:
        app_label = APP_LABEL
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

