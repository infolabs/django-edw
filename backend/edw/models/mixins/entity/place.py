# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property

from edw.utils.geo import get_location_from_geocoder, get_postcode

from edw.models.postal_zone import get_all_postal_zone_terms_ids, get_postal_zone
from edw.models.entity import EntityModel


class PlaceMixin(object):

    REQUIRED_FIELDS = ('geoposition',)

    def need_terms_validation_after_save(self, origin, **kwargs):
        if origin is None or origin.geoposition != self.geoposition:
            do_validate = kwargs["context"]["validate_place"] = True
        else:
            do_validate = False
        return super(PlaceMixin, self).need_terms_validation_after_save(origin, **kwargs) or do_validate

    def get_location(self):
        return get_location_from_geocoder(geoposition=self.geoposition)

    @cached_property
    def location(self):
        return self.get_location()

    def validate_terms(self, origin, **kwargs):
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_place", False):
            if origin is not None:
                postal_zone_terms_ids = get_all_postal_zone_terms_ids()
                self.terms.remove(*EntityModel.terms.through.objects.filter(
                    entity_id=self.id, term_id__in=postal_zone_terms_ids).values_list('term_id', flat=True))

            zone = get_postal_zone(get_postcode(self.location))
            if zone is not None:
                self.terms.add(zone.term)

        super(PlaceMixin, self).validate_terms(origin, **kwargs)
