# -*- coding: utf-8 -*-
from django.db import DEFAULT_DB_ALIAS
from django.core.cache import cache
from django.conf import settings
from multidb import PinningReplicaRouter
from edw.management.commands.replication_health import REPLICATION_UNHEALTHY_KEY


class EdwReplicationRouter(PinningReplicaRouter):
    initial_replica_databases = None
    unhealthy = []

    def mark_healthy(self):
        if self.initial_replica_databases is None:
            self.initial_replica_databases = settings.REPLICA_DATABASES

        unhealthy = cache.get(REPLICATION_UNHEALTHY_KEY, [])
        if set(unhealthy) == set(self.unhealthy):
            return
        self.unhealthy = unhealthy
        healthy = [k for k in self.initial_replica_databases if k not in unhealthy]
        settings.REPLICA_DATABASES = healthy

    def db_for_read(self, model, **hints):
        self.mark_healthy()

        # TODO: doesn't work, for example Term has no _rest_meta and so on
        if not hasattr(model, '_rest_meta'):
            return DEFAULT_DB_ALIAS
        db = model._rest_meta.db_for_read(self, model, **hints)
        return db if db is not None else super().db_for_read(model, **hints)
