from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime, timedelta
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.apps import apps
from utils.views import getRole
import random
import string
import logging
logger = logging.getLogger(__name__)

Genus = apps.get_model('orchidaceae', 'Genus')
Species = apps.get_model('orchidaceae', 'Species')
SpcImages = apps.get_model('orchidaceae', 'SpcImages')
HybImages = apps.get_model('orchidaceae', 'HybImages')
Comment = apps.get_model('orchidaceae', 'Comment')
num_img = 20


@require_GET
def robots_txt(request):
    # only allow access to common
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /account/",
        "Disallow: /bromeliaceae/",
        "Disallow: /cactaceae/",
        "Disallow: /core/",
        "Disallow: /documents/",
        "Disallow: /detail/",
        "Disallow: /documents/",
        "Disallow: /donations/",
        "Disallow: /orchidaceae/",
        "Disallow: /orchidlist/",
        "Disallow: /other/",
        "Disallow: /utils/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def dispatch(request):
    pid = ''
    send_url = ''
    role = getRole(request)
    if 'pid' in request.GET:
        pid = request.GET['pid']
    if 'family' in request.GET:
        family = request.GET['family']
    if pid:
        species = Species
    if family == 'Orchidaceae':
        send_url = '/detail/information/' + str(pid) + '/'
    elif family == 'Bromeliaceae':
        send_url = '/bromeliaceae/advanced/?role=' + role
    logger.error("send_url = " + send_url + " - family = " + family)
    return HttpResponseRedirect(send_url)


def require_get(view_func):
    def wrap(request, *args, **kwargs):
        if request.method != "GET":
            return HttpResponseBadRequest("Expecting GET request")
        return view_func(request, *args, **kwargs)
    wrap.__doc__ = view_func.__doc__
    wrap.__dict__ = view_func.__dict__
    wrap.__name__ = view_func.__name__
    return wrap


