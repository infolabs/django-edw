# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import hashlib
from binascii import hexlify
from django.template.defaultfilters import slugify


#==============================================================================
# create_hash
#==============================================================================
def create_hash(key):
    _hash = hashlib.md5()
    _hash.update(key)
    return _hash.hexdigest()


#==============================================================================
# create_uid
#==============================================================================
def create_uid():
    return hexlify(os.urandom(16))


#==============================================================================
# get_unique_slug
#==============================================================================
def get_unique_slug(slug, key=None):
    return ''.join([slugify(slug)[:18], create_uid() if key is None else create_hash(str(key))])


#==============================================================================
# hash_unsorted_list
#==============================================================================
def hash_unsorted_list(value):
    lst = list(value)
    lst.sort()
    return create_hash('.'.join([str(x) for x in lst]))
