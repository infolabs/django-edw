# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.utils.encoding import smart_str

from edw.models.entity import EntityModel
from edw.models.data_mart import DataMartModel


#==============================================================================
# EntityModelTerms
#==============================================================================
EntityModelTerms = EntityModel.terms.through

EntityModelTerms._meta.verbose_name = EntityModel.TERMS_M2M_VERBOSE_NAME

EntityModelTerms._meta.verbose_name_plural = EntityModel.TERMS_M2M_VERBOSE_NAME_PLURAL

def entitymodel_terms_m2m__str__(self):
    """
    Improves string representation of m2m relationship objects
    """
    term_title = "{} - {}".format(self.term.parent.name, self.term.name) if self.term.parent else self.term.name
    return smart_str("{} → {}".format(self.entity.get_real_instance().entity_name, term_title))

EntityModelTerms.__str__ = entitymodel_terms_m2m__str__


#==============================================================================
# DataMartModelTerms
#==============================================================================
DataMartModelTerms = DataMartModel.terms.through

DataMartModelTerms._meta.verbose_name = DataMartModel.TERMS_M2M_VERBOSE_NAME

DataMartModelTerms._meta.verbose_name_plural = DataMartModel.TERMS_M2M_VERBOSE_NAME_PLURAL

def datamartmodel_terms_m2m__str__(self):
    """
    Improves string representation of m2m relationship objects
    """
    term_title = "{} - {}".format(self.term.parent.name, self.term.name) if self.term.parent else self.term.name
    return smart_str("{} → {}".format(self.datamart.get_real_instance().name, term_title))

DataMartModelTerms.__str__ = datamartmodel_terms_m2m__str__

