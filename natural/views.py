# -*- coding: utf8 -*-
from django.http import HttpResponse
redirect_message = "This page was decommissioned"

def acc_species(request, pid):
    return HttpResponse(redirect_message)


def hyb_species(request, pid):
    return HttpResponse(redirect_message)


def species(request, pid):
    return HttpResponse(redirect_message)


def family_tree (request,pid):
    return HttpResponse(redirect_message)


def browse(request):
    return HttpResponse(redirect_message)