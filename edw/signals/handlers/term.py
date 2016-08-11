# -*- coding: utf-8 -*-
from django.db.models.signals import (
    pre_delete,
)

from edw.signals import make_dispatch_uid
from edw.signals.mptt import (
    move_to_done,
    pre_save,
    post_save
)

from edw.models.term import TermModel


#==============================================================================
# Term model event handlers
#==============================================================================

def invalidate_term_before_save(sender, instance, **kwargs):
    print "*******************************"
    print "* invalidate_term_before_save *"
    print "*******************************"
    print sender, instance


def invalidate_term_after_save(sender, instance, **kwargs):
    print "*******************************"
    print "* invalidate_term_after_save  *"
    print "*******************************"
    print sender, instance

    # Clear decompress buffer
    TermModel.clear_decompress_buffer()


def invalidate_term_after_move(sender, instance, target, position, prev_parent, **kwargs):
    print "*******************************"
    print "* invalidate_term_after_move  *"
    print "*******************************"
    print sender, instance, target, position, prev_parent

    invalidate_term_after_save(sender, instance, **kwargs)


pre_save.connect(invalidate_term_before_save, sender=TermModel.materialized,
                 dispatch_uid=make_dispatch_uid(
                     pre_save,
                     invalidate_term_before_save,
                     TermModel
                 ))
post_save.connect(invalidate_term_after_save, sender=TermModel.materialized,
                  dispatch_uid=make_dispatch_uid(
                      post_save,
                      invalidate_term_after_save,
                      TermModel
                  ))
pre_delete.connect(invalidate_term_after_save, sender=TermModel.materialized,
                   dispatch_uid=make_dispatch_uid(
                       pre_delete,
                       invalidate_term_after_save,
                       TermModel
                   ))
move_to_done.connect(invalidate_term_after_move, sender=TermModel.materialized,
                     dispatch_uid=make_dispatch_uid(
                         move_to_done,
                         invalidate_term_after_move,
                         TermModel
                     ))
