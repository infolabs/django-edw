# -*- coding: utf-8 -*-
from edw.models.mixins import ModelMixin
from edw.models.term import TermModel


class PrivatePersonMixin(ModelMixin):
    """
    `Миксин для работы с частной персоной
    """

    def set_private_person_terms_by_place_and_entity(self):
        terms_to_set = (
                set(self.get_common_terms_ids())
                - set(self.get_uncommon_terms_ids())
                - set(self.get_region_terms_ids())
        )

        current_region_terms_ids = self.private_person.get_region_terms_ids()
        has_valid_region_terms = TermModel.objects.filter(
            id__in=current_region_terms_ids
        ).exclude(
            slug__in=["other-regions", "terra-incognita"]
        ).exists()

        if not has_valid_region_terms:
            # Получаем региональные термины места
            place_common_terms_ids = self.place.get_nearest_known_common_terms_ids()
            place_uncommon_terms_ids = self.place.get_uncommon_terms_ids()
            region_terms_to_set = list(
                set(place_common_terms_ids) - set(place_uncommon_terms_ids)
            )

            # Удаляем старые региональные термины
            old_region_terms = list(
                self.place.all_regions_terms_ids_set & set(current_region_terms_ids)
            )
            self.private_person.terms.remove(*old_region_terms)

            # Добавляем новые региональные термины
            terms_to_set.update(region_terms_to_set)

        if terms_to_set:
            self.private_person.terms.add(*terms_to_set)

        return terms_to_set


