# -*- coding: utf-8 -*-

try:
    from . import (
        term,
        data_mart,
        entity,
        auth,
        notification
    )
except AttributeError as e:
    # initial migrations hack
    print e.args