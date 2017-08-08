# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
``rebuild_datamart``
---------------------

``rebuild_datamart`` rebuilds your mptt pointers. Only use in emergencies.
"""

from django.core.management.base import NoArgsCommand

from edw.models.data_mart import DataMartModel

class Command(NoArgsCommand):
    help = "Run this manually to rebuild your mptt pointers. Only use in emergencies."

    def handle_noargs(self, **options):
        #print "Rebuilding MPTT pointers for DataMartModel"
        DataMartModel._tree_manager.rebuild()
