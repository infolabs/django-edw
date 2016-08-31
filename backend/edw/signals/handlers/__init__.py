# -*- coding: utf-8 -*-

try:
    from . import (
        term,
        data_mart,
    )
except AttributeError as e:
    # initial migrations hack
    print e.args