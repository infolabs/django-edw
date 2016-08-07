# -*- coding: utf-8 -*-

from django.dispatch import Signal


move_to_done = Signal(providing_args=["instance", "target", "position"])


class MPTTModelSignalSenderMixin(object):

    def move_to(self, target, position='first-child'):
        prev_parent = self.parent
        super(MPTTModelSignalSenderMixin, self).move_to(target, position)

        print "++ Sender ++", self.__class__, self._materialized_model

        move_to_done.send(sender=self.__class__, instance=self, target=target, position=position,
                          prev_parent=prev_parent)

