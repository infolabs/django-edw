# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.data_mart import DataMartModel


@shared_task(name='update_data_mart_terms')
def update_data_mart_terms(datamarts_ids, to_set_terms_ids, to_unset_terms_ids):
    does_not_exist = []

    for datamart_id in datamarts_ids:
        try:
            datamart = DataMartModel.objects.get(id=datamart_id)
        except DataMartModel.DoesNotExist:
            does_not_exist.append(datamart_id)
        else:
            datamart.terms.add(*to_set_terms_ids)
            datamart.terms.remove(*to_unset_terms_ids)

    return {
        'datamarts_ids': datamarts_ids,
        'to_set_terms_ids': to_set_terms_ids,
        'to_unset_terms_ids': to_unset_terms_ids,
        'does_not_exist_entities_ids': does_not_exist
    }
