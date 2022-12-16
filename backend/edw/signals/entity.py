# -*- coding: utf-8 -*-

from django.dispatch import Signal


external_add_terms = Signal(providing_args=["instance", "pk_set"])


external_remove_terms = Signal(providing_args=["instance", "pk_set"])


post_save = Signal(providing_args=["instance", "origin"])


post_add_relations = Signal(providing_args=["instances", "rel_id", "direction"])
# :param instances: list of instances
# :param rel_id: relation `id`
# :param direction: - relation direction (`f` or `r`, if `f` - `from_entity_id` is identical for all instances)


pre_delete_relations = Signal(providing_args=["instances", "rel_ids"])
# :param instances: queryset of instances
# :param rel_ids: id's filter (`id` or `slug` list, need normalization).
# If `[]` - delete all relations, else only contained in the list

# Use code pattern `TermModel.normalize_keys(*rel_ids) & TermModel.normalize_keys('my_relation_slug')`
# for detecting target relations in `post_add_relations` and `pre_delete_relations` signals
# Static method TermModel.normalize_keys(*values: Union[int, str]) -> Set[int]
# convert keys *values list (ids & slugs) to relations ids set
