# -*- coding: utf-8 -*-
from django.db.utils import ProgrammingError

try:
    from . import (
        term,
        data_mart,
        entity,
        auth,
        notification
    )
except (AttributeError, ProgrammingError) as e:
    # initial migrations hack
    print("*** INITIAL MIGRATIONS HACK ***")
    print e.args