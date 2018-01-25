# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
``force_resave_entities``
---------------------

``force_resave_entities`` save all your entities with force validate terms. Only use for initial terms auto set.
"""

from django.core.management.base import NoArgsCommand

from edw.models.entity import EntityModel


class Command(NoArgsCommand):
    help = "Run this manually to save all entities with force validate"

    def handle_noargs(self, **options):
        print "Save all entities with force validate terms"
        all_entities = EntityModel.objects.all()
        for entity in all_entities:
            entity.save(force_validate_terms=True, bulk_force_validate_terms=True)
