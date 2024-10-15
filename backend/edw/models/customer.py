# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import string
from six import with_metaclass, python_2_unicode_compatible
from importlib import import_module
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, DEFAULT_DB_ALIAS
try:
    from django.db.models.fields import FieldDoesNotExist
except ImportError:
    from django.core.exceptions import FieldDoesNotExist
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.utils.translation import ugettext_lazy as _
from jsonfield.fields import JSONField
from .. import deferred

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore()


class CustomerQuerySet(models.QuerySet):
    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        ENG: Emulate filter queries on a Customer using attributes from the User object.
        Example: Customer.objects.filter(last_name__icontains='simpson') will return
        a queryset with customers whose last name contains "simpson".
        RUS: Эмуляция отфильтрованных запросов к пользователю  Customer с использованием атрибутов объекта User
        """
        opts = self.model._meta
        lookup_kwargs = {}
        for key, lookup in kwargs.items():
            try:
                field_name = key[:key.index('__')]
            except ValueError:
                field_name = key
            if field_name == 'pk':
                field_name = opts.pk.name
            try:
                opts.get_field(field_name)
                if isinstance(lookup, get_user_model()):
                    lookup.pk  # force lazy object to resolve
                lookup_kwargs[key] = lookup
            except FieldDoesNotExist as fdne:
                try:
                    get_user_model()._meta.get_field(field_name)
                    lookup_kwargs['user__' + key] = lookup
                except FieldDoesNotExist:
                    raise fdne
                except Exception as othex:
                    raise othex
        result = super(CustomerQuerySet, self)._filter_or_exclude(negate, *args, **lookup_kwargs)
        return result


class CustomerManager(models.Manager):
    """
    ENG: Manager for the Customer database model. This manager can also cope with customers, which have
    an entity in the database but otherwise are considered as anonymous. The username of these
    so called unrecognized customers is a compact version of the session key.
    RUS: Менеджер модели пользователя Customer.
    """
    BASE64_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase + '.@'
    REVERSE_ALPHABET = dict((c, i) for i, c in enumerate(BASE64_ALPHABET))
    BASE36_ALPHABET = string.digits + string.ascii_lowercase

    _queryset_class = CustomerQuerySet

    @classmethod
    def encode_session_key(cls, session_key):
        """
        ENG: Session keys have base 36 and length 32. Since the field ``username`` accepts only up
        to 30 characters, the session key is converted to a base 64 representation, resulting
        in a length of approximately 28.
        RUS: Преобразует ключ сеанса в представление base64,
         в результате чего длина ключа равна приблизительно 28.
        """
        return cls._encode(int(session_key[:32], 36), cls.BASE64_ALPHABET)

    @classmethod
    def decode_session_key(cls, compact_session_key):
        """
        ENG: Decode a compact session key back to its original length and base.
        RUS: Декодирует сеансовый ключ до его исходной длины и основания.
        """
        base_length = len(cls.BASE64_ALPHABET)
        n = 0
        for c in compact_session_key:
            n = n * base_length + cls.REVERSE_ALPHABET[c]
        return cls._encode(n, cls.BASE36_ALPHABET).zfill(32)

    @classmethod
    def _encode(cls, n, base_alphabet):
        """
        RUS: Переводит из кодировки сессионного ключа Base36 в кодировку Base64.
        """
        base_length = len(base_alphabet)
        s = []
        while True:
            n, r = divmod(n, base_length)
            s.append(base_alphabet[r])
            if n == 0:
                break
        return ''.join(reversed(s))

    def get_queryset(self):
        """
        ENG: Whenever we fetch from the Customer table, inner join with the User table to reduce the
        number of queries to the database.
        RUS: Возвращает объект запроса, который включает в выборку данные связанных 
        объектов при выполнении запроса между таблицами Customer и User.
        """
        qs = self._queryset_class(self.model, using=self._db).select_related('user')
        return qs

    def create(self, *args, **kwargs):
        """
        RUS: Создает пользователя Customer, если он аутентифицирован.
        """
        customer = super(CustomerManager, self).create(*args, **kwargs)
        if 'user' in kwargs and kwargs['user'].is_authenticated():
            customer.recognized = self.model.REGISTERED
        return customer

    def _get_visiting_user(self, session_key):
        """
        ENG: Since the Customer has a 1:1 relation with the User object, look for an entity for a
        User object. As its ``username`` (which must be unique), use the given session key.
        RUS: Проверка пользователя объектов Customer и User. Если данных о нем нет в сессионном ключе,
        то пользователь считается анонимным.
        """
        username = self.encode_session_key(session_key)
        try:
            user = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            user = AnonymousUser()
        return user

    def get_from_request(self, request):
        """
        ENG: Return an Customer object for the current User object.
        RUS: Возвращает объект Customer для текущего объекта User. 
        """
        is_anonymous = (request.user.is_anonymous() if callable(request.user.is_anonymous)
                        else request.user.is_anonymous)
        if is_anonymous and request.session.session_key:
            # the visitor is determined through the session key
            user = self._get_visiting_user(request.session.session_key)
        else:
            user = request.user
        try:
            if user.customer:
                return user.customer
        except AttributeError:
            pass
        is_authenticated = (request.user.is_authenticated() if callable(request.user.is_authenticated)
                   else request.user.is_authenticated)
        if is_authenticated:
            customer, created = self.get_or_create(user=user)
            if created:  # `user` has been created by another app than shop
                customer.recognized = self.model.REGISTERED
                customer.save()
        else:
            customer = VisitingCustomer()
        return customer

    def get_or_create_from_request(self, request):
        """
        RUS: Возвращает объект Customer при прохождении аутентификации 
        или создает новый объект.
        """
        is_authenticated = (request.user.is_authenticated() if callable(request.user.is_authenticated)
                   else request.user.is_authenticated)
        if is_authenticated:
            user = request.user
            recognized = self.model.REGISTERED
        else:
            if not request.session.session_key:
                request.session.cycle_key()
                assert request.session.session_key
            username = self.encode_session_key(request.session.session_key)
            # create an inactive intermediate user, which later can declare himself as
            # guest, or register as a valid Django user
            user = get_user_model().objects.create_user(username)
            user.is_active = False
            user.save()
            recognized = self.model.UNRECOGNIZED
        (customer, is_created) = self.get_or_create(user=user)
        customer.recognized = recognized
        return (customer, is_created)


@python_2_unicode_compatible
class BaseCustomer(with_metaclass(deferred.ForeignKeyBuilder, models.Model)):
    """
    ENG: Base class for edw customers.

    Customer is a profile model that extends
    the django User model if a customer is authenticated. On checkout, a User
    object is created for anonymous customers also (with unusable password).
    RUS: Базовый класс пользвателей EDW, который расширяет модель пользователя django, 
    если клиент аутентифицирован.
    """
    SALUTATION = (('mrs', _("Mrs.")), ('mr', _("Mr.")), ('na', _("(n/a)")))
    UNRECOGNIZED = 0
    GUEST = 1
    REGISTERED = 2
    CUSTOMER_STATES = ((UNRECOGNIZED, _("Unrecognized")), (GUEST, _("Guest")), (REGISTERED, _("Registered")))

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    recognized = models.PositiveSmallIntegerField(_("Recognized as"), choices=CUSTOMER_STATES,
        help_text=_("Designates the state the customer is recognized as."), default=UNRECOGNIZED)
    salutation = models.CharField(_("Salutation"), max_length=5, choices=SALUTATION)
    last_access = models.DateTimeField(_("Last accessed"), default=timezone.now)
    extra = JSONField(default={}, editable=False,
        verbose_name=_("Extra information about this customer"))

    objects = CustomerManager()

    class Meta:
        abstract = True

    def __str__(self):
        """
        RUS: Возвращает имя пользователя модели Customer в строковом виде.
        """
        return self.get_username()

    def get_username(self):
        """
        RUS: Возвращает имя пользователя модели Customer.
        """
        return self.user.get_username()

    def get_full_name(self):
        """
        RUS: Возвращает полное имя пользователя модели Customer.
        """
        full_name = self.user.get_full_name()
        return full_name if full_name != '' else self.get_username()

    @property
    def organisation_detail(self):
        if self.extra is not None and self.extra.get("organisation") is not None and \
                isinstance(self.extra["organisation"], dict):
            return self.extra["organisation"]

        return {}

    @property
    def is_organisation(self):
        """
        {'organisation': {'oid': 1063633333, 'prnOid': 1019777777, 'fullName': 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КОМПАНИЯ"', 'shortName': 'ООО "КОМПАНИЯ"', 'ogrn': '1163123077777', 'type': 'LEGAL', 'chief': True, 'admin': False, 'phone': '+7(4722)333333', 'email': 'team@infolabs.ru', 'active': True, 'hasRightOfSubstitution': True, 'hasApprovalTabAccess': False, 'isLiquidated': False}}
        :return:
        """
        return True if self.organisation_detail.get('oid', None) is not None else False

    @property
    def organisation_full_name(self):

        return self.organisation_detail.get('fullName', "")

    @property
    def organisation_short_name(self):

        return self.organisation_detail.get('shortName', "")


    @property
    def organisation_inn(self):

        return self.organisation_detail.get('inn', "")

    @property
    def organisation_ogrn(self):

        return self.organisation_detail.get('ogrn', "")


    @property
    def first_name(self):
        """
        RUS: Возвращает имя пользователя модели Customer.
        """
        return self.user.first_name

    @first_name.setter
    def first_name(self, value):
        """
        ENG: Pending deprecation: warnings.warn("Property first_name is deprecated and will be removed").
        RUS: Имя будет заменено новым значением, если яявляется устаревшим.
        """
        self.user.first_name = value

    @property
    def last_name(self):
        """
        ENG: Pending deprecation: warnings.warn("Property last_name is deprecated and will be removed").
        RUS: Фамилия будет удалена, если является устаревшей.
        """
        return self.user.last_name

    @last_name.setter
    def last_name(self, value):
        """
        ENG: Pending deprecation: warnings.warn("Property last_name is deprecated and will be removed").
        RUS: Фамилия будет заменена новым значением, если яявляется устаревшей.
        """
        self.user.last_name = value

    @property
    def email(self):
        """
        RUS: Определяет email пользователя модели Customer.
        """
        return self.user.email

    @email.setter
    def email(self, value):
        """
        RUS: Присваивает новое значение email пользователя модели Customer.
        """
        self.user.email = value

    @property
    def date_joined(self):
        """
        RUS: Возвращает дату и время создания аккаунта пользователя модели Customer.
        """
        return self.user.date_joined

    @property
    def last_login(self):
        """
        RUS: Определяет дату и время последнего входа пользователя модели Customer в систему.
        """
        return self.user.last_login

    def is_anonymous(self):
        """
        RUS: Определяет статус не прошедшего аутентификацию ипользователя модели Customer.
        """
        return self.recognized in (self.UNRECOGNIZED, self.GUEST)

    def is_authenticated(self):
        """
        RUS: Определяет статус прошедшего аутентификацию ипользователя модели Customer.
        """
        return self.recognized == self.REGISTERED

    def is_recognized(self):
        """
        ENG: Return True if the customer is associated with a User account.
        Unrecognized customers have accessed the shop, but did not register
        an account nor declared themselves as guests.
        RUS: Разграничивает права прошедших аутентификацию пользователей и непрошедших.
        """
        return self.recognized != self.UNRECOGNIZED

    def is_guest(self):
        """
        ENG: Return true if the customer isn't associated with valid User account, but declared
        himself as a guest, leaving their email address.
        RUS: У пользователя появляется статус Гость, если он незарегистрирован, но оставил свой email. 
        """
        return self.recognized == self.GUEST

    def recognize_as_guest(self):
        """
        ENG: Recognize the current customer as guest customer.
        RUS: Определяет статус пользователя в качестве Гостя
        """
        self.recognized = self.GUEST

    def is_registered(self):
        """
        ENG: Return true if the customer has registered himself.
        RUS: Проверяет регистрацию пользователя
        """
        return self.recognized == self.REGISTERED

    def recognize_as_registered(self):
        """
        ENG: Recognize the current customer as registered customer.
        RUS: Определяет статус пользователя в качестве зарегистрированного
        """
        self.recognized = self.REGISTERED

    def is_visitor(self):
        """
        ENG: Always False for instantiated Customer objects.
        RUS: Пользователь со статусом посетитель не является объектом модели Customer
        """
        return False

    def is_expired(self):
        """
        ENG: Return true if the session of an unrecognized customer expired.
        Registered customers never expire.
        Guest customers only expire, if they failed fulfilling the purchase (currently not implemented).
        RUS: Проверяет, является ли сессия истекшей для незарегистрированных пользователей.
        """
        if self.recognized == self.UNRECOGNIZED:
            session_key = CustomerManager.decode_session_key(self.user.username)
            return not SessionStore.exists(session_key)
        return False

    def get_or_assign_number(self):
        """
        ENG: Hook to get or to assign the customers number. It shall be invoked, every time an Order
        object is created. If the customer number shall be different from the primary key, then
        override this method.
        RUS: Получает или при отсутствии присваивает номер id зарегистрированного пользователя.
        """
        return self.get_number()

    def get_number(self):
        """
        ENG: Hook to get the customers number. Customers haven't purchased anything may return None.
        RUS: Возвращает номер id зарегистрированного пользователя в строковом формате.
        """
        return str(self.user_id)

    def save(self, **kwargs):
        """
        RUS: Сохраняет данные пользователя.
        """
        if 'update_fields' not in kwargs:
            self.user.save(using=kwargs.get('using', DEFAULT_DB_ALIAS))
        super(BaseCustomer, self).save(**kwargs)

    def delete(self, *args, **kwargs):
        """
        RUS: Удаляет данные неаутентифицированного пользователя и аутентифицированного через каскадное удаление.
        """
        if self.user.is_active and self.recognized == self.UNRECOGNIZED:
            # invalid state of customer, keep the referred User
            super(BaseCustomer, self).delete(*args, **kwargs)
        else:
            # also delete self through cascading
            self.user.delete(*args, **kwargs)

CustomerModel = deferred.MaterializedModel(BaseCustomer)


class VisitingCustomer(object):
    """
    ENG: This dummy object is used for customers which just visit the site. Whenever a VisitingCustomer
    adds something to the cart, this object is replaced against a real Customer object.
    RUS: Класс анонимного (незарегистрированного) пользователя-посетителя сайта, статус которого может меняться
    в зависимости от совершенных действий.
    """
    user = AnonymousUser()

    def __str__(self):
        """
        RUS: Возвращает строковое представление объекта.
        """
        return 'Visitor'

    @property
    def email(self):
        """
        RUS: Пользователь со статусом посетитель может не указывать при регистрации свой email адрес.
        """
        return ''

    @email.setter
    def email(self, value):
        """
        RUS: Email адрес пользователя неуказан и поэтому не хранится и не возвращается.
        """
        pass

    def is_anonymous(self):
        """
        RUS: Проверка анонимности пользователя.
        """
        return True

    def is_authenticated(self):
        """
        RUS: Проверка аутентификации пользователя. Анонимный пользователь не является аутентифицированным.
        """
        return False

    def is_recognized(self):
        """
        RUS: Проверка регистрации пользователя в модели. Анонимный пользователь не зарегистрирован.
        """
        return False

    def is_guest(self):
        """
        RUS: Проверка статуса Гость пользователя. Анонимный пользователь не является гостем,
        поскольку не оставил свой email адрес.
        """
        return False

    def is_registered(self):
        """
        RUS: Проверяет, является пользователь зарегистрированным. 
        Анонимный пользователь не является зарегистрированным.
        """
        return False

    def is_visitor(self):
        """
        RUS: Проверка статуса Посетитель пользователя. Анонимный пользователь является посетителем.
        """
        return True

    def save(self, **kwargs):
        """
        RUS: Сохраняет у пользователя статус Посетитель.
        """
        pass


@receiver(user_logged_in)
def handle_customer_login(sender, **kwargs):
    """
    ENG: Update request.customer to an authenticated Customer.
    RUS: Авторизовывает аутентифицированного пользователя и уведомляет его об этом.
    """
    try:
        kwargs['request'].customer = kwargs['request'].user.customer
    except (AttributeError, ObjectDoesNotExist):
        kwargs['request'].customer = SimpleLazyObject(lambda: CustomerModel.objects.get_from_request(kwargs['request']))


@receiver(user_logged_out)
def handle_customer_logout(sender, **kwargs):
    """
    ENG: Update request.customer to a visiting Customer.
    RUS: Используется для отмены авторизации пользователя и очистки данных сессии и его уведомлении.
    """
    # defer assignment to anonymous customer, since the session_key is not yet rotated
    kwargs['request'].customer = SimpleLazyObject(lambda: CustomerModel.objects.get_from_request(kwargs['request']))
