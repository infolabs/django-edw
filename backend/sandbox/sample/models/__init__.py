# -*- coding: utf-8 -*-
from __future__ import unicode_literals


# import default models from django-edw to materialize them

from edw.models.defaults import mapping

from edw.models.defaults.customer import Customer
from edw.models.defaults.term import Term
from edw.models.defaults.data_mart import DataMart

from book import Book, ChildBook, AdultBook


