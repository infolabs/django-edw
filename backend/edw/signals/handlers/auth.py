# -*- coding: utf-8 -*-
# from ..auth import customer_registered, user_activated
# from django.dispatch import receiver
#
# from edw.signals import make_dispatch_uid

#==============================================================================
# Auth event handlers
#==============================================================================
# @receiver(customer_registered, dispatch_uid=make_dispatch_uid(customer_registered, 'customer_registered_handler'))
# def customer_registered_handler(sender, **kwargs):
#     pass
#
# @receiver(user_activated, dispatch_uid=make_dispatch_uid(user_activated, 'user_activated_handler'))
# def user_activated_handler(sender, **kwargs):
#     pass