# -*- coding: utf-8 -*-
from django.db.utils import ProgrammingError, ImproperlyConfigured

try:

    from . import (
        term,
        data_mart,
        entity,
        # auth,
        # notification,
    )

    # try import `boundary`
    try:
        from . import boundary
    except (ImproperlyConfigured, ImportError, RuntimeError):
        pass

    # try import `postal_zone`
    try:
        from . import postal_zone
    except (ImproperlyConfigured, ImportError, RuntimeError):
        pass

    # try import `email_category`
    try:
        from . import email_category
    except (ImproperlyConfigured, ImportError, RuntimeError):
        pass

except (AttributeError, ProgrammingError) as e:
    # initial migrations hack
    print("*** INITIAL MIGRATIONS HACK ***")
    print(e.args)
