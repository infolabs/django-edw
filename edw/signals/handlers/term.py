# -*- coding: utf-8 -*-
from edw.signals import make_dispatch_uid
from edw.signals.mptt import move_to_done

from edw.models.term import TermModel


def invalidate_rbrc_after_move(sender, instance, target, position, prev_parent, **kwargs):
    print "*******************************"
    print "* invalidate_rbrc_after_move  *"
    print "*******************************"
    print sender, instance, target, position, prev_parent


move_to_done.connect(invalidate_rbrc_after_move, sender=TermModel.materialized,
                     dispatch_uid=make_dispatch_uid(
                         move_to_done,
                         invalidate_rbrc_after_move,
                         TermModel
                     ))