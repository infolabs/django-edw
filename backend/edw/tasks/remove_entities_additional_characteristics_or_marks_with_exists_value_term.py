# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel
from edw.models.defaults.mapping import AdditionalEntityCharacteristicOrMark


@shared_task(name='remove_entities_additional_characteristics_or_marks_with_exists_value_term')
def remove_entities_additional_characteristics_or_marks_with_exists_value_term(entities_ids):
    does_not_exist_entities_ids = []

    entities = EntityModel.objects.filter(id__in=entities_ids)
    existing_entities_ids = [i.id for i in entities]
    does_not_exist_entities_ids.extend(
        list(
            set(entities_ids) - set(existing_entities_ids)
        )
    )

    for e in entities:
        additional_characteristics_or_marks = AdditionalEntityCharacteristicOrMark.objects.filter(entity__id=e.id)
        if additional_characteristics_or_marks:
            for characteristic_or_mark in additional_characteristics_or_marks:
                values_terms_map = {x['id']: x['name'] for x in reversed(
                    characteristic_or_mark.term.get_descendants(include_self=False).values('id', 'name'))}

                entity_attr_values_not_terms_ids = list(
                    set(values_terms_map.keys()) - set(e.terms.values_list('id', flat=True))
                )
                for term_id in entity_attr_values_not_terms_ids:
                    del values_terms_map[term_id]

                if characteristic_or_mark.value in values_terms_map.values():
                    characteristic_or_mark.delete()

    return {
        'entities_ids': entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids
    }
