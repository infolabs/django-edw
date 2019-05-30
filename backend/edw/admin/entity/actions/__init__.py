# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.exceptions import ImproperlyConfigured

try:
    from edw.models.related.entity_image import EntityImageModel
    EntityImageModel() # Test pass if model materialized
except (ImproperlyConfigured, ImportError):
    pass
else:
    from update_images import update_images

from update_terms import update_terms
from update_relations import update_relations
from update_additional_characteristics_or_marks import update_additional_characteristics_or_marks
from update_related_data_marts import update_related_data_marts
from update_states import update_states
from update_active import update_active
from force_validate import force_validate
from make_terms_from_additional_characteristics_or_marks import make_terms_from_additional_characteristics_or_marks
from remove_additional_characteristics_or_marks_with_exists_value_term import remove_additional_characteristics_or_marks_with_exists_value_term
