# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools
from operator import __or__ as OR

from django.utils import six
from django.db.models import Q
# from django.db.models.signals import pre_delete
from django.db.models.signals import pre_save

from edw.models.entity import EntityModel
from edw.models.customer import CustomerModel
from edw.models.mixins.entity.customer_category import CustomerCategoryMixin
from edw.models.email_category import EmailCategoryModel
from edw.signals import make_dispatch_uid


if six.PY3:
    from functools import reduce


# ==============================================================================
# Find Models with CustomerCategoryMixin
# ==============================================================================
_model_with_customer_category_mixin = []

Model = EntityModel.materialized
for clazz in itertools.chain([Model], Model.get_all_subclasses()):
    if issubclass(clazz, CustomerCategoryMixin):
        _model_with_customer_category_mixin.append(clazz)


# ==============================================================================
# Email category model event handlers
# ==============================================================================
# def on_pre_delete_email_category(sender, instance, **kwargs):
#     customer_category_term_id = instance.term.id
#     entities_ids = EntityModel.objects.instance_of(*_model_with_customer_category_mixin).filter(
#         terms__id=customer_category_term_id).values_list('id', flat=True)
#     EntityModel.terms.through.objects.filter(entity_id__in=entities_ids, term_id=customer_category_term_id).delete()


def on_pre_save_email_category(sender, instance, **kwargs):
    if instance.pk is not None:
        try:
            origin = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            if origin.term != instance.term:
                origin_customer_category_term_id = origin.term.id
                customer_category_term_id = instance.term.id
                entities_ids = EntityModel.objects.instance_of(*_model_with_customer_category_mixin).filter(
                    terms__id=origin_customer_category_term_id).values_list('id', flat=True)
                EntityModel.terms.through.objects.filter(
                    entity_id__in=list(entities_ids), term_id=origin_customer_category_term_id).update(
                    term_id=customer_category_term_id)


# ==============================================================================
# Customer model event handlers
# ==============================================================================
def on_pre_save_customer(sender, instance, **kwargs):
    if instance.pk is not None:
        try:
            origin = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            if origin.email != instance.email:
                q_lst = [Q(
                    **{"{}___customer_id".format(x.__name__): instance.pk}
                ) for x in _model_with_customer_category_mixin]
                entities = EntityModel.objects.filter(reduce(OR, q_lst))
                for entity in entities:
                    entity.save(validate_customer_category=True)


# def on_pre_delete_customer(sender, instance, **kwargs):
#     pass


#==============================================================================
# Connect
#==============================================================================

# EmailCategory
email_category_model = EmailCategoryModel.materialized

# pre_delete.connect(on_pre_delete_email_category, email_category_model,
#                    dispatch_uid=make_dispatch_uid(pre_delete, on_pre_delete_email_category, email_category_model))
pre_save.connect(on_pre_save_email_category, email_category_model,
                 dispatch_uid=make_dispatch_uid(pre_save, on_pre_save_email_category, email_category_model))

# Customer
customer_model = CustomerModel.materialized

# pre_delete.connect(on_pre_delete_customer, customer_model,
#                    dispatch_uid=make_dispatch_uid(pre_delete, on_pre_delete_customer, customer_model))
pre_save.connect(on_pre_save_customer, customer_model,
                 dispatch_uid=make_dispatch_uid(pre_save, on_pre_save_customer, customer_model))
