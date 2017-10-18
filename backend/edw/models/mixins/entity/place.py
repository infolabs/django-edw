# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from edw.models.postal_zone import get_all_post_zone, get_postal_zone


class PlaceMixin(object):

    def PlaceMixin(self):
        return True

    def need_terms_validation_after_save(self, origin, **kwargs):
        if origin is None or origin.geoposition != self.geoposition:
            do_validate = kwargs["context"]["validate_place"] = True
        else:
            do_validate = False
        return super(PlaceMixin, self).need_terms_validation_after_save(
            origin, **kwargs) or do_validate

    def validate_terms(self, origin, **kwargs):
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_place", False):
            if origin is not None:
                for zone in get_all_post_zone():
                    if zone is not None:
                        self.terms.remove(zone.term)
            zone = get_postal_zone(self.postcode())
            if zone is not None:
                self.terms.add(zone.term)
        super(PlaceMixin, self).validate_terms(origin, **kwargs)