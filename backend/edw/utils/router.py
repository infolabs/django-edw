# -*- coding: utf-8 -*-
from django.db import DEFAULT_DB_ALIAS
from django.core.cache import cache
from django.conf import settings
from multidb import PinningReplicaRouter
from edw.management.commands.replication_health import REPLICATION_UNHEALTHY_KEY


DEFAULT_REPLICATION_MASTER_APP_LABELS = ('sessions', 'email_auth', 'contenttypes', )


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
        master_app_labels = getattr(
            settings, 'REPLICATION_MASTER_APP_LABELS',
            DEFAULT_REPLICATION_MASTER_APP_LABELS)

        if model._meta.app_label in master_app_labels:
            return DEFAULT_DB_ALIAS

        if hasattr(model, '_rest_meta') and hasattr(model._rest_meta, 'db_for_read'):
            return model._rest_meta.db_for_read(self, model, **hints)

        self.mark_healthy()
        return super().db_for_read(model, **hints)
