# -*- coding: utf-8 -*-
"""
E11/R5: real database routers for the write-alias regression gate.

No router function is monkeypatched: the tests flip the class attribute
``route_all`` (or ``enabled``) on the real router object.  Disabled routers
return ``None`` for every hook, so the rest of the runtime suite runs on the
single ``default`` alias exactly as before.
"""
from __future__ import unicode_literals


class _BaseRouter(object):
    route_all = False
    enabled = False
    model_name = 'term'

    def _is_target(self, model):
        if not (self.route_all or self.enabled):
            return False
        meta = getattr(model, '_meta', None)
        return meta is not None and meta.model_name == self.model_name

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return None

    def reset(self):
        self.route_all = False
        self.enabled = False


class TermSecondAliasRouter(_BaseRouter):
    """Route all Term traffic (read and write) to ``second`` while enabled."""

    def db_for_read(self, model, **hints):
        return 'second' if self._is_target(model) else None

    def db_for_write(self, model, **hints):
        return 'second' if self._is_target(model) else None


class ReadReplicaRouter(_BaseRouter):
    """Route Term reads to the replica; Term writes stay on ``default``.

    ``db_for_write`` returns ``None`` (the Django default), so the divergence is
    only visible through the read side.
    """

    def db_for_read(self, model, **hints):
        return 'second' if self._is_target(model) else None

    def db_for_write(self, model, **hints):
        return None


class ExplicitWriteDefaultRouter(_BaseRouter):
    """Explicitly diverge: reads on ``second``, writes explicitly ``default``.

    Unlike :class:`ReadReplicaRouter`, the write side returns a real alias
    instead of ``None``; both sides are configured and still disagree.
    """

    def db_for_read(self, model, **hints):
        return 'second' if self._is_target(model) else None

    def db_for_write(self, model, **hints):
        return 'default' if self._is_target(model) else None


class InstanceHintWriteRouter(_BaseRouter):
    """Both class-level answers are ``default``; an instance hint writes second.

    This is the ``write=None`` + instance-hint hazard: nothing is visible at the
    model level, but ``router.db_for_write(Model, instance=obj)`` silently moves
    the write to another alias.  The guard must refuse instead of following the
    hint.
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
    TermSecondAliasRouter,
    ReadReplicaRouter,
    ExplicitWriteDefaultRouter,
    InstanceHintWriteRouter,
)


def reset_all():
    for router_class in ROUTER_CLASSES:
        router_class.route_all = False
        router_class.enabled = False
