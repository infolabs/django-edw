# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from collections import Counter

from django.apps import apps
# from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _

from haystack.utils import get_model_ct

# from edw.models.entity import EntityModel
from edw.search.classify import get_more_like_this, analyze_suggestions


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'entity_model',
            help=_('Run tests against this entity model. Example: nash_region.particularproblem')
        ),

    def show_entity_info(self, entity, suggestions, is_guessed):
        print('Объект {}, категория {}'.format(entity.id, entity.category.id))

        if suggestions:
            print('Текст:')
            print('  {}'.format(' '.join(entity.description.splitlines())))
            print('Правильная категория:')
            print('  {}'.format(entity.category.entity_name))

            if is_guessed:
                print('Определилась как:')
                print('✓ ' + entity.category.entity_name)
                print()
                pass
            else:
                print()
                print('Сводка по коэффициентам:')

                suggestion_coefficients = []
                for i, suggestion in enumerate(suggestions):
                    is_right = '→ ' if suggestion['category'] == entity.category.entity_name else ''
                    suggestion_row = [is_right + suggestion['category'][:80]]
                    for key, value in suggestion['coefficients'].items():
                        suggestion_row.append(round(value, 2))
                    suggestion_coefficients.append(suggestion_row)

                # Requires tabulate package
                # print(tabulate(suggestion_coefficients, headers=['category', *[key for key in suggestion['coefficients']]]))

                # Some kind of tabulate package replacement.
                # Didn't want to bring another package in project just for this case
                head_row = ['category']
                for key in suggestion['coefficients']:
                    head_row.append(key)
                for row in suggestion_coefficients:
                    print(row)

                print()
                print('Сводка по словам:')
                for i, suggestion in enumerate(suggestions):
                    is_right = '→' if suggestion['category'] == entity.category.entity_name else ' '
                    print('{is_right} {i+1}. {suggestion["category"]}'.format(**locals()))

                    print('     Самые весомые слова в полях:')
                    for field, words in suggestion['words'].items():
                        if words:
                            print('       {field}: {words}'.format(**locals()))

                    print()

        else:
            print('Определилась как:')
            print('✗ Никак')
            print()
            pass

        print()
        print()

    def show_total_info(self, entity_count, guessed_right_count, guessed_wrong_count, dunno_count, right_indexes):
        right_index_counter = Counter(right_indexes)

        print('Объектов в тестовой выборке:', entity_count)
        print('Правильная категория на первом месте:', str(round(guessed_right_count / entity_count * 100, 2)) + '%')
        print('Правильной категории нет в предложенных вариантах:', str(round(guessed_wrong_count / entity_count * 100, 2)) + '%')

        most_common = right_index_counter.most_common(100)
        print('Распределение позиции правильной категории в предложенных вариантах:', most_common)
        first_3 = sum([index[1] for index in most_common[:3]])
        print('В первых трёх:', str(round(first_3 / sum([x[1] for x in most_common]) * 100, 2)) + '%')
        first_4 = sum([index[1] for index in most_common[:4]])
        print('В первых четырёх:', str(round(first_4 / sum([x[1] for x in most_common]) * 100, 2)) + '%')
        first_5 = sum([index[1] for index in most_common[:5]])
        print('В первых пяти:', str(round(first_5 / sum([x[1] for x in most_common]) * 100, 2)) + '%')

        print('Вообще никак не определились:', str(round(dunno_count / entity_count * 100, 2)) + '%')

    def handle(self, **options):
        """
        Grab `created_at__year__gte='2020'` instances and try to classify them,
        based on models in search index. Search index must be populated beforehand
        with `created_at__year__lt='2020'` instances
        """

        model = apps.get_model(options['entity_model'])
        entity_model = get_model_ct(model).split('.')[1]
        queryset = model.objects \
            .instance_of(model) \
            .filter(active=True) \
            .filter(description__isnull=False) \
            .filter(created_at__year__gte='2020') \
            .order_by('-created_at')

        total_info = {
            'entity_count': 0,
            'guessed_right_count': 0,
            'guessed_wrong_count': 0,
            'dunno_count': 0,
            'right_indexes': [],
        }
        for entity in queryset:
            total_info['entity_count'] += 1

            search_result = get_more_like_this(entity.description, entity_model)
            suggestions = analyze_suggestions(search_result)

            if suggestions:
                if suggestions[0]['category'] == entity.category.entity_name:
                    is_guessed = True
                    total_info['guessed_right_count'] += 1
                    total_info['right_indexes'].append(1)

                else:
                    is_guessed = False
                    for i, suggestion in enumerate(suggestions):
                        if suggestion['category'] == entity.category.entity_name:
                            total_info['right_indexes'].append(i + 1)
                            is_guessed = True

                    if not is_guessed:
                        total_info['guessed_wrong_count'] += 1

            else:
                is_guessed = False
                total_info['dunno_count'] += 1

            entity_info = {
                'entity': entity,
                'suggestions': suggestions,
                'is_guessed': is_guessed,
            }

            self.show_entity_info(**entity_info)

        self.show_total_info(**total_info)
