# -*- coding: utf-8 -*-


def make_dispatch_uid(*args):
    return "::".join(map(lambda obj: obj if isinstance(obj, str) else str(id(obj)), args))