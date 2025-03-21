from django.db import connections
from django.db.utils import DEFAULT_DB_ALIAS


def get_db_vendor(db_alias=DEFAULT_DB_ALIAS):
    return connections[db_alias].vendor  # или укажите нужный alias
