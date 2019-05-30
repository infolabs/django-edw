# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel
from edw.models.defaults.mapping import AdditionalEntityCharacteristicOrMark


@shared_task(name='normalize_entities_additional_attrs')
def normalize_entities_additional_attrs(entities_ids):
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
            add_terms_ids = []
            for characteristic_or_mark in additional_characteristics_or_marks:
                values_terms_map = {x['name']: x['id'] for x in reversed(
                    characteristic_or_mark.term.get_descendants(include_self=False).values('id', 'name'))}
                if characteristic_or_mark.value in values_terms_map:
                    add_terms_ids.append(values_terms_map[characteristic_or_mark.value])
                    characteristic_or_mark.delete()
            if add_terms_ids:
                e.terms.add(*add_terms_ids)

    return {
        'entities_ids': entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids
    }
