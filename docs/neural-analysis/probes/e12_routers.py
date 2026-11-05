# -*- coding: utf-8 -*-
"""E12.residualcheck: own database routers for the independent alias controls.

The routers are inert until a check enables one of them, so every other probe
runs on the single ``default`` alias exactly like the product suite.
"""
from __future__ import unicode_literals


class _BaseRouter(object):
    enabled = False
    model_name = 'term'

    def _is_target(self, model):
        if not self.enabled:
            return False
        meta = getattr(model, '_meta', None)
        return meta is not None and meta.model_name == self.model_name

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return None

    def reset(self):
        self.enabled = False


class SecondAliasRouter(_BaseRouter):
    """Consistent route: both Term reads and writes on ``second``."""

    def db_for_read(self, model, **hints):
        return 'second' if self._is_target(model) else None

    def db_for_write(self, model, **hints):
        return 'second' if self._is_target(model) else None


class ReadReplicaRouter(_BaseRouter):
    """Divergent route: reads on ``second``, writes fall back to ``default``."""

    def db_for_read(self, model, **hints):
        return 'second' if self._is_target(model) else None

    def db_for_write(self, model, **hints):
        return None


class ExplicitWriteDefaultRouter(_BaseRouter):
    """Explicit divergence: reads ``second``, writes explicitly ``default``."""

    def db_for_read(self, model, **hints):
        return 'second' if self._is_target(model) else None

    def db_for_write(self, model, **hints):
        return 'default' if self._is_target(model) else None


class InstanceHintWriteRouter(_BaseRouter):
    """Class-level answers are ``default``; the instance hint moves writes.

    ``db_for_write(Term)`` is ``None`` (=> ``default``), but for an instance
    loaded from ``default`` the hinted call answers ``second``.  A guard that
    checks only the class-level answer silently follows the hint.
    """

    def db_for_read(self, model, **hints):
        return None

    def db_for_write(self, model, **hints):
        if not self._is_target(model):
            return None
        instance = hints.get('instance')
        state = getattr(instance, '_state', None)
        if state is not None and state.db == 'default':
            return 'second'
        return None


ROUTER_CLASSES = (
    SecondAliasRouter,
    ReadReplicaRouter,
    ExplicitWriteDefaultRouter,
    InstanceHintWriteRouter,
)


def reset_all():
    for router_class in ROUTER_CLASSES:
        router_class.enabled = False
