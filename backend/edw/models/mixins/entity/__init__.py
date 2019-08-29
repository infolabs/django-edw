# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from edw.models.term import TermModel

_default_system_flags_restriction = (TermModel.system_flags.delete_restriction |
                                     TermModel.system_flags.change_parent_restriction |
                                     TermModel.system_flags.change_slug_restriction |
                                     TermModel.system_flags.change_semantic_rule_restriction |
                                     TermModel.system_flags.has_child_restriction |
                                     TermModel.system_flags.external_tagging_restriction)


ENTITY_CLASS_WRAPPER_TERM_SLUG_PATTERN = "{}_wrapper"


def get_or_create_model_class_wrapper_term(cls):
    """
    RUS: Получает или создает модель класса пользователя model_root_term.
    """
    system_flags = _default_system_flags_restriction
    cls_name_lower = cls.__name__.lower()

    # Get original entity model class term
    original_model_class_term = cls.get_entities_types(from_cache=False)[cls_name_lower]
    original_model_class_term_parent = original_model_class_term.parent

    # Compose new entity model class term slug
    new_model_class_term_slug = ENTITY_CLASS_WRAPPER_TERM_SLUG_PATTERN.format(cls_name_lower)
    if original_model_class_term_parent.slug != new_model_class_term_slug:
        with transaction.atomic():
            try:  # get or create model class root term
                model_root_term = TermModel.objects.get(slug=new_model_class_term_slug,
                                                        parent=original_model_class_term_parent)
            except TermModel.DoesNotExist:
                model_root_term = TermModel(
                    slug=new_model_class_term_slug,
                    parent_id=original_model_class_term_parent.id,
                    name=force_text(cls._meta.verbose_name),
                    semantic_rule=TermModel.AND_RULE,
                    system_flags=system_flags
                )
                model_root_term.save()
        # set original entity model class term to new parent
        original_model_class_term.parent = model_root_term
        original_model_class_term.name = _("Type")
        original_model_class_term.save()
    else:
        model_root_term = original_model_class_term_parent

    return model_root_term
