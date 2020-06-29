# -*- coding: utf-8 -*-

import json
from collections import Counter
# from math import log

from haystack import connections


def get_more_like_this(text, entity_model=None, stop_words=None):
    """
    Perform `more_like_this` query to find similar model instances.

    `entity_model` is like 'particularproblem', 'typicalestablishment', etc.

    `stop_words` is a list of stopwords to make search results better.
    Common Russian stopwords are already filtered in search backend,
    this list must only contain words specific to the entity model.
    """

    backend = connections['default'].get_backend()

    payload = {
        'query': {
            'bool': {
                'must': [
                    {
                        'more_like_this': {
                            'fields': ['title', 'text', 'category', 'characteristics'],
                            'like': text,
                            'min_term_freq': 1,
                            'min_doc_freq': 1,
                            'max_query_terms': 200,
                            'minimum_should_match': '0%',
                            'analyzer': 'default',
                            'stop_words': stop_words or []
                        }
                    }
                ]
            }
        }
    }
    if entity_model:
        payload['query']['bool']['filter'] = [
            {
                'term': {
                    'entity_model': entity_model,
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

    # print('----- search_result -----', search_result)
    # print()
    # print()
    # print()

    # Parse search result to get score and words per suggestion
    suggestions = {}
    for hit in search_result['hits']['hits']:
        # When querying all models at the same time,
        # some of them may have [None] in category field,
        # so we ignore them
        raw_categories = hit['_source']['categories']
        if not raw_categories:
            continue
        words = set()
        # print('----- hit[_explanation][details] --------->>>>>>', hit['_explanation'])

        # формируем список ключевых слов
        for raw_word_details in hit['_explanation']['details']:
            for word_details in (raw_word_details['details'][0], raw_word_details):
                try:
                    words.add(word_details['description'].replace('weight(', '').split(' ')[0].split(':')[1])
                except IndexError:
                    pass
                else:
                    break
        # накапливаем результат
        for x in raw_categories:
            try:
                category = json.loads(x)
            except json.decoder.JSONDecodeError:
                pass
            else:
                foo = suggestions.get(x, None)
                if foo is None:
                    suggestions[x] = {
                        'category': category,
                        'words': words,
                        'score': hit['_score']
                    }
                else:
                    foo['score'] += hit['_score']
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

    print('>>> suggestions >>> ')
    for x in suggestions[:5]:
        print('------------------')
        print('* id:', x['category']['id'])
        print('* category:', x['category']['name'])
        print('* score:', x['score'])
        print('* words:', x['words'])

    print('>>>>>>>>>>>>>>>>>>>>')


    return suggestions