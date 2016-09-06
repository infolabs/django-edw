# -*- coding: utf-8 -*-
from django.shortcuts import render


def index(request):
    return render(request, "todos/index.html")

def registration(request):
    return render(request, "todos/registration.html")