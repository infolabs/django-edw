# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.db.models import Q
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from geoposition import str_to_geoposition
from geoposition.geohash import geo_expand

from edw.models.entity import EntityModel
from edw.models.boundary import get_boundary
from edw.models.postal_zone import get_postal_zone
from edw.models.term import TermModel
from edw.signals.place import zone_changed
from edw.utils.geo import get_location_from_geocoder, get_postcode, GeocoderException

from geopy.exc import GeopyError


class PlaceMixin(object):
    """
    RUS: Определяет поля модели. Добавляет в модели Регион и Другие регионы.
    """

    REQUIRED_FIELDS = ('geoposition',)

    REGION_ROOT_TERM_SLUG = "region"
    TERRA_INCOGNITA_TERM_SLUG = "terra-incognita"

    @classmethod
    def validate_term_model(cls):
        """
        RUS: Добавляет термин Регион и Другие регионы в модель терминов TermModel при их отсутствии.
        """
        # валидируем только один раз
        key = 'vldt:place'
        need_validation = EntityModel._validate_term_model_cache.get(key, True)
        if need_validation:
            EntityModel._validate_term_model_cache[key] = False

            with transaction.atomic():
                try:  # region
                    region = TermModel.objects.get(slug=cls.REGION_ROOT_TERM_SLUG, parent=None)
                except TermModel.DoesNotExist:
                    region = TermModel(
                        slug=cls.REGION_ROOT_TERM_SLUG,
                        parent=None,
                        name=force_text(_('Region')),
                        semantic_rule=TermModel.XOR_RULE,
                        system_flags=(TermModel.system_flags.delete_restriction |
                                      TermModel.system_flags.change_parent_restriction |
                                      TermModel.system_flags.change_slug_restriction))
                    region.save()
            with transaction.atomic():
                try:  # terra-incognita
                    region.get_descendants(include_self=False).get(slug=cls.TERRA_INCOGNITA_TERM_SLUG)
                except TermModel.DoesNotExist:
                    terra_incognita = TermModel(
                        slug=cls.TERRA_INCOGNITA_TERM_SLUG,
                        parent_id=region.id,
                        name=force_text(_('Terra Incognita')),
                        semantic_rule=TermModel.OR_RULE,
                        system_flags=(TermModel.system_flags.delete_restriction |
                                      TermModel.system_flags.change_parent_restriction |
                                      TermModel.system_flags.change_slug_restriction |
                                      TermModel.system_flags.has_child_restriction))
                    terra_incognita.save()
        super(PlaceMixin, cls).validate_term_model()

    @staticmethod
    def get_region_term():
        """
        RUS: Ищет регион в модели TermModel с применением PlaceMixin (слаг = "region").
        Результат кешируется.
        """
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
        """
        RUS: добавляет Другие регионы в модель EntityModel, если они отсутствуют.
        """
        terra_incognita = getattr(EntityModel, "_terra_incognita_cache", None)
        if terra_incognita is None:
            region = PlaceMixin.get_region_term()
            if region is not None:
                try:
                    terra_incognita = region.get_descendants(include_self=False).get(
                        slug=PlaceMixin.TERRA_INCOGNITA_TERM_SLUG)
                except TermModel.DoesNotExist:
                    # может вернуть None
                    pass
                else:
                    EntityModel._terra_incognita_cache = terra_incognita
        return terra_incognita

    @classmethod
    def get_all_regions_terms_ids_set(cls):
        """
        RUS: Добавляет список ids регионов, если есть термин Регион в модели.
        """
        region = PlaceMixin.get_region_term()
        if region is not None:
            ids = region.get_descendants(include_self=True).values_list('id', flat=True)
        else:
            ids = []
        return set(ids)

    @cached_property
    def all_regions_terms_ids_set(self):
        """
        RUS: Кэширует список ids регионов.
        """
        return self.get_all_regions_terms_ids_set()

    def need_terms_validation_after_save(self, origin, **kwargs):
        """
        RUS: Проставляет автоматически термины, связанные с местоположением объекта,
        после сохранения его геопозиции.
        """
        if (origin is None or origin.geoposition != self.geoposition) and self.geoposition:
            do_validate = kwargs["context"]["validate_place"] = True
        else:
            do_validate = False
        return super(PlaceMixin, self).need_terms_validation_after_save(origin, **kwargs) or do_validate

    def get_location(self):
        """
        RUS: Определяет местоположение объекта.
        """
        return get_location_from_geocoder(geoposition=self.geoposition)

    @cached_property
    def location(self):
        """
        RUS: Кэширует местоположение объекта.
        """
        return self.get_location()

    def validate_terms(self, origin, **kwargs):
        """
        RUS: Добавляет id почтовой зоны в случае определения местположения,
        если местоположение не определяется, то id добавляется в другие регионы.
        """
        context = kwargs["context"]
        if context.get("force_validate_terms", False) or context.get("validate_place", False):
            if origin is not None:
                to_remove = EntityModel.terms.through.objects.filter(
                    Q(entity_id=self.id) &
                    Q(term_id__in=self.all_regions_terms_ids_set)
                ).values_list('term_id', flat=True)
            else:
                to_remove = []

            # определяем термин зоны по границам
            zone = get_boundary(self.geoposition.longitude, self.geoposition.latitude) if self.geoposition else None

            # Уточняем зону если не удалось определить по границам, либо возможно найти более частную зону,
            # нельзя использовать в массовых операциях из ограничения API геокодера
            if not context.get("bulk_force_validate_terms", False):
                if zone is None or not zone.term.is_leaf_node():
                    try:
                        # определяем термин зоны по почтовому индексу
                        postcode = get_postcode(self.location)
                    except (GeocoderException, GeopyError):
                        pass
                    else:
                        post_zone = get_postal_zone(postcode)
                        level_attr = TermModel._mptt_meta.level_attr
                        if post_zone is not None and (
                                zone is None or getattr(zone.term, level_attr) < getattr(post_zone.term, level_attr)):
                            zone = post_zone
                if zone is None:
                    # если зона не найдена ни по почтовому индексу ни по границе - устанавливаем "Terra Incognita"
                    to_add = [self.get_terra_incognita_term().id]
                else:
                    to_add = [zone.term.id]
            else:
                # если зона определенная границей не найдена или менее частная - оставляем старые термины
                if zone is None or zone.term.get_descendants().filter(id__in=to_remove).exists():
                    to_add = to_remove
                else:
                    to_add = [zone.term.id]

            if set(to_add) != set(to_remove):
                self.terms.remove(*to_remove)
                self.terms.add(*to_add)
                zone_changed.send(sender=self.__class__, instance=self,
                                  zone_term_ids_to_remove=to_remove,
                                  zone_term_ids_to_add=to_add)

        super(PlaceMixin, self).validate_terms(origin, **kwargs)

    @classmethod
    def _get_search_query(cls, query, geoposition):
        """
        Example:
        query = {
            'like': "request.GET.get('q', '')",
            'unlike': "request.GET.get('u', None)",
            'ignore_like': "request.GET.get('iq', None)",
            'ignore_unlike': "request.GET.get('iu', None)"
        }
        """
        geohash = geoposition.geohash.strip()
        text_parts = [query['like']]
        for i in [6, 7, 8, 9]:
            hash_parts = geo_expand(geohash[:i])
            text_parts.extend(hash_parts)

        query['like'] = ' '.join(text_parts)
        return query

    @classmethod
    def get_search_query(cls, request):
        """
        Формируем поисковый запрос из объета Request
        """
        query = super(PlaceMixin, cls).get_search_query(request)
        g = request.GET.get('g', None)
        if g is not None:
            try:
                geoposition = str_to_geoposition(g)
            except ValueError:
                pass
            else:
                query = cls._get_search_query(query, geoposition)
        return query
