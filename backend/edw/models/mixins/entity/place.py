# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from edw.signals.place import zone_changed
from edw.utils.geo import get_location_from_geocoder, get_postcode, GeocoderException

from edw.models.postal_zone import get_all_postal_zone_terms_ids, get_postal_zone
from edw.models.term import TermModel
from edw.models.entity import EntityModel


class PlaceMixin(object):

    REQUIRED_FIELDS = ('geoposition',)

    REGION_ROOT_TERM_SLUG = "region"
    TERRA_INCOGNITA_TERM_SLUG = "terra-incognita"

    @classmethod
    def validate_term_model(cls):
        try: # region
            region = TermModel.objects.get(slug=cls.REGION_ROOT_TERM_SLUG, parent=None)
        except TermModel.DoesNotExist:
            region = TermModel(
                slug=cls.REGION_ROOT_TERM_SLUG,
                parent=None,
                name=_('Region'),
                semantic_rule=TermModel.XOR_RULE,
                system_flags=(TermModel.system_flags.delete_restriction |
                              TermModel.system_flags.change_parent_restriction |
                              TermModel.system_flags.change_slug_restriction))
            region.save()
        try: # terra-incognita
            region.get_descendants(include_self=False).get(slug=cls.TERRA_INCOGNITA_TERM_SLUG)
        except TermModel.DoesNotExist:
            terra_incognita = TermModel(
                slug=cls.TERRA_INCOGNITA_TERM_SLUG,
                parent_id=region.id,
                name=_('Terra Incognita'),
                semantic_rule=TermModel.OR_RULE,
                system_flags=(TermModel.system_flags.delete_restriction |
                              TermModel.system_flags.change_parent_restriction |
                              TermModel.system_flags.change_slug_restriction |
                              TermModel.system_flags.has_child_restriction))
            terra_incognita.save()
        super(PlaceMixin, cls).validate_term_model()

    @staticmethod
    def get_region_term():
        region = getattr(EntityModel, "_region_term_cache", None)
        if region is None:
            try:
                region = TermModel.objects.get(slug=PlaceMixin.REGION_ROOT_TERM_SLUG, parent=None)
            except TermModel.DoesNotExist:
                pass
            else:
                EntityModel._region_term_cache = region
        return region

    @staticmethod
    def get_terra_incognita_term():
        terra_incognita = getattr(EntityModel, "_terra_incognita_cache", None)
        if terra_incognita is None:
            region = PlaceMixin.get_region_term()
            if region is not None:
                try:
                    terra_incognita = region.get_descendants(include_self=False).get(
                        slug=PlaceMixin.TERRA_INCOGNITA_TERM_SLUG)
                except TermModel.DoesNotExist:
                    pass
                else:
                    EntityModel._terra_incognita_cache = terra_incognita
        return terra_incognita

    def need_terms_validation_after_save(self, origin, **kwargs):
        if (origin is None or origin.geoposition != self.geoposition) and self.geoposition:
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
        if (context.get("force_validate_terms", False) and not context.get("bulk_force_validate_terms", False)
        ) or context.get("validate_place", False):
            # нельзя использовать в массовых операциях из ограничения API геокодера
            terra_incognita = self.get_terra_incognita_term()
            if origin is not None:
                postal_zone_terms_ids = get_all_postal_zone_terms_ids()
                to_remove = EntityModel.terms.through.objects.filter(
                    Q(entity_id=self.id) &
                    (Q(term_id__in=postal_zone_terms_ids) | Q(term_id=terra_incognita.id))
                ).values_list('term_id', flat=True)
                self.terms.remove(*to_remove)
            else:
                to_remove = []

            try:
                postcode = get_postcode(self.location)
            except GeocoderException:
                zone = None
            else:
                zone = get_postal_zone(postcode)

            if zone is not None:
                to_add = [zone.term.id]
            else:
                to_add = [terra_incognita.id]
            self.terms.add(*to_add)

            if set(to_add) != set(to_remove):
                zone_changed.send(sender=self.__class__, instance=self,
                                  zone_term_ids_to_remove=to_remove,
                                  zone_term_ids_to_add=to_add)

        super(PlaceMixin, self).validate_terms(origin, **kwargs)
