# -*- coding: utf-8 -*-
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from edw.signals import make_dispatch_uid
