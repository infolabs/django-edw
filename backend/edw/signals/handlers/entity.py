# -*- coding: utf-8 -*-
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from edw.signals import make_dispatch_uid

from edw.models.term import TermModel
from edw.models.entity import EntityModel


#==============================================================================
# Entity model event handlers
#==============================================================================
Model = EntityModel.terms.through
@receiver(m2m_changed, sender=Model, dispatch_uid=make_dispatch_uid(
    m2m_changed, 'invalidate_after_terms_set_changed', Model))
def invalidate_after_terms_set_changed(sender, instance, **kwargs):

    print "*** invalidate_after_terms_set_changed ***", sender, instance, kwargs

    if getattr(instance, "_during_terms_validation", False):
        return
    pk_set = kwargs.pop('pk_set', None)
    action = kwargs.pop('action', None)

    if action == "pre_add":
        # normalize terms set
        origin_pk_set = set(instance.terms.values_list('id', flat=True))
        tree = TermModel.decompress(origin_pk_set | pk_set, fix_it=True)
        normal_pk_set = set([x.term.id for x in tree.values() if x.is_leaf])
        # pk set to add
        pk_set_difference = normal_pk_set - origin_pk_set
        pk_set.clear()
        pk_set.update(pk_set_difference)
        # pk set to remove
        pk_set_difference = origin_pk_set - normal_pk_set
        if pk_set_difference:
            instance._during_terms_validation = True
            instance.terms.remove(*list(pk_set_difference))
            del instance._during_terms_validation
