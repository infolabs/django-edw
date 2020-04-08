# -*- coding: utf-8 -*-

from haystack.backends.elasticsearch_backend import (
    ElasticsearchSearchBackend,
    ElasticsearchSearchEngine,
    DEFAULT_FIELD_MAPPING
)


class RussianElasticsearchBackend(ElasticsearchSearchBackend):
    # Copy-pasted from https://github.com/django-haystack/django-haystack/blob/193b418f0006df6037a2a4a9029ac3060ccd8d89/haystack/backends/elasticsearch_backend.py
    # and added custom Russian analyzer as default

    DEFAULT_SETTINGS = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "default": {
                        "tokenizer":  "standard",
                        "filter": [
                            "lowercase",
                            "russian_stop",
                            "russian_stemmer"
                        ]
                    },
                    "ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["haystack_ngram", "lowercase"],
                    },
                    "edgengram_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["haystack_edgengram", "lowercase"],
                    },
                },
                "tokenizer": {
                    "haystack_ngram_tokenizer": {
                        "type": "nGram",
                        "min_gram": 3,
                        "max_gram": 15,
                    },
                    "haystack_edgengram_tokenizer": {
                        "type": "edgeNGram",
                        "min_gram": 2,
                        "max_gram": 15,
                        "side": "front",
                    },
                },
                "filter": {
                    "haystack_ngram": {
                        "type": "nGram",
                        "min_gram": 3,
                        "max_gram": 15
                    },
                    "haystack_edgengram": {
                        "type": "edgeNGram",
                        "min_gram": 2,
                        "max_gram": 15,
                    },
                    "russian_stop": {
                        "type":       "stop",
                        "stopwords":  "_russian_"
                    },
                    "russian_stemmer": {
                        "type":       "stemmer",
                        "language":   "russian"
                    }
                },
            }
        }
    }

    def build_schema(self, fields):
        """Reset some field analyzers from 'snowball' to 'default' (custom Russian analyzer ↑)."""

        content_field_name, mapping = super(RussianElasticsearchBackend, self).build_schema(fields)

        for field_name, field_mapping in mapping.items():
            if field_name in ['text', 'categories', 'characteristics']:
                field_mapping['analyzer'] = 'default'

        return content_field_name, mapping


class RussianElasticsearchEngine(ElasticsearchSearchEngine):
    """
    Use in settings: `'ENGINE': 'edw.search.engines.RussianElasticsearchEngine',`
    """

    backend = RussianElasticsearchBackend
