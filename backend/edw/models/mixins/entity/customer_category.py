# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.utils.encoding import force_text
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from edw.models.entity import EntityModel
from edw.models.email_category import get_email_category
from edw.models.term import TermModel


class CustomerCategoryMixin(object):
    """
    RUS: Добавляет в модель категорию пользователя которая определяется по его почтовому адресу,
    возможна ручная установка.
    """

    REQUIRED_FIELDS = ('customer',)

    CUSTOMER_CATEGORY_ROOT_TERM_SLUG = "customer-category"
    UNKNOWN_CUSTOMER_TERM_SLUG = "unknown-customer"

    @classmethod
    def validate_term_model(cls):
        """
        RUS: Добавляет термин 'Категория пользователя' и 'Неизвестный пользователь' в модель терминов TermModel
        при их отсутствии.
        """
        # валидируем только один раз
        key = 'vldt:сstmr_ctgr'
        need_validation = EntityModel._validate_term_model_cache.get(key, True)
        if need_validation:
            EntityModel._validate_term_model_cache[key] = False

            with transaction.atomic():
                try:  # customer-category
                    customer_category = TermModel.objects.get(slug=cls.CUSTOMER_CATEGORY_ROOT_TERM_SLUG, parent=None)
                except TermModel.DoesNotExist:
                    customer_category = TermModel(
                        slug=cls.CUSTOMER_CATEGORY_ROOT_TERM_SLUG,
                        parent=None,
                        name=force_text(_('Customer category')),
                        semantic_rule=TermModel.XOR_RULE,
                        system_flags=(TermModel.system_flags.delete_restriction |
                                      TermModel.system_flags.change_parent_restriction |
                                      TermModel.system_flags.change_slug_restriction))
                    customer_category.save()
            with transaction.atomic():
                try:  # unknown-customer
                    customer_category.get_descendants(include_self=False).get(slug=cls.UNKNOWN_CUSTOMER_TERM_SLUG)
                except TermModel.DoesNotExist:
                    unknown_customer = TermModel(
                        slug=cls.UNKNOWN_CUSTOMER_TERM_SLUG,
                        parent_id=customer_category.id,
                        name=force_text(_('Unknown customer')),
                        semantic_rule=TermModel.OR_RULE,
                        system_flags=(TermModel.system_flags.delete_restriction |
                                      TermModel.system_flags.change_parent_restriction |
                                      TermModel.system_flags.change_slug_restriction |
                                      TermModel.system_flags.has_child_restriction))
                    unknown_customer.save()
        super(CustomerCategoryMixin, cls).validate_term_model()

    @staticmethod
    def customer_category_root_term():
        """
        RUS: Ищет корневой термин категории пользователей в модели TermModel (slug = "customer-category").
        Результат кешируется.
        """
        customer_category_root = getattr(EntityModel, "_customer_category_root_term_cache", None)
        if customer_category_root is None:
            try:
                customer_category_root = TermModel.objects.get(
                    slug=CustomerCategoryMixin.CUSTOMER_CATEGORY_ROOT_TERM_SLUG, parent=None)
            except TermModel.DoesNotExist:
                pass
            else:
                EntityModel._customer_category_root_term_cache = customer_category_root
        return customer_category_root

    @staticmethod
    def get_unknown_customer_term():
        """
        RUS: Ищет термин - неизвестная категория пользователей в модели TermModel (slug = "unknown-customer").
        Результат кешируется.
        """
        unknown_customer = getattr(EntityModel, "_unknown_customer_term_cache", None)
        if unknown_customer is None:
            customer_category_root = CustomerCategoryMixin.customer_category_root_term()
            if customer_category_root is not None:
                try:
                    unknown_customer = customer_category_root.get_descendants(include_self=False).get(
                        slug=CustomerCategoryMixin.UNKNOWN_CUSTOMER_TERM_SLUG)
                except TermModel.DoesNotExist:
                    pass
                else:
                    EntityModel._unknown_customer_term_cache = unknown_customer
        return unknown_customer

    @staticmethod
    def get_all_customer_categories_terms_ids_set():
        """
        RUS: Добавляет список ids терминов категорий пользователей.
        """
        customer_category_root = CustomerCategoryMixin.customer_category_root_term()
        if customer_category_root is not None:
            ids = customer_category_root.get_descendants(include_self=True).values_list('id', flat=True)
        else:
            ids = []
        return set(ids)

    @cached_property
    def all_customer_categories_terms_ids_set(self):
        """
        RUS: Кэширует список ids категорий терминов.
        """
        return self.get_all_customer_categories_terms_ids_set()

    @cached_property
    def customer_categories_terms_ids_set(self):
        ids = EntityModel.terms.through.objects.filter(
            Q(entity_id=self.id) &
            Q(term_id__in=self.all_customer_categories_terms_ids_set)
        ).values_list('term_id', flat=True)
        return set(ids)

    def clean_terms(self, terms):
        ids_set = self.all_customer_categories_terms_ids_set
        new_terms, customer_categories_terms_ids = [], []
        for x in terms:
            if x.id not in ids_set:
                new_terms.append(x)
            else:
                customer_categories_terms_ids.append(x.id)
        # save customer categories terms ids for validation
        self._clean_customer_categories_terms_ids_set = set(customer_categories_terms_ids)
        return super(CustomerCategoryMixin, self).clean_terms(new_terms)

    def need_terms_validation_after_save(self, origin, **kwargs):
        """
        RUS: Термины зависят от модели CustomerModel, валидируем при создании либо валидация вызывается сигналом.
        """
        if origin is None or origin.customer_id != self.customer_id:
            do_validate = kwargs["context"]["validate_customer_category"] = True
        else:
            do_validate = kwargs["context"].get("validate_customer_category", False)
            if not do_validate:
                c_c_c_terms_ids_set = getattr(self, '_clean_customer_categories_terms_ids_set', None)
                do_validate = kwargs["context"]["validate_customer_category"] = (
                    not self.customer_categories_terms_ids_set or
                    c_c_c_terms_ids_set is not None
                )
        return super(CustomerCategoryMixin, self).need_terms_validation_after_save(origin, **kwargs) or do_validate

    def get_customer_category_term(self):
        email_category = get_email_category(self.customer.email)
        return email_category.term if email_category else None

    @cached_property
    def customer_category_term(self):
        return self.get_customer_category_term()

    def validate_terms(self, origin, **kwargs):
        """
        RUS: Добавляет id категории пользователя
        """
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_customer_category", False):
            if origin is not None:
                to_remove_set = self.customer_categories_terms_ids_set
            else:
                to_remove_set = set()
            if to_remove_set:
                self.terms.remove(*to_remove_set)
            if self.customer_category_term:
                self.terms.add(self.customer_category_term.id)
            else:
                to_add_set = getattr(self, '_clean_customer_categories_terms_ids_set', set())
                if len(to_add_set) != 1:
                    to_add_set = {self.get_unknown_customer_term().id}
                self.terms.add(*to_add_set)

        super(CustomerCategoryMixin, self).validate_terms(origin, **kwargs)
