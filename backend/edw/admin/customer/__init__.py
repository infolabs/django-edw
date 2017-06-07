#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import OneToOneRel
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.timezone import localtime
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.db import IntegrityError, transaction

from edw import settings as edw_settings

from edw.models.customer import CustomerModel

from .forms import CustomerChangeForm, CustomerCreationForm


class CustomerInlineAdmin(admin.StackedInline):
    model = CustomerModel
    fields = ('salutation', 'get_number', 'recognized')
    readonly_fields = ('get_number',)

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj is None else 1

    def has_add_permission(self, request):
        return False

    def get_number(self, customer):
        return customer.get_number()
    get_number.short_description = pgettext_lazy('customer', "Number")


class CustomerListFilter(admin.SimpleListFilter):
    title = _("Customer State")
    parameter_name = 'custate'

    def lookups(self, request, model_admin):
        return CustomerModel.CUSTOMER_STATES

    def queryset(self, request, queryset):
        try:
            custate = int(self.value())
            if custate in dict(CustomerModel.CUSTOMER_STATES):
                queryset = queryset.filter(customer__recognized=custate)
        finally:
            return queryset


class CustomerAdmin(UserAdmin):
    """
    This ModelAdmin class must be registered inside the implementation of this edw.
    """
    form = CustomerChangeForm
    add_form = CustomerCreationForm
    inlines = (CustomerInlineAdmin,)
    list_display = ('get_username', 'salutation', 'last_name', 'first_name', 'recognized',
        'last_access', 'is_unexpired')
    segmentation_list_display = ('get_username',)
    list_filter = UserAdmin.list_filter + (CustomerListFilter,)
    readonly_fields = ('last_login', 'date_joined', 'last_access', 'recognized')
    ordering = ('id',)

    class Media:
        js = ('edw/js/admin/customer.js',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(CustomerAdmin, self).get_fieldsets(request, obj=obj)
        if obj:
            fieldsets[0][1]['fields'] = ('username', 'recognized', 'password',)
            fieldsets[3][1]['fields'] = ('date_joined', 'last_login', 'last_access',)
        return fieldsets

    def to_field_allowed(self, request, to_field):
        opts = self.model._meta
        try:
            field = opts.get_field(to_field)
            if isinstance(field, OneToOneRel) and not hasattr(field, 'primary_key'):
                setattr(field, 'attname', 'id')
                setattr(field, 'primary_key', True)
        except FieldDoesNotExist:
            return False
        return super(CustomerAdmin, self).to_field_allowed(request, to_field)

    def get_username(self, user):
        if hasattr(user, 'customer'):
            return user.customer.get_username()
        return user.get_username()
    get_username.short_description = _("Username")
    get_username.admin_order_field = 'email'

    def salutation(self, user):
        if hasattr(user, 'customer'):
            return user.customer.get_salutation_display()
        return ''
    salutation.short_description = _("Salutation")
    salutation.admin_order_field = 'customer__salutation'

    def recognized(self, user):
        if hasattr(user, 'customer'):
            state = user.customer.get_recognized_display()
            if user.is_staff:
                state = '{}/{}'.format(state, _("Staff"))
            return state
        return _("User")
    recognized.short_description = _("State")

    def last_access(self, user):
        if hasattr(user, 'customer'):
            return localtime(user.customer.last_access).strftime("%d %B %Y %H:%M:%S")
        return _("No data")
    last_access.short_description = _("Last accessed")
    last_access.admin_order_field = 'customer__last_access'

    def is_unexpired(self, user):
        if hasattr(user, 'customer'):
            return not user.customer.is_expired()
        return True
    is_unexpired.short_description = _("Unexpired")
    is_unexpired.boolean = True

    def save_model(self, request, obj, form, change):
        try:
            with transaction.atomic():
                super(CustomerAdmin, self).save_model(request, obj, form, change)
        except IntegrityError as e:
            if obj.email is None:
                obj.email = ""
                super(CustomerAdmin, self).save_model(request, obj, form, change)
        else:
            raise e


class CustomerProxy(get_user_model()):
    """
    With this neat proxy model, we are able to place the Customer Model Admin into
    the section “MyEDW” instead of section email_auth.
    """
    class Meta:
        proxy = True
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        app_label = edw_settings.APP_LABEL


try:
    admin.site.unregister(get_user_model())
except admin.sites.NotRegistered:
    pass
