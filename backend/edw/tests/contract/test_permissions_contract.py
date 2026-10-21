# -*- coding: utf-8 -*-
"""
E4: контракт прав API django-edw на стеке DRF 3.18 / Django 5.2.

Проверки фиксируют текущую (строгую) семантику классов edw.rest.permissions и
модели DataMartPermission. Ослабление любого правила — регрессия:
* небезопасный метод для анонимного пользователя запрещён;
* обычный аутентифицированный пользователь не получает прав на запись;
* суперпользователь/администратор получает доступ только со статусом active;
* при наличии строк DataMartPermission клиент без собственной строки не получает
  прав (deny-by-default), has_owner=True — это сигнал ограничения, а не разрешения.
"""
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import permissions as drf_permissions
from rest_framework.test import APIClient

from edw.rest import permissions as edw_permissions
from edw.tests.contract.app.models import (
    Customer,
    DataMart,
    DataMartPermission,
)

DENIED_DATAMART_PERMISSIONS = {
    'can_add': False,
    'can_change': False,
    'can_delete': False,
    'has_owner': False,
}

ALLOWED_DATAMART_PERMISSIONS = {
    'can_add': True,
    'can_change': True,
    'can_delete': True,
    'has_owner': False,
}


def make_request(method='get', user=None, data=None):
    """Django-запрос с явным пользователем (без middleware и DRF-аутентификации)."""
    request = getattr(RequestFactory(), method)('/', data or {})
    request.user = AnonymousUser() if user is None else user
    # View'ы EDW кладут в GET разобранные права витрины (_data_mart_permissions).
    request.GET = request.GET.copy()
    return request


def make_user(**kwargs):
    kwargs.setdefault('is_active', True)
    return User(username='user-{}'.format(abs(hash(repr(sorted(kwargs.items()))))), **kwargs)


class Owned(object):
    """Минимальный объект с атрибутом owner для object-level проверок."""

    def __init__(self, owner):
        self.owner = owner


def test_is_read_only_contract():
    permission = edw_permissions.IsReadOnly()
    owner = make_user()

    for method in ('get', 'head', 'options'):
        assert permission.has_permission(make_request(method, owner), None)
        assert permission.has_object_permission(make_request(method, owner), None, Owned(owner))

    for method in ('post', 'put', 'patch', 'delete'):
        assert not permission.has_permission(make_request(method, owner), None)
        assert not permission.has_object_permission(make_request(method, owner), None, Owned(owner))


def test_is_superuser_or_read_only_contract():
    permission = edw_permissions.IsSuperuserOrReadOnly()
    superuser = make_user(is_superuser=True, is_staff=True)
    inactive_superuser = make_user(is_superuser=True, is_staff=True, is_active=False)
    regular = make_user()

    assert permission.has_permission(make_request('get', AnonymousUser()), None)
    assert not permission.has_permission(make_request('post', AnonymousUser()), None)

    assert permission.has_permission(make_request('post', superuser), None)
    assert permission.has_object_permission(make_request('delete', superuser), None, Owned(regular))

    # Неактивный суперпользователь не получает доступа.
    assert not permission.has_permission(make_request('post', inactive_superuser), None)
    assert not permission.has_object_permission(
        make_request('post', inactive_superuser), None, Owned(inactive_superuser)
    )

    # Обычный пользователь остаётся read-only.
    assert permission.has_permission(make_request('get', regular), None)
    assert not permission.has_permission(make_request('post', regular), None)


def test_is_owner_or_read_only_contract():
    permission = edw_permissions.IsOwnerOrReadOnly()
    owner = make_user()
    other = make_user()

    assert permission.has_object_permission(make_request('get', other), None, Owned(owner))
    assert permission.has_object_permission(make_request('delete', owner), None, Owned(owner))
    assert not permission.has_object_permission(make_request('delete', other), None, Owned(owner))
    # Объект без owner недоступен на запись.
    assert not permission.has_object_permission(make_request('delete', owner), None, object())


def test_is_owner_or_staff_or_superuser_contract():
    permission = edw_permissions.IsOwnerOrStaffOrSuperuser()
    staff = make_user(is_staff=True)
    superuser = make_user(is_superuser=True)
    owner = make_user()
    other = make_user()

    assert permission.has_permission(make_request('get', staff), None)
    assert permission.has_permission(make_request('post', superuser), None)
    assert not permission.has_permission(make_request('get', owner), None)
    assert not permission.has_permission(make_request('get', AnonymousUser()), None)

    assert permission.has_object_permission(make_request('get', staff), None, Owned(other))
    assert permission.has_object_permission(make_request('post', owner), None, Owned(owner))
    assert not permission.has_object_permission(make_request('post', other), None, Owned(owner))


