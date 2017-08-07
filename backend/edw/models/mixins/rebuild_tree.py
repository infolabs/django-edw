from time import gmtime, mktime
from datetime import timedelta, datetime
from django.utils import timezone


class RebuildTreeMixin(object):

    def rebuild2(self):
        """
        The same as rebuild but keeps current order.
        """
        qs = self._mptt_filter()
        dates = {}
        base_date = timezone.make_aware(
                        datetime.fromtimestamp(
                            mktime(
                                gmtime(0)
                            )
                        ),
                        timezone.get_current_timezone()
                    )
        for item in qs:
            dates[item.pk] = item.created_at
            offset = item.tree_id + item.lft
            lookups = {
                "created_at" : base_date + timedelta(seconds=offset)
            }
            item_qs = self.model._default_manager.filter(pk=item.pk)
            item_qs.update(**lookups)
        e = None
        try:
            super(RebuildTreeMixin, self).rebuild()
        except Exception as e:
            pass
        for item in qs:
            lookups = {
                "created_at" : dates[item.pk]
            }
            item_qs = self.model._default_manager.filter(pk=item.pk)
            item_qs.update(**lookups)
        if e is not None:
            raise e
