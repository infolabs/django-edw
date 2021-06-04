# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.utils.encoding import force_text
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from edw.models.mixins.entity import get_or_create_model_class_wrapper_term, ENTITY_CLASS_WRAPPER_TERM_SLUG_PATTERN
from edw.models.term import TermModel

_default_system_flags_restriction = (TermModel.system_flags.delete_restriction |
                                     TermModel.system_flags.change_parent_restriction |
                                     TermModel.system_flags.change_slug_restriction |
                                     TermModel.system_flags.change_semantic_rule_restriction |
                                     TermModel.system_flags.has_child_restriction |
                                     TermModel.system_flags.external_tagging_restriction)


class FSMMixin(object):
    """
    RUS: Добавляет Состояние в модель, автоматически обновляет Состояние при изменении статуса.
    """

    REQUIRED_FIELDS = ('status',)

    STATE_ROOT_TERM_SLUG = "state"

    '''
    Example:
    TRANSITION_TARGETS = {
        'new': "Default state",
        ...
    }
    '''
    TRANSITION_TARGETS = {}

    @classmethod
    def get_transition_name(cls, target):
        """
        ENG: Return the human readable name for a given transition target.
        RUS: Возвращает удобочитаемое имя для данного целевого объекта перехода.
        """
        return target

    def state_name(self):
        """
        RUS: Возбуждает исключение, когда абстрактные методы класса требуют переопределения в дочерних классах.
        """
        raise NotImplementedError(
            '{cls}.state_name must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    @classmethod
    def get_states(cls):
        """
        RUS: Добавляет термин Состояние в модель fsm_model при его отсутствии.
        """
        fsm_model = cls._meta.get_field('status').model
        cache_key = "_{cls}_states_cache".format(cls=fsm_model)
        states = getattr(fsm_model, cache_key, None)
        if states is None:
            model_class_term_slug = ENTITY_CLASS_WRAPPER_TERM_SLUG_PATTERN.format(fsm_model.__name__.lower())
            states = {}
            try:
                root = TermModel.objects.get(
                    slug=fsm_model.STATE_ROOT_TERM_SLUG,
                    parent__slug=model_class_term_slug
                )
                for term in root.get_descendants(include_self=False):
                    states[term.slug] = term
            except TermModel.DoesNotExist:
                pass
            setattr(fsm_model, cache_key, states)
        return states

    @classmethod
    def validate_term_model(cls):
        """
        RUS: Добавляет Состояние родителя и объекта в модель TermModel при их отсутствии и сохраняет их.
        """
        super(FSMMixin, cls).validate_term_model()

        if not cls._meta.abstract and cls._meta.get_field('status').model == cls:
            system_flags = _default_system_flags_restriction

            model_root_term = get_or_create_model_class_wrapper_term(cls)
            with transaction.atomic():
                try:
                    states_parent_term = TermModel.objects.get(slug=cls.STATE_ROOT_TERM_SLUG, parent=model_root_term)
                except TermModel.DoesNotExist:
                    states_parent_term = TermModel(
                        slug=cls.STATE_ROOT_TERM_SLUG,
                        parent_id=model_root_term.id,
                        name=force_text(cls._meta.get_field('status').verbose_name),
                        semantic_rule=TermModel.XOR_RULE,
                        system_flags=system_flags
                    )
                    states_parent_term.save()
            transition_states = cls.TRANSITION_TARGETS
            for state_key, state_name in transition_states.items():
                with transaction.atomic():
                    try:
                        states_parent_term.get_descendants(include_self=False).get(slug=state_key)
                    except TermModel.DoesNotExist:
                        state = TermModel(
                            slug=state_key,
                            parent_id=states_parent_term.id,
                            name=force_text(state_name),
                            semantic_rule=TermModel.OR_RULE,
                            system_flags=system_flags
                        )
                        state.save()

    def need_terms_validation_after_save(self, origin, **kwargs):
        """
        RUS: Автоматически проставляет Состояние в терминах после сохранения объекта.
        """
        if origin is None or origin.status != self.status:
            do_validate = kwargs["context"]["validate_entity_state"] = True
        else:
            do_validate = False
        return super(FSMMixin, self).need_terms_validation_after_save(
            origin, **kwargs) or do_validate

    def validate_terms(self, origin, **kwargs):
        """
        RUS: Обновляет Состояние объекта при его изменении.
        """
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_entity_state", False):
            states = self.get_states()
            # remove old state term
            self.terms.remove(*[term.id for term in states.values()])
            # add new state term
            new_state = states[self.status]
            self.terms.add(new_state)
        super(FSMMixin, self).validate_terms(origin, **kwargs)

    def do_transition(self, transition_name, request=None):
        raise NotImplementedError(
            '{cls}.do_transition must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )


class FSMTransitionAndLoggingMixin(FSMMixin):
    def state_name(self):
        """
        RUS: Возбуждает исключение, когда абстрактные методы класса требуют переопределения в дочерних классах.
        """
        raise NotImplementedError(
            '{cls}.state_name must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    def log_entity_transition(self, transition_name, user_id):
        old_state, new_state = transition_name.split('_to_')

        LogEntry.objects.log_action(
            user_id=user_id,
            content_type_id=ContentType.objects.get_for_model(self).pk,
            object_id=self.pk,
            object_repr=force_text(self),
            change_message=_('Change status from "%(old_status)s" to "%(new_status)s"') %
                           {
                               'old_status': self.TRANSITION_TARGETS[old_state],
                               'new_status': self.TRANSITION_TARGETS[new_state],
                           },
            action_flag=CHANGE,
        )

    def do_transition(self, transition_name, request=None):
        trans_func = getattr(self, transition_name)
        if request:
            user_id = request.user.pk
            self.log_entity_transition(transition_name, user_id)
        return trans_func()
