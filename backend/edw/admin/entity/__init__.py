#-*- coding: utf-8 -*-
from __future__ import unicode_literals

import urllib

from django.core.exceptions import ImproperlyConfigured
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin

from edw.models.entity import EntityModel

from edw.models.related import (
    AdditionalEntityCharacteristicOrMarkModel,
    EntityRelationModel,
    EntityRelatedDataMartModel,
)

from forms import (
    EntityAdminForm,
    EntityCharacteristicOrMarkInlineForm,
    EntityRelationInlineForm,
    EntityRelatedDataMartInlineForm
)

from edw.rest.filters.entity import EntityFilter

#===========================================================================================
# import edw actions
#===========================================================================================
from actions import (
    update_terms,
    update_relations,
    update_additional_characteristics_or_marks,
    update_related_data_marts,
    update_states,
    update_active,
    force_validate,
    make_terms_by_additional_attrs,
    normalize_additional_attrs
)

edw_actions = [
    update_terms, update_relations, update_additional_characteristics_or_marks, update_related_data_marts,
    update_states, update_active, force_validate, make_terms_by_additional_attrs, normalize_additional_attrs
]

DISABLED_ACTIONS = [
    "update_terms",
    "update_relations",
    "update_additional_characteristics_or_marks",
    "update_related_data_marts",
    "update_states",
    "update_active",
    "update_images",
    "force_validate",
    "make_terms_from_additional_characteristics_or_marks",
    "remove_additional_characteristics_or_marks_with_exists_value_term"
]


def filter_actions(request, actions):
    if not request.user.is_superuser:
        for a in DISABLED_ACTIONS:
            if a in actions.keys():
                del actions[a]
    return actions


try:
    from edw.models.related.entity_image import EntityImageModel
    EntityImageModel()  # Test pass if model materialized
except (ImproperlyConfigured, ImportError):
    pass
else:
    from actions import update_images

    edw_actions.append(update_images)
#===========================================================================================


#===========================================================================================
# TermsTreeFilter
#===========================================================================================
class TermsTreeFilter(admin.ListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Terms')
    template = 'edw/admin/term/filters/tree/filter.html'

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
                self.used_parameters[self.parameter_name] = value

    def has_output(self):
        return True

    def value(self):
        return self.used_parameters.get(self.parameter_name, None)

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, cl):
        value = self.value()
        if value:
            values = urllib.unquote(value).decode('utf8').split(',')
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


#===========================================================================================
# EntityCharacteristicOrMarkInline
#===========================================================================================
class EntityCharacteristicOrMarkInline(admin.TabularInline):
    model = AdditionalEntityCharacteristicOrMarkModel
    fields = ['term', 'value', 'view_class']
    extra = 1
    form = EntityCharacteristicOrMarkInlineForm


#===========================================================================================
# EntityRelationInline
#===========================================================================================
class EntityRelationInline(admin.TabularInline):
    model = EntityRelationModel
    fields = ['term', 'to_entity']
    fk_name = 'from_entity'
    extra = 1
    form = EntityRelationInlineForm


#===========================================================================================
# EntityRelatedDataMartInline
#===========================================================================================
class EntityRelatedDataMartInline(admin.TabularInline):
    model = EntityRelatedDataMartModel
    fields=['data_mart']
    fk_name = 'entity'
    extra = 1
    form = EntityRelatedDataMartInlineForm


#===========================================================================================
# EntityChildModelAdmin
#===========================================================================================
class EntityChildModelAdmin(PolymorphicChildModelAdmin):

    base_model = EntityModel

    base_form = EntityAdminForm

    base_fieldsets = (
        (_("Main params"), {
            'fields': ('get_name', 'get_type', 'active', 'created_at', 'terms'),
        }),
    )

    readonly_fields = ('get_name', 'get_type')

    list_display = ('get_name', 'get_type', 'active', 'created_at')

    inlines = [EntityCharacteristicOrMarkInline, EntityRelationInline, EntityRelatedDataMartInline]

    list_filter = (TermsTreeFilter, 'active')

    actions = edw_actions

    save_on_top = True

    show_in_index = True

    def get_name(self, object):
        return object.get_real_instance().entity_name
    get_name.short_description = _("Name")

    def get_type(self, object):
        return object.get_real_instance().entity_type()
    get_type.short_description = _("Entity type")

    class Media:
        css = {
            'all': (
                '/static/css/admin/entity.css',
                '/static/edw/css/admin/jqtree.css',
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.min.css',
            )
        }
        js = (

            '/static/edw/lib/spin/spin.min.js',
            '/static/edw/js/admin/jquery.compat.js',
            '/static/edw/js/admin/tree.jquery.js'
        )

    def get_actions(self, request):
       actions = super(EntityChildModelAdmin, self).get_actions(request)
       return filter_actions(request, actions)


# ===========================================================================================
# EntityParentModelAdmin
# ===========================================================================================
class EntityParentModelAdmin(PolymorphicParentModelAdmin):

    base_model = EntityModel

    form = EntityAdminForm

    base_fieldsets = (
        (_("Main params"), {
            'fields': ('get_name', 'get_type', 'active', 'created_at', 'terms'),
        }),
    )

    readonly_fields = ('get_name', 'get_type')

    list_display = ('get_name', 'get_type', 'active', 'created_at')

    actions = edw_actions

    inlines = [EntityCharacteristicOrMarkInline, EntityRelationInline, EntityRelatedDataMartInline]

    save_on_top = True

    list_filter = (TermsTreeFilter, 'active')

    list_per_page = 250

    list_max_show_all = 1000

    def get_name(self, object):
        return object.get_real_instance().entity_name
    get_name.short_description = _("Name")

    def get_type(self, object):
        return object.get_real_instance().entity_type()
    get_type.short_description = _("Entity type")

    class Media:
        css = {
            'all': (
                '/static/edw/css/admin/jqtree.css',
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.min.css',
            )
        }
        js = (

            '/static/edw/lib/spin/spin.min.js',
            '/static/edw/js/admin/jquery.compat.js',
            '/static/edw/js/admin/tree.jquery.js'
        )

    def get_actions(self, request):
       actions = super(EntityParentModelAdmin, self).get_actions(request)
       return filter_actions(request, actions)
