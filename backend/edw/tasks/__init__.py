# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.exceptions import ImproperlyConfigured

try:
    from edw.models.related.entity_image import EntityImageModel
    EntityImageModel() # Test pass if model materialized
except (ImproperlyConfigured, ImportError):
    pass
else:
    from update_images import update_entities_images

from update_terms import update_entities_terms
from update_relations import update_entities_relations
from update_related_data_marts import update_entities_related_data_marts
from update_additional_characteristics_or_marks import update_entities_additional_characteristics_or_marks
from update_states import update_entities_states
from update_active import update_entities_active
from force_validate import entities_force_validate
from update_terms_parent import update_terms_parent
from make_terms_by_additional_attrs import entities_make_terms_by_additional_attrs
from normalize_entities_additional_attrs import normalize_entities_additional_attrs
