#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.admin.views.main import TO_FIELD_VAR
from salmonella.widgets import SalmonellaIdWidget

from edw.admin.customer import CustomerProxy


#==============================================================================
# CustomerRel
#==============================================================================
class CustomerRel(object):
    def __init__(self):
        self.to = CustomerProxy
        self.limit_choices_to = {}


#==============================================================================
# CustomerIdWidget
#==============================================================================
class CustomerIdWidget(SalmonellaIdWidget):
    def __init__(self, admin_site, attrs=None, using=None):
        rel = CustomerRel()
        super(CustomerIdWidget, self).__init__(rel, admin_site, attrs, using)

    def url_parameters(self):
        params = self.base_url_parameters()
        params.update({TO_FIELD_VAR: 'customer'})
        return params
