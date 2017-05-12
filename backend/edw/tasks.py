# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task


@shared_task
def update_entities_terms(entities_ids, to_set_terms_ids, to_unset_terms_ids):


    return {
        'entities_ids': entities_ids,
        'to_set_terms_ids': to_set_terms_ids,
        'to_unset_terms_ids': to_unset_terms_ids
    }