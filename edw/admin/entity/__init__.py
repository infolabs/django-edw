#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.admin import ListFilter

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

from edw.rest.filters.entity import EntityFilter


#===========================================================================================
#
#===========================================================================================
class TermsTreeFilter(ListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Terms')
    template = 'edw/admin/term/widgets/filter_tree.html'
    node_template = 'simple'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'terms'

    def __init__(self, request, params, model, model_admin):
        super(TermsTreeFilter, self).__init__(
            request, params, model, model_admin)

        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify "
                "a 'parameter_name'." % self.__class__.__name__)

        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            if value:
                self.used_parameters[self.parameter_name] = str(value)

    def has_output(self):
        return True

    def value(self):
        return self.used_parameters.get(self.parameter_name, None)

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, cl):
        value = self.value()
        if value:
            values = value.split(',')
        else:
            values = list()

        yield {
            'title': self.title,
            'selected': values
        }

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        request.
        """
        f = EntityFilter(request.GET, queryset=queryset)
        return f.qs