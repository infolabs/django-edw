# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel
from edw.models.defaults.mapping import AdditionalEntityCharacteristicOrMark


@shared_task(name='normalize_entities_additional_attrs')
def normalize_entities_additional_attrs(entities_ids, **kwargs):
    does_not_exist_entities_ids = []

    entities = EntityModel.objects.filter(id__in=entities_ids)
    existing_entities_ids = [i.id for i in entities]
    does_not_exist_entities_ids.extend(
        list(
            set(entities_ids) - set(existing_entities_ids)
        )
    )

    for e in entities:
        additional_attrs = AdditionalEntityCharacteristicOrMark.objects.filter(entity__id=e.id)
        if additional_attrs:
            add_terms_ids = []
            delete_attr_ids = []
            # todo: требует исправления. Сейчас удалило доп. х-ку, но термин не установило,
            #  возможно из-за no_external_tagging_restriction. Удалять доп. х-ку можно только если термин установлен.
            for attr in additional_attrs:
                values_terms_map = {x['name']: x['id'] for x in reversed(
                    attr.term.get_descendants(include_self=False).no_external_tagging_restriction().values('id', 'name'))}
                if attr.value in values_terms_map:
                    add_terms_ids.append(values_terms_map[attr.value])
                    delete_attr_ids.append(attr.term.id)
            if add_terms_ids:
                e.terms.add(*add_terms_ids)
            if delete_attr_ids:
                additional_attrs.filter(term__in=delete_attr_ids).delete()

    return {
        'existing_entities_ids': existing_entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids
    }
