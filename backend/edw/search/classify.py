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

    This code was written to be easily understood,
    it can be improved to run faster if needed.
    """

    # Parse search result to get score and words per suggestion
    suggestions = {}
    print('-----------------------------------------------')
    for hit in search_result['hits']['hits']:
        # When querying all models at the same time,
        # some of them may have [None] in category field,
        # so we ignore them
        raw_categories = hit['_source']['categories']
        if not raw_categories:
            continue
        words = {}
        print('----- hit[_explanation][details] --------->>>>>>', hit['_explanation']['details'])
        print()
        for word_details in hit['_explanation']['details']:
            field, word = word_details['description'].replace('weight(', '').split(' ')[0].split(':')
            foo = words.get(field, None)
            if foo is None:
                words[field] = [word]
            else:
                foo.append(word)

        for x in raw_categories:
            try:
                category = json.loads(x)
            except json.decoder.JSONDecodeError:
                pass
            else:
                pass
                # category.update({
                #     'coefficients': {'score': hit['_score']},
                #     'words': words
                # })
                # categories.append(category)


    print('>>>>>>>>>>>>>>>>>>>>>>')
    # print('>>> categories >>> ', categories)
    print()

    #     suggestion = {
    #         'coefficients': {'score': hit['_score']},
    #         'source': hit['_source'],
    #         'words': {},
    #     }
    #
    #     for word_details in hit['_explanation']['details'][0]['details']:
    #         try:
    #             field, word = word_details['description'].replace('weight(', '').split(' ')[0].split(':')
    #         except ValueError:
    #             field = 'error'
    #             word = None
    #
    #         if field not in suggestion['words']:
    #             suggestion['words'][field] = []
    #
    #         suggestion['words'][field].append(word)
    #
    #     suggestions.append(suggestion)
    #
    # # Count suggestions per category
    # category_counter = Counter()
    # for suggestion in suggestions:
    #     category = suggestion['category']
    #     category_counter[category] += 1
    #
    # for suggestion in suggestions:
    #     category = suggestion['category']
    #     suggestion['coefficients']['count'] = category_counter[category]
    #
    # # Calculate coefficients
    #
    # category_score_sums = {}
    # # category_score_mults = {}
    #
    # for suggestion in suggestions:
    #     category = suggestion['category']
    #
    #     if suggestion['category'] in category_score_sums:
    #         category_score_sums[category] += suggestion['coefficients']['score']
    #     else:
    #         category_score_sums[category] = suggestion['coefficients']['score']
    #
    # for suggestion in suggestions:
    #     category = suggestion['category']
    #     suggestion['coefficients']['score_sum'] = category_score_sums[category]
    #
    # # Sort by coefficient
    # suggestions = sorted(
    #     suggestions,
    #     key=lambda suggestion: suggestion['coefficients']['score_sum'],
    #     reverse=True
    # )
    #
    # # Make categories unique
    # unique_category_suggestions = []
    # already_present_suggestions = []
    # for suggestion in suggestions:
    #     if suggestion['category'] not in already_present_suggestions:
    #         unique_category_suggestions.append(suggestion)
    #         already_present_suggestions.append(suggestion['category'])
    #
    # return unique_category_suggestions
    return []