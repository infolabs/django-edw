# -*- coding: utf-8 -*-
"""
Custom signals sent during the registration and activation processes.
"""
from django.dispatch import Signal


# A new customer has registered.
customer_registered = Signal(providing_args=["customer", "request"])

# A user has activated his or her account.
user_activated = Signal(providing_args=["user", "request"])
