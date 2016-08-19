# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
``rebuild_term``
---------------------

``rebuild_term`` rebuilds your mptt pointers. Only use in emergencies.
"""

from django.core.management.base import NoArgsCommand

from edw.models.term import TermModel

class Command(NoArgsCommand):
    help = "Run this manually to rebuild your mptt pointers. Only use in emergencies."

    def handle_noargs(self, **options):
        #print "Rebuilding MPTT pointers for TermModel"
        TermModel._tree_manager.rebuild()
