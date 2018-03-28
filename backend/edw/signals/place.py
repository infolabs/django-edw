# -*- coding: utf-8 -*-

from django.dispatch import Signal


zone_changed = Signal(providing_args=["instance", "zone_term_ids_to_remove", "zone_term_ids_to_add"])