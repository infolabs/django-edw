# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from celery import shared_task

from edw.models.entity import EntityModel


@shared_task(name='update_entities_states')
def update_entities_states(entities_ids, state):
    does_not_exist_entities_ids = []
    does_not_fsm_instances_entities_ids = []
    does_not_have_available_transitions_entities_ids = []

    for entity_id in entities_ids:
        try:
            entity = EntityModel.objects.get(id=entity_id)
        except EntityModel.DoesNotExist:
            does_not_exist_entities_ids.append(entity_id)
        else:
            if hasattr(entity, 'TRANSITION_TARGETS'):
                for transition in entity.get_available_status_transitions():
                    allowed_states = getattr(transition.target, 'allowed_states', [transition.target,])
                    if state in allowed_states:
                        getattr(entity, transition.name)()
                        entity.save()
                        break
                else:
                    does_not_have_available_transitions_entities_ids.append(entity_id)
            else:
                does_not_fsm_instances_entities_ids.append(entity_id)

    return {
        'entities_ids': entities_ids,
        'state': state,
        'does_not_fsm_instances_entities_ids': does_not_fsm_instances_entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
        'does_not_have_available_transitions_entities_ids': does_not_have_available_transitions_entities_ids
    }
