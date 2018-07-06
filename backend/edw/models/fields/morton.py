from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.db.models import Lookup
from django.db.models.lookups import PatternLookup


class BaseMortonOrder(object):
    def __init__(self, mortoncode=None, base=32, fn=lambda: '', inv_fn=lambda: None, *args):
        self.args = args
        self.interleave = fn
        self.deinterleave = inv_fn

        if mortoncode is None:
            self.mortoncode = self.interleave()
        else:
            self.mortoncode = mortoncode

    def __str__(self):
        return "%s,%s" % (self.mortoncode)

    def __repr__(self):
        return "MortonOrder(%s)" % str(self)

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        return isinstance(other, BaseMortonOrder) and self.mortoncode == other.mortoncode

    def __ne__(self, other):
        return not isinstance(other, BaseMortonOrder) or self.mortoncode != other.mortoncode

    def __gt__(self, other):
        return not isinstance(other, BaseMortonOrder) or self.mortoncode > other.mortoncode

    def __lt__(self, other):
        return not isinstance(other, BaseMortonOrder) or self.mortoncode < other.mortoncode

    def interleave(self, *args, **kwargs):
        pass

    def deinterleave(self, *args, **kwargs):
        pass


class MortonField(models.Field):
    description = _("MortonOrder field")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 255
        super(MortonField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'CharField'

    def to_python(self, value):
        if not value or value == 'None':
            return None
        if isinstance(value, MortonField):
            return value
        # default case is string
        return BaseMortonOrder(mortoncode=value)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def get_prep_value(self, value):
        return str(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return smart_text(value)


@MortonField.register_lookup
class MortonSearchMatchedLookup(Lookup):
    lookup_name = 'mortonsearch'

    def __init__(self, lhs, rhs):
        super(MortonSearchMatchedLookup, self).__init__(lhs, rhs)

    def process_rhs(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = super(MortonSearchMatchedLookup, self).process_rhs(compiler, connection)
        rhs = ''
        params = rhs_params[0]
        if params and not self.bilateral_transforms:
            rhs_params[0] = "%s%%" % connection.ops.prep_for_like_query(params)
            rhs += lhs + 'like %s'
        return rhs, rhs_params

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return rhs, params


@MortonField.register_lookup
class MortonPreciseSearchMatchedLookup(PatternLookup):
    lookup_name = 'mortonprecise'

    def __init__(self, lhs, rhs):
        super(MortonPreciseSearchMatchedLookup, self).__init__(lhs, rhs)

    def get_rhs_op(self, connection, rhs):
        return connection.operators['startswith'] % rhs

    def process_rhs(self, qn, connection):
        rhs, params = super(MortonPreciseSearchMatchedLookup, self).process_rhs(qn, connection)
        if params and not self.bilateral_transforms:
            params[0] = "%s%%" % connection.ops.prep_for_like_query(params[0])
        return rhs, params
