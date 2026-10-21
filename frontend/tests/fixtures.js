/*
 * Общие фикстуры офлайн smoke-тестов: тематическое дерево, фасеты и витрина.
 * Формы повторяют ответы REST API django-edw, чтобы редьюсеры собрали то же
 * состояние, что и в браузере.
 */
import {
  SEMANTIC_RULE_AND,
  SEMANTIC_RULE_OR,
  STANDARD_SPECIFICATION,
  STRUCTURE_LIMB,
} from 'constants/TermsTree';


const term = (options) => Object.assign({
  name: '',
  slug: '',
  url: '',
  short_description: '',
  view_class: '',
  semantic_rule: SEMANTIC_RULE_AND,
  specification_mode: STANDARD_SPECIFICATION,
  structure: null,
  is_leaf: true,
  children: [],
}, options);


export const TERM_NAMES = {
  industry: 'Отрасли',
  it: 'Информационные технологии',
  software: 'Разработка ПО',
  consulting: 'ИТ-консалтинг',
  industry_other: 'Промышленность',
};


export const termsTree = [
  term({
    id: 1,
    name: TERM_NAMES.industry,
    slug: 'industries',
    url: '/api/terms/1/',
    view_class: 'ex-industry',
    structure: STRUCTURE_LIMB,
    is_leaf: false,
    children: [
      term({
        id: 2,
        name: TERM_NAMES.it,
        slug: 'it',
        url: '/api/terms/2/',
        short_description: 'Разработка и внедрение ПО',
        view_class: 'ex-it',
        semantic_rule: SEMANTIC_RULE_OR,
        structure: STRUCTURE_LIMB,
        is_leaf: false,
        children: [
          term({
            id: 3,
            name: TERM_NAMES.software,
            slug: 'software',
            url: '/api/terms/3/',
            view_class: 'ex-software',
          }),
          term({
            id: 4,
            name: TERM_NAMES.consulting,
            slug: 'consulting',
            url: '/api/terms/4/',
            view_class: 'ex-consulting',
          }),
        ],
      }),
      term({
        id: 5,
        name: TERM_NAMES.industry_other,
        slug: 'industry-other',
        url: '/api/terms/5/',
        structure: STRUCTURE_LIMB,
      }),
    ],
  }),
];


export const ENTITY_NAMES = {
  first: 'ООО «Альфа»',
  second: 'АО «Бета»',
};


const entity = (options) => Object.assign({
  id: 0,
  entity_name: '',
  entity_url: '',
  media: '',
  short_characteristics: [],
  short_marks: [],
  extra: {},
}, options);


export const entitiesPayload = {
  count: 45,
  limit: 10,
  offset: 0,
  next: '/api/data-marts/1/entities/?offset=10',
  previous: null,
  results: {
    objects: [
      entity({
        id: 101,
        entity_name: ENTITY_NAMES.first,
        entity_url: '/entity/101/',
        media: '<img src="/media/101.png" alt=""/>',
        short_characteristics: [
          {
            path: 'entity/org/inn',
            name: 'ИНН',
            values: ['7700000001'],
            view_class: [],
          },
        ],
        short_marks: [],
        extra: {},
      }),
      entity({
        id: 102,
        entity_name: ENTITY_NAMES.second,
        entity_url: '/entity/102/',
        media: '',
        short_characteristics: [],
        short_marks: [],
        extra: {
          geoposition: '55.755826,37.617299',
          group_size: 2,
          group_name: 'Группа «Бета»',
        },
      }),
    ],
    meta: {
      count: 45,
      limit: 10,
      offset: 0,
      ordering: 'name',
      view_component: 'tile',
      data_mart: {
        id: 1,
        name: 'Витрина «Организации»',
        limit: 10,
        max_limit: 20,
        ordering_modes: {
          name: 'по названию',
          date: 'по дате',
        },
        view_components: {
          tile: 'Плитка',
          list: 'Список',
        },
      },
      potential_terms_ids: [3],
      real_terms_ids: [3],
      subj_ids: [],
      aggregation: {
        count: {name: 'Всего', value: 45},
      },
    },
  },
};


export const requestOptions = {
  limit: 10,
  offset: 0,
  terms: [],
};


export const entryPoints = {
  1: {
    id: 1,
    name: 'Витрина «Организации»',
    template_name: 'data_mart',
    request_params: [],
    url: '/data-mart/1/',
  },
};


export const ENTRY_POINT_ID = 1;
