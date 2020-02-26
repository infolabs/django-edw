# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
``rebuild_datamart``
---------------------

``rebuild_datamart`` rebuilds your mptt pointers. Only use in emergencies.
"""

from django.core.management.base import BaseCommand

from edw.models.data_mart import DataMartModel


class Command(BaseCommand):
    help = "Run this manually to rebuild your mptt pointers. Only use in emergencies."

    def handle(self, **options):
        #print("Rebuilding MPTT pointers for DataMartModel")
        DataMartModel._tree_manager.rebuild()
