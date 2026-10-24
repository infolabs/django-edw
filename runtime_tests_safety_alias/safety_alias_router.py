# -*- coding: utf-8 -*-
"""E9/R5: real two-database routers (no monkeypatched router function)."""
from __future__ import unicode_literals


class _BaseRouter(object):
    route_all = False
    model_name = 'term'

    def _is_target(self, model):
        if not self.route_all:
            return False
        meta = getattr(model, '_meta', None)
        return meta is not None and meta.model_name == self.model_name

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return None


class TermSecondAliasRouter(_BaseRouter):
    """Routes all Term traffic (read and write) to ``second`` while enabled."""

    def db_for_read(self, model, **hints):
        return 'second' if self._is_target(model) else None

    def db_for_write(self, model, **hints):
        return 'second' if self._is_target(model) else None


class ReadReplicaRouter(_BaseRouter):
    """Routes Term reads to the replica while TERM writes stay on default."""

    def db_for_read(self, model, **hints):
        return 'second' if self._is_target(model) else None

    def db_for_write(self, model, **hints):
        return None
