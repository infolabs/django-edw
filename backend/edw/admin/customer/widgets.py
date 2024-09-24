from edw.admin.entity.widgets.dynamic_raw_id import ModelIdWidget, ModelRel
from edw.admin.customer import CustomerProxy


#==============================================================================
# CustomerIdWidget
#==============================================================================
class CustomerIdWidget(ModelIdWidget):

    def __init__(self, admin_site, attrs=None, using=None):
        super(CustomerIdWidget, self).__init__(admin_site, ModelRel(CustomerProxy), 'customer', attrs=None, using=None)
