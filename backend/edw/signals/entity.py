# -*- coding: utf-8 -*-

from django.dispatch import Signal


external_add_terms = Signal(providing_args=["instance", "pk_set"])


external_remove_terms = Signal(providing_args=["instance", "pk_set"])
