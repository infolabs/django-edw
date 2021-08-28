# -*- coding: utf-8 -*-
from django.db import DEFAULT_DB_ALIAS
from multidb import PinningReplicaRouter


class EdwReplicationRouter(PinningReplicaRouter):
    def db_for_read(self, model, **hints):
        if not hasattr(model, '_rest_meta'):
            return DEFAULT_DB_ALIAS
        db = model._rest_meta.db_for_read(self, model, **hints)
        return db if db is not None else super().db_for_read(model, **hints)
