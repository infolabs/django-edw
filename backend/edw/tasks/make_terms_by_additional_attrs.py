# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pytils.translit import slugify
from celery import shared_task

from edw.models.entity import EntityModel
from edw.models.term import TermModel
from edw.models.defaults.mapping import AdditionalEntityCharacteristicOrMark


@shared_task(name='entities_make_terms_by_additional_attrs')
def entities_make_terms_by_additional_attrs(entities_ids, **kwargs):
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
                values_terms_map = {x['name']: x['id'] for x in reversed(
                    characteristic_or_mark.term.get_descendants(include_self=False).values('id', 'name'))}
                if not characteristic_or_mark.value in values_terms_map:
                    try:
                        TermModel.objects.create(
                            name=characteristic_or_mark.value,
                            slug=slugify(characteristic_or_mark.value),
                            parent=characteristic_or_mark.term
                        )
                    except Exception as e:
                        # todo: сделать нормальнй эксепшн
                        print(e)

    return {
        'existing_entities_ids': existing_entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids
    }
