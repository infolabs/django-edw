# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

# import default models from django-edw to materialize them


from edw.models.defaults.customer import Customer
from edw.models.defaults.term import Term
from edw.models.defaults.data_mart import DataMart


from book import Book, ChildBook, AdultBook


from edw.models.defaults.mapping import AdditionalEntityCharacteristicOrMark
