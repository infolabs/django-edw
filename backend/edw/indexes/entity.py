#-*- coding: utf-8 -*-

from haystack import indexes


class BaseEntityIndex(indexes.SearchIndex, indexes.Indexable):
    title = indexes.CharField(model_attr='entity_name')
    entity_model = indexes.CharField(model_attr='entity_model')
    text = indexes.NgramField(document=True, use_template=True)