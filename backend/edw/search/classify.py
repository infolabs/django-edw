# -*- coding: utf-8 -*-

import re
import json

from haystack import connections
from haystack.constants import DOCUMENT_FIELD, DJANGO_CT


def get_more_like_this(like, unlike=None, ignore_like=None, ignore_unlike=None, model=None):
    """
    Perform `more_like_this` query to find similar model instances.

    `model` is like 'particularproblem', 'typicalestablishment', etc.

    Common Russian stopwords are already filtered in search backend,
    this list must only contain words specific to the entity model.
    """
    backend = connections['default'].get_backend()
    fields = [DOCUMENT_FIELD]
    payload = {
        'query': {
            'bool': {
                'must': [
                    {
                        'more_like_this': {
                            'fields': fields,
                            'like': like,
                            'min_term_freq': 1,
                            'min_doc_freq': 1,
                            'max_query_terms': 25,
                            'minimum_should_match': '0%',
                            'analyzer': 'default',
                        }
                    }
                ]
            }
        }
    }
    if ignore_like:
        payload['query']['bool']['must'][0]['more_like_this']['unlike'] = ignore_like
    if unlike:
        foo = {
                'fields': fields,
                'like': unlike,
                'min_term_freq': 1,
                'min_doc_freq': 1,
                'max_query_terms': 12,
                'minimum_should_match': '0%',
                'analyzer': 'default',
            }
        if ignore_unlike:
            foo['unlike'] = ignore_unlike
        payload['query']['bool']['must_not'] = [
            {
                'more_like_this': foo
            }
        ]

    if model:
        payload['query']['bool']['filter'] = [
            {
                'term': {
                    DJANGO_CT: str(model),
                }
            }
        ]
    search_result = backend.conn.search(
        body=payload,
        index=backend.index_name,
        doc_type='modelresult',
        explain=True,
        _source=True,
        size=10,
    )
    return search_result


def analyze_suggestions(search_result):
    """
    Sort and filter `get_more_like_this` suggestions to classify category.
    """
    # Parse search result to get score and words per suggestion
    suggestions = {}
    for hit in search_result['hits']['hits']:

        # print ('hit', hit)
        # print ()

        # When querying all models at the same time,
        # some of them may have [None] in category field,
        # so we ignore them
        raw_categories = hit['_source']['categories']
        if not raw_categories:
            continue

        words = set()
        # формируем список ключевых слов
        for obj in hit['_explanation']['details']:
            raw_details = json.dumps(obj, ensure_ascii=False)
            words.update(set(re.findall(r'"weight\(\w+:(.+?)\s+in', raw_details)))

        # накапливаем результат
        for x in raw_categories:
            try:
                category = json.loads(x)
            except json.decoder.JSONDecodeError:
                pass
            else:
                score = hit['_score'] if category.get('similar', True) else -hit['_score']
                foo = suggestions.get(x, None)
                if foo is None:
                    suggestions[x] = {
                        'category': category,
                        'words': words,
                        'score': score
                    }
                else:
                    foo['score'] += score
                    foo['words'].update(words)
    # переводим множество слов в список
    suggestions = suggestions.values()
    for x in suggestions:
        x['words'] = list(x['words'])
    # сортируем
    suggestions = sorted(
        suggestions,
        key=lambda x: x['score'],
        reverse=True
    )

    # print('>>> suggestions >>> ')
    # for x in suggestions[:5]:
    #     print('------------------')
    #     print('* id:', x['category']['id'])
    #     print('* category:', x['category']['name'])
    #     print('* score:', x['score'])
    #     print('* words:', x['words'])
    # print('>>>>>>>>>>>>>>>>>>>>')

    return suggestions