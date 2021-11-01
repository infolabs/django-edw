# -*- coding: utf-8 -*-

import re
import json
import math

from haystack import connections
from haystack.constants import DOCUMENT_FIELD, DJANGO_CT

from .. import settings as edw_settings


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
    менее 0 - точно нет
    от 0 до 0.2 - очень низкая вероятность
    от 0.2 до 0.4 - низкая вероятность
    от 0.4 до 0.6 - cредняя вероятность
    от 0.6 до 0.8 - высокая вероятность
    более 0.8 - очень высокая вероятность
    '''
    # Parse search result to get score and words per suggestion
    raw_suggestions = {}
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
                foo = raw_suggestions.get(x, None)
                if foo is None:
                    raw_suggestions[x] = {
                        'category': category,
                        'words': words,
                        'count': 1,
                        'score': score,
                        'similar': similar
                    }
                else:
                    foo['score'] = max(foo['score'], score)
                    foo['count'] += 1
                    foo['words'].update(words)

    suggestions = []
    _suggestions = {
        True: {
            'results': [],
            'geo_mean_score': 1,
            'min_score': None,
            'max_score': None,
        },
        False: {
            'results': [],
            'geo_mean_score': 1,
            'min_score': None,
            'max_score': None,
        },
    }

    # получаем балансовый коэффициент для расчета F меры
    b2 = edw_settings.CLASSIFY['precision_recall_balance'] ** 2

    # Переводим множество слов в список, для "похожих" / "не похожих" категорий формируем разные списки.
    for x in raw_suggestions.values():
        similar = x['similar']
        same_suggestions = _suggestions[similar]
        same_suggestions['results'].append(x)
        min_score, max_score = same_suggestions['min_score'], same_suggestions['max_score']
        x['words'] = list(x['words'])
        precision, recall = x['score'], x['count']

        # F-metric
        score = x['score'] = (1 + b2) * precision * recall / (b2 * precision + recall)

        same_suggestions['geo_mean_score'] *= score
        same_suggestions['min_score'] = score if min_score is None else min(min_score, score)
        same_suggestions['max_score'] = score if max_score is None else max(max_score, score)

    # получаем балансовый коэффициент для расчета Confidence
    b2 = edw_settings.CLASSIFY['emission_dispersion_balance'] ** 2

    # относительная погрешность
    relative_error = edw_settings.CLASSIFY['relative_error']
    # разница между доминантом и остальной группой
    dominant_difference = edw_settings.CLASSIFY['dominant_difference']

    # обрабатываем результаты отдельно для "похожих" и "не похожих" категорий
    raw_results = {
        True: [],
        False: []
    }
    for similar in (True, False):
        # Вычисляем среднее геометрическое рейтинга среди всех выявленных тем
        same_suggestions = _suggestions[similar]
        cnt = len(same_suggestions['results'])

        if cnt:
            max_score, min_score = same_suggestions['max_score'], same_suggestions['min_score']
            geo_mean_score = same_suggestions['geo_mean_score'] = same_suggestions['geo_mean_score'] ** (1 / cnt)
            delta_score = same_suggestions['delta_score'] = max_score - min_score

            same_suggestions_results = same_suggestions['results']
            results = raw_results[similar]
            if delta_score != 0:
                # Сортируем
                same_suggestions_results = sorted(
                    same_suggestions_results,
                    key=lambda y: y['score'],
                    reverse=True
                )

                # Вычисляем показатели для определениия коэффициента уверености в правильном ответе, для каждого варианта
                max_confidence = None
                for suggestion in same_suggestions_results:
                    score = suggestion['score']
                    emission = math.fabs(suggestion['score'] - geo_mean_score) / delta_score
                    dispersion = delta_score * score / (max_score ** 2)

                    # Confidence - гармоническое среднее, зависит от разброса значений и их кучности
                    confidence = suggestion['confidence'] = (1 + b2) * emission * dispersion / (
                            b2 * emission + dispersion)

                    max_confidence = confidence if max_confidence is None else max(max_confidence, confidence)

                #  Фильтрация
                suggestion = same_suggestions_results[0]
                results.append(suggestion)

                potential_dominants = [suggestion]
                has_dominant = False
                dominant_delta = 0
                dominant_cnt = 1
                i = 1

                c0 = suggestion['confidence']
                d0 = c0 / max_confidence
                d0_avg = d0

                for suggestion in same_suggestions_results[1:]:
                    c = suggestion['confidence']
                    d = c / max_confidence
                    delta = d - d0
                    if delta <= relative_error:
                        results.append(suggestion)
                        if not has_dominant:
                            d0_avg = ((dominant_cnt - 1) * d0_avg + d0) / dominant_cnt
                            if d0_avg - d >= dominant_difference:
                                has_dominant = True
                            else:
                                dominant_delta -= delta
                                potential_dominants.append(suggestion)
                                dominant_cnt += 1
                        c0, d0 = c, d
                        i += 1
                    else:
                        break

                for suggestion in same_suggestions_results[i:]:
                    results.append(suggestion)
                    suggestion['status'] = 'fake'

                if has_dominant and dominant_delta / dominant_cnt <= relative_error:
                    for suggestion in potential_dominants:
                        suggestion['status'] = 'dominant'

            else:
                for suggestion in same_suggestions_results:
                    suggestion['confidence'] = 0
                    suggestion['status'] = 'dominant'
                    results.append(suggestion)

            if not similar:
                # Меняем порядок сортировки и знак для "не похожих" категорий
                results.reverse()
                for suggestion in results:
                    suggestion['score'] = -suggestion['score']

            # Добавлям в результирующий список
            suggestions.extend(results)

        else:
            # Категории не найдены
            del same_suggestions['geo_mean_score']
            del same_suggestions['min_score']
            del same_suggestions['max_score']

    # for development purposes only
    # print()
    # for x in suggestions:
    #     print('------------------')
    #     print('* id:', x['category']['id'])
    #     print('* category:', x['category']['name'])
    #     print('* score:', x['score'])
    #     print('* confidence:', x['confidence'])
    #     print('* similar:', x['similar'])
    #     print('* count:', x['count'])
    #     print('* words:', x['words'])
    # print()

    return suggestions
