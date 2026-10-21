# -*- coding: utf-8 -*-

from django.dispatch import Signal


external_add_terms = Signal()


external_remove_terms = Signal()


post_save = Signal()


post_add_relations = Signal()
# :param instances: list of instances
# :param rel_id: relation `id`
# :param direction: - relation direction (`f` or `r`, if `f` - `from_entity_id` is identical for all instances)


pre_delete_relations = Signal()
# :param instances: queryset of instances
# :param rel_ids: id's filter (`id` or `slug` list, need normalization).
# If `[]` - delete all relations, else only contained in the list

# Use code pattern `TermModel.normalize_keys(*rel_ids) & TermModel.normalize_keys('my_relation_slug')`
# for detecting target relations in `post_add_relations` and `pre_delete_relations` signals
# Static method TermModel.normalize_keys(*values: Union[int, str]) -> Set[int]
# convert keys *values list (ids & slugs) to relations ids set
