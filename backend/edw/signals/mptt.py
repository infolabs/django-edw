# -*- coding: utf-8 -*-

from django.dispatch import Signal


move_to_done = Signal()

pre_save = Signal()

post_save = Signal()


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

