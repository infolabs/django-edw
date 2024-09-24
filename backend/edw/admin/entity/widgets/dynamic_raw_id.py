from django.contrib.admin.views.main import TO_FIELD_VAR
try:
    from salmonella.widgets import SalmonellaIdWidget
except ImportError:
    from dynamic_raw_id.widgets import DynamicRawIDWidget as SalmonellaIdWidget


#==============================================================================
# ModelRel
#==============================================================================
class Field(object):
    def __init__(self, name):
        self.name =  name


class ModelRel(object):
    def __init__(self, model):
        self.to = model
        self.limit_choices_to = {}
        self.model = model

    def get_related_field(self):
        return Field('customer')


#==============================================================================
# ModelIdWidget
#==============================================================================
class ModelIdWidget(SalmonellaIdWidget):
    def __init__(self, admin_site, rel, to_field, attrs=None, using=None):
        self.to_field = to_field
        super(ModelIdWidget, self).__init__(rel, admin_site, attrs, using)

    def url_parameters(self):
        params = self.base_url_parameters()
        params.update({TO_FIELD_VAR: self.to_field})
        return params
