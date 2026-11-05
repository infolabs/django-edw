# -*- coding: utf-8 -*-
"""Harness smoke test: the independent settings/URLconf boot against the wheel."""
from __future__ import unicode_literals

import pytest

pytestmark = pytest.mark.django_db


def test_wheel_and_smoke(operator):
    from edw.models.defaults.term import Term

    Term.objects.create(name='Smoke root', slug='e12-smoke-root')
    response = operator.get('/edw/api/terms/')
    assert response.status_code == 200, response.content[:400]
    assert response.data['count'] >= 1, response.data
