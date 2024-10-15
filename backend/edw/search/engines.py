# -*- coding: utf-8 -*-
import haystack
import warnings

from haystack.utils import get_model_ct
from haystack.backends.elasticsearch5_backend import (
    Elasticsearch5SearchBackend,
    Elasticsearch5SearchEngine
)
from haystack.constants import DEFAULT_OPERATOR, FUZZINESS, DOCUMENT_FIELD, DJANGO_CT

# todo: move this class to 'nash-region'
class RussianElasticsearchBackend(Elasticsearch5SearchBackend):
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
            if field_name in [DOCUMENT_FIELD]:
                field_mapping['analyzer'] = 'default'

        return content_field_name, mapping

    # bugfix: https://github.com/django-haystack/django-haystack/issues/1622
    def build_search_kwargs(
        self,
        query_string,
        sort_by=None,
        start_offset=0,
        end_offset=None,
        fields="",
        highlight=False,
        facets=None,
        date_facets=None,
        query_facets=None,
        narrow_queries=None,
        spelling_query=None,
        within=None,
        dwithin=None,
        distance_point=None,
        models=None,
        limit_to_registered_models=None,
        result_class=None,
        **extra_kwargs
    ):
        index = haystack.connections[self.connection_alias].get_unified_index()
        content_field = index.document_field

        if query_string == "*:*":
            kwargs = {"query": {"match_all": {}}}
        else:
            kwargs = {
                "query": {
                    "query_string": {
                        "default_field": content_field,
                        "default_operator": DEFAULT_OPERATOR,
                        "query": query_string,
                        "analyze_wildcard": True,
                        "auto_generate_phrase_queries": True,
                        "fuzziness": FUZZINESS,
                    }
                }
            }

        filters = []

        if fields:
            if isinstance(fields, (list, set)):
                fields = " ".join(fields)

            kwargs["stored_fields"] = fields

        if sort_by is not None:
            order_list = []
            for field, direction in sort_by:
                if field == "distance" and distance_point:
                    # Do the geo-enabled sort.
                    lng, lat = distance_point["point"].coords
                    sort_kwargs = {
                        "_geo_distance": {
                            distance_point["field"]: [lng, lat],
                            "order": direction,
                            "unit": "km",
                        }
                    }
                else:
                    if field == "distance":
                        warnings.warn(
                            "In order to sort by distance, you must call the '.distance(...)' method."
                        )

                    # Regular sorting.
                    sort_kwargs = {field: {"order": direction}}

                order_list.append(sort_kwargs)

            kwargs["sort"] = order_list

        # From/size offsets don't seem to work right in Elasticsearch's DSL. :/
        # if start_offset is not None:
        #     kwargs['from'] = start_offset

        # if end_offset is not None:
        #     kwargs['size'] = end_offset - start_offset

        if highlight:
            # `highlight` can either be True or a dictionary containing custom parameters
            # which will be passed to the backend and may override our default settings:

            kwargs["highlight"] = {"fields": {content_field: {}}}

            if isinstance(highlight, dict):
                kwargs["highlight"].update(highlight)

        if self.include_spelling:
            kwargs["suggest"] = {
                "suggest": {
                    "text": spelling_query or query_string,
                    "term": {
                        # Using content_field here will result in suggestions of stemmed words.
                        "field": "_all"
                    },
                }
            }

        if narrow_queries is None:
            narrow_queries = set()

        if facets is not None:
            kwargs.setdefault("aggs", {})

            for facet_fieldname, extra_options in facets.items():
                facet_options = {
                    "meta": {"_type": "terms"},
                    "terms": {"field": index.get_facet_fieldname(facet_fieldname)},
                }
                if "order" in extra_options:
                    facet_options["meta"]["order"] = extra_options.pop("order")
                # Special cases for options applied at the facet level (not the terms level).
                if extra_options.pop("global_scope", False):
                    # Renamed "global_scope" since "global" is a python keyword.
                    facet_options["global"] = True
                if "facet_filter" in extra_options:
                    facet_options["facet_filter"] = extra_options.pop("facet_filter")
                facet_options["terms"].update(extra_options)
                kwargs["aggs"][facet_fieldname] = facet_options

        if date_facets is not None:
            kwargs.setdefault("aggs", {})

            for facet_fieldname, value in date_facets.items():
                # Need to detect on gap_by & only add amount if it's more than one.
                interval = value.get("gap_by").lower()

                # Need to detect on amount (can't be applied on months or years).
                if value.get("gap_amount", 1) != 1 and interval not in (
                    "month",
                    "year",
                ):
                    # Just the first character is valid for use.
                    interval = "%s%s" % (value["gap_amount"], interval[:1])

                kwargs["aggs"][facet_fieldname] = {
                    "meta": {"_type": "date_histogram"},
                    "date_histogram": {"field": facet_fieldname, "interval": interval},
                    "aggs": {
                        facet_fieldname: {
                            "date_range": {
                                "field": facet_fieldname,
                                "ranges": [
                                    {
                                        "from": self._from_python(
                                            value.get("start_date")
                                        ),
                                        "to": self._from_python(value.get("end_date")),
                                    }
                                ],
                            }
                        }
                    },
                }

        if query_facets is not None:
            kwargs.setdefault("aggs", {})

            for facet_fieldname, value in query_facets:
                kwargs["aggs"][facet_fieldname] = {
                    "meta": {"_type": "query"},
                    "filter": {"query_string": {"query": value}},
                }

        if models and len(models):
            model_choices = sorted(get_model_ct(model) for model in models)
        elif limit_to_registered_models:
            # Using narrow queries, limit the results to only models handled
            # with the current routers.
            model_choices = self.build_models_list()
        else:
            model_choices = []

        if len(model_choices) > 0:
            filters.append({"terms": {DJANGO_CT: model_choices}})


        for q in narrow_queries:
            filters.append({"query_string": {"query": q}})

        if within is not None:
            filters.append(self._build_search_query_within(within))

        if dwithin is not None:
            filters.append(self._build_search_query_dwithin(dwithin))

        # if we want to filter, change the query type to bool
        if filters:
            kwargs["query"] = {"bool": {"must": kwargs.pop("query")}}
            if len(filters) == 1:
                kwargs["query"]["bool"]["filter"] = filters[0]
            else:
                kwargs["query"]["bool"]["filter"] = {"bool": {"must": filters}}

        if extra_kwargs:
            kwargs.update(extra_kwargs)

        return kwargs


class RussianElasticsearchEngine(Elasticsearch5SearchEngine):
    """
    Use in settings: `'ENGINE': 'edw.search.engines.RussianElasticsearchEngine',`
    """

    backend = RussianElasticsearchBackend