def test_is_superuser_or_datamart_has_owner_contract():
    permission = edw_permissions.IsSuperuserOrDataMartHasOwnerOrReadOnly()
    regular = make_user()
    superuser = make_user(is_superuser=True)

    request = make_request('post', regular)
    assert not permission.has_permission(request, None)

    # has_owner=True — ограничение (витрина закрыта), а не разрешение.
    request.GET['_data_mart_permissions'] = {'has_owner': True}
    assert permission.has_permission(request, None)
    assert permission.has_object_permission(request, None, object())

    request.GET['_data_mart_permissions'] = {'has_owner': False}
    assert not permission.has_permission(request, None)
    assert not permission.has_object_permission(request, None, object())

    # Анонимный запрос без вычисленных прав запрещён.
    assert not permission.has_permission(make_request('post', AnonymousUser()), None)

    # Параметр из query-string — строка, а не mapping прав: отказ, не 500.
    anonymous_request = make_request('post', AnonymousUser())
    anonymous_request.GET['_data_mart_permissions'] = 'has_owner=true'
    assert permission.has_permission(anonymous_request, None) is False

    # Суперпользователь проходит независимо от флага.
    superuser_request = make_request('post', superuser)
    superuser_request.GET['_data_mart_permissions'] = {'has_owner': False}
    assert permission.has_permission(superuser_request, None)


@pytest.mark.django_db
def test_datamart_permission_deny_by_default():
    """
    DataMartPermission не ослаблен: при наличии строк прав клиент без своей
    строки получает полный запрет, а has_owner=True означает лишь ограничение.
    """
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    user = User.objects.create_user('customer-1', password='secret')
    customer = Customer.objects.create(user=user, salutation='na')

    # Анонимный пользователь не получает ничего.
    assert data_mart.get_permissions_from_request(make_request('get', AnonymousUser())) == \
        DENIED_DATAMART_PERMISSIONS

    # Пока строк DataMartPermission нет, активный пользователь получает доступ.
    assert data_mart.get_permissions_from_request(make_request('get', user)) == \
        ALLOWED_DATAMART_PERMISSIONS

    # Появилась строка чужого клиента — у текущего клиента полный запрет.
    other_user = User.objects.create_user('customer-2', password='secret')
    other_customer = Customer.objects.create(user=other_user, salutation='na')
    DataMartPermission.objects.create(data_mart=data_mart, customer=other_customer)
    assert data_mart.get_permissions_from_request(make_request('get', user)) == {
        'can_add': False,
        'can_change': False,
        'can_delete': False,
        'has_owner': True,
    }

    # Собственная строка возвращает ровно выставленные флаги.
    DataMartPermission.objects.create(
        data_mart=data_mart,
        customer=customer,
        can_add=True,
        can_change=False,
        can_delete=True,
    )
    assert data_mart.get_permissions_from_request(make_request('get', user)) == {
        'can_add': True,
        'can_change': False,
        'can_delete': True,
        'has_owner': True,
    }

    # Суперпользователь не ограничен строками DataMartPermission.
    superuser = User.objects.create_superuser('root', 'root@example.com', 'secret')
    assert data_mart.get_permissions_from_request(make_request('get', superuser)) == \
        ALLOWED_DATAMART_PERMISSIONS

    # Неактивный пользователь не получает доступа даже со своей строкой.
    user.is_active = False
    user.save(update_fields=['is_active'])
    assert data_mart.get_permissions_from_request(make_request('get', user)) == \
        DENIED_DATAMART_PERMISSIONS


@pytest.mark.django_db
def test_drf_permission_flow_on_probe_view():
    """Права на уровне представления проверяются самим DRF 3.18, а не только классом."""
    client = APIClient()
    url = reverse('edw:permission-probe')

    assert client.get(url).status_code == 403

    regular = User.objects.create_user('regular', password='secret')
    client.force_authenticate(regular)
    assert client.get(url).status_code == 403

    staff = User.objects.create_user('staff', password='secret', is_staff=True)
    client.force_authenticate(staff)
    assert client.get(url).status_code == 200
    assert client.post(url).status_code == 200


def test_permission_classes_are_drf_base_permissions():
    """Классы прав по-прежнему являются нормальными BasePermission для DRF."""
    for name in (
        'IsReadOnly',
        'IsSuperuserOrReadOnly',
        'IsSuperuserOrDataMartHasOwnerOrReadOnly',
        'IsOwnerOrReadOnly',
        'IsOwnerOrStaffOrSuperuser',
    ):
        permission_class = getattr(edw_permissions, name)
        assert issubclass(permission_class, drf_permissions.BasePermission)
