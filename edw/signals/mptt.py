# -*- coding: utf-8 -*-

from django.dispatch import Signal


move_to_done = Signal(providing_args=["instance", "target", "position"])

pre_save = Signal(providing_args=["instance"])

post_save = Signal(providing_args=["instance"])


class MPTTModelSignalSenderMixin(object):

    def move_to(self, target, position='first-child'):
        prev_parent = self.parent
        super(MPTTModelSignalSenderMixin, self).move_to(target, position)
        move_to_done.send(sender=self.__class__, instance=self, target=target, position=position,
                          prev_parent=prev_parent)

    def save(self, *args, **kwargs):
        pre_save.send(sender=self.__class__, instance=self)
        result = super(MPTTModelSignalSenderMixin, self).save(*args, **kwargs)
        post_save.send(sender=self.__class__, instance=self)
        return result

