# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
``rebuild_term``
---------------------

``rebuild_term`` rebuilds your mptt pointers. Only use in emergencies.
"""

from django.core.management.base import BaseCommand

from edw.models.term import TermModel


class Command(BaseCommand):
    help = "Run this manually to rebuild your mptt pointers. Only use in emergencies."

    def handle(self, **options):
        #print("Rebuilding MPTT pointers for TermModel")
        TermModel._tree_manager.rebuild()
