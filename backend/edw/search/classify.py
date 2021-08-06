# -*- coding: utf-8 -*-

import re
import json
import math

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
    '''
    Sort and filter `get_more_like_this` suggestions to classify category.
    Интерпретация confidience:
    менее 1 - точно нет
    от 1 до 1.23 - слабая уверенность
    от 1.23 до 1.81 - средняя уверенность
    более 1.81 - высокая уверенность
    '''
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
                score = hit['_score']
                similar = category.get('similar', True)
                foo = suggestions.get(x, None)
                if foo is None:
                    suggestions[x] = {
                        'category': category,
                        'words': words,
                        'count': 1,
                        'score': score,
                        'confidience': 0,
                        'similar': similar
                    }
                else:
                    foo['score'] = max(foo['score'], score)
                    foo['count'] += 1
                    foo['words'].update(words)

    # переводим множество слов в список
    suggestions = suggestions.values()

    geo_mean, cnt, min_score = {
        False: 1,
        True: 1
    }, {
        False: 0,
        True: 0
    }, {
        False: 0,
        True: 0
    }

    for x in suggestions:
        similar = x['similar']
        score = x['score']
        min_f_metric = min_score[similar]
        x['words'] = list(x['words'])
        precision = score
        recall = x['count']
        B = .2
        b2 = B ** 2

        # F-metric
        score = x['score'] = (1 + b2) * precision * recall / (b2 * precision + recall)
        geo_mean[similar] *= score
        cnt[similar] += 1
        min_score[similar] = min(min_f_metric, score) if min_f_metric > 0 else score

        # print()
        # print('category, precision, recall', x['category'], precision, recall)
        # print()

    for x in (True, False):
        # Вычисляем среднее арифметическое и среднее геометрическое рейтинга среди всех выявленных тем
        _cnt = cnt[x]
        geo_mean[x] = geo_mean[x] ** (1 / _cnt) if _cnt else 0

    for x in suggestions:
        similar = x['similar']
        _min_score = min_score[similar]
        _delta = geo_mean[similar] - _min_score
        _shifted_score = x['score'] - _min_score
        x['confidience'] = math.log(_shifted_score / _delta, 4) if _delta > 0 else 0

    for x in suggestions:
        if not x['similar']:
            x['score'] = -x['score']

    # сортируем
    suggestions = sorted(
        suggestions,
        key=lambda x: x['confidience'],
        reverse=True
    )

    # for development purposes only
    # print()
    # for x in suggestions:
    #     print('------------------')
    #     print('* id:', x['category']['id'])
    #     print('* category:', x['category']['name'])
    #     print('* score:', x['score'])
    #     print('* confidience:', x['confidience'])
    #     print('* similar:', x['similar'])
    #     print('* count:', x['count'])
    #     print('* words:', x['words'])
    # print()

    return suggestions