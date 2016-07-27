# -*- coding: utf-8 -*-


#==============================================================================
# uniq
#==============================================================================
def uniq(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]
