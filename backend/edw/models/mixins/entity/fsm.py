# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from edw.models.term import TermModel


class FSMMixin(object):

    @classmethod
    def get_transition_name(cls, target):
        """Return the human readable name for a given transition target"""
        return target

    def state_name(self):
        raise NotImplementedError(
            '{cls}.state_name must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    @classmethod
    def validate_term_model(cls):
        super(FSMMixin, cls).validate_term_model()
        system_flags = (
            TermModel.system_flags.delete_restriction |
            TermModel.system_flags.change_parent_restriction |
            TermModel.system_flags.change_slug_restriction |
            TermModel.system_flags.change_semantic_rule_restriction |
            TermModel.system_flags.has_child_restriction |
            TermModel.system_flags.external_tagging_restriction
        )

        # Get original entity model class term
        original_model_class_term = cls.get_entities_types()[cls.__name__.lower()]
        original_model_class_term_parent = original_model_class_term.parent

        # Compose new entity model class term slug
        new_model_class_term_slug = "{}_wrapper".format(cls.__name__.lower())
        if original_model_class_term_parent.slug != new_model_class_term_slug:
            try:  # get or create model class root term
                model_root_term = TermModel.objects.get(slug=new_model_class_term_slug,
                                                        parent=original_model_class_term_parent)
            except TermModel.DoesNotExist:
                model_root_term = TermModel(
                    slug=new_model_class_term_slug,
                    parent=original_model_class_term_parent,
                    name=cls._meta.verbose_name,
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
        try:
            states_parent_term = TermModel.objects.get(slug=cls.STATE_ROOT_TERM_SLUG, parent=model_root_term)
        except TermModel.DoesNotExist:
            states_parent_term = TermModel(
                slug=cls.STATE_ROOT_TERM_SLUG,
                parent=model_root_term,
                name=_('State'),
                semantic_rule=TermModel.XOR_RULE,
                system_flags=system_flags
            )
            states_parent_term.save()
        transition_states = cls.TRANSITION_TARGETS
        for state_key in transition_states.keys():
            try:
                state = TermModel.objects.get(slug=state_key, parent=states_parent_term)
            except TermModel.DoesNotExist:
                state = TermModel(
                    slug=state_key,
                    parent=states_parent_term,
                    name=transition_states[state_key],
                    semantic_rule=TermModel.OR_RULE,
                    system_flags=system_flags
                )
            state.save()

    def need_terms_validation_after_save(self, origin, **kwargs):
        if origin is None or origin.status != self.status:
            do_validate = kwargs["context"]["validate_entity_state"] = True
        else:
            do_validate = False
        return super(FSMMixin, self).need_terms_validation_after_save(
            origin, **kwargs) or do_validate

    def validate_terms(self, origin, **kwargs):
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_entity_state", False):
            states = self.get_states()
            # remove old state term
            origin_state = states[origin.status]
            self.terms.remove(origin_state)
            # add new state term
            new_state = states[self.status]
            self.terms.add(new_state)
        super(FSMMixin, self).validate_terms(origin, **kwargs)