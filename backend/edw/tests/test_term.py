# -*- coding: utf-8 -*-
from django.test import TestCase

from edw.models.defaults.term import Term
from edw.models.term import TermModel


class TermTestHandler(TestCase):
    TERMS = {
        "term1": {
            "id": 1,
            "name": "Term1",
            "slug": "term1",
            "path": "term1",
            "semantic_rule": 10,
            "attributes": "0",
            "specification_mode": 10,
            "view_class": None,
            "description": "",
            "active": True,
            "system_flags": "0"
        },
        "term2": {
            "id": 2,
            "name": "Term2",
            "slug": "term2",
            "path": "term1/term2",
            "semantic_rule": 20,
            "attributes": "0",
            "specification_mode": 10,
            "view_class": None,
            "description": "",
            "active": True,
            "system_flags": "0",
        },
        'term2_1': {
            "id": 4,
            "name": "Term2_1",
            "slug": "term2_1",
            "path": "term1/term2/term2_1",
            "semantic_rule": 10,
            "attributes": "0",
            "specification_mode": 10,
            "view_class": None,
            "description": "",
            "active": True,
            "system_flags": "0"
        },
        'term2_2': {
            "id": 5,
            "name": "Term2_2",
            "slug": "term2_2",
            "path": "term1/term2/term2_2",
            "semantic_rule": 10,
            "attributes": "0",
            "specification_mode": 10,
            "view_class": None,
            "description": "",
            "active": True,
            "system_flags": "0"
        },
        'term3': {
            "id": 3,
            "name": "Term3",
            "slug": "term3",
            "path": "term3",
            "semantic_rule": 10,
            "attributes": "0",
            "specification_mode": 10,
            "view_class": None,
            "description": "",
            "active": True,
        },
    }

    def setUp(self):
        self.term1 = Term.objects.create(**self.TERMS['term1'])
        self.term1.save()
        self.term2 = Term.objects.create(**self.TERMS['term2'])
        self.term2.parent = self.term1
        self.term2.save()
        self.term2_1 = Term.objects.create(**self.TERMS['term2_1'])
        self.term2_1.parent = self.term2
        self.term2_1.save()
        self.term2_2 = Term.objects.create(**self.TERMS['term2_2'])
        self.term2_2.parent = self.term2
        self.term2_2.save()
        self.term3 = Term.objects.create(**self.TERMS['term3'])
        self.term3.save()

    def test_term_decompress(self):
        self.assertEqual(TermModel.decompress(value=[4,5]), {1: [[[], []]], 2: [[], []], 4: [], 5: []})

    def test_term_decompress_fix_it_true(self):
        self.assertEqual(TermModel.decompress(value=[4, 5], fix_it=True), {1: [[]], 2: []})
