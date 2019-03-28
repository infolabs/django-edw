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


#==============================================================================
# Cookie hash and cookie key, should be consistent with
# frontend/src/utils/hashUtils.js
#==============================================================================
def int32(x):
    x = 0xffffffff & x
    if x > 0x7fffffff:
        return -(~(x - 1) & 0xffffffff)
    else:
        return x


def cookie_hash(s):
    hash_code = 0
    if len(s) == 0:
        return hash_code
    for l in s:
        char = ord(l)
        hash_code = ((hash_code << 5) - hash_code) + char
        hash_code = int32(hash_code)  # Convert to 32bit integer
    return abs(hash_code)


def cookie_key(data_mart_id, path, setting):
    return "dm_{}_{}_{}".format(data_mart_id, str(cookie_hash(path)), setting)


def get_cookie_setting(request, setting):
    data_mart = request.GET['_data_mart']
    if data_mart is not None:
        key = cookie_key(data_mart.pk, request.path, setting)
        return request.COOKIES.get(key, None)
