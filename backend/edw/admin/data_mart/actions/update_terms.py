from django.utils.translation import ugettext_lazy as _

from edw.tasks import update_data_mart_terms
from edw.admin.base_actions import update_terms as base_update_terms


def update_terms(modeladmin, request, queryset):
    """
    Обновляет термины для нескольких объектов возвращая базовую функция обновления терминов
    передавая название task`а, который будет запущен.
    """
    return base_update_terms.update_terms(modeladmin, request, queryset, update_data_mart_terms)


update_terms.short_description = _("Modify terms for selected %(verbose_name_plural)s")
