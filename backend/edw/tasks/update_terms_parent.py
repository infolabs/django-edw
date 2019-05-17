# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from celery import shared_task

from edw.models.term import TermModel


@shared_task(name='update_terms_parent')
def update_terms_parent(terms_ids, to_set_parent_term_id):
    does_not_exist = []

    if to_set_parent_term_id is not None:
        try:
            to_set_parent_term = TermModel.objects.get(id=to_set_parent_term_id)
        except TermModel.DoesNotExist:
            pass
        else:

            for term_id in terms_ids:
                try:
                    term = TermModel.objects.get(id=term_id)
                except TermModel.DoesNotExist:
                    does_not_exist.append(term_id)
                else:
                    term.parent = to_set_parent_term
                    term.save()

    return {
        'terms_ids': terms_ids,
        'to_set_parent_term_id': to_set_parent_term_id,
        'does_not_exist_term_ids': does_not_exist
    }