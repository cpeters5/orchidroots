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
    lines = [
        "User-Agent: *",
        "Disallow: /accounts/",
        "Disallow: /core/",
        "Disallow: /documents/",
        "Disallow: /detail/ancestor/",
        "Disallow: /documents/",
        "Disallow: /donations/",
        "Disallow: /other/",
        "Disallow: /search/",
        "Disallow: /orchidaceae/",
        "Disallow: /utils/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def orchid_home(request):
    randgenus = Genus.objects.exclude(status='synonym').extra(where=["num_spc_with_image + num_hyb_with_image > 0"]
                                                              ).values_list('pid', flat=True).order_by('?')
    # Number of visits to this view, as counted in the session variable.
    # num_visits = request.session.get('num_visits', 0)
    # request.session['num_visits'] = num_visits + 1
    randimages = []
    for e in randgenus:
        if len(randimages) >= num_img:
            break
        if SpcImages.objects.filter(gen=e):
            img = SpcImages.objects.filter(gen=e).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?'
                                                                                                 )[0:1]
            if img and len(img):
                randimages.append(img[0])

    random.shuffle(randimages)
    role = getRole(request)
    context = {'title': 'orchid_home', 'role': role, 'randimages': randimages, 'level': 'detail', 'tab': 'sum', }
    return render(request, 'orchid_home.html', context)


def home(request):
    randgenus = Genus.objects.exclude(status='synonym').extra(where=["num_spc_with_image + num_hyb_with_image > 0"]
                                                              ).values_list('pid', flat=True).order_by('?')
    # Number of visits to this view, as counted in the session variable.
    # num_visits = request.session.get('num_visits', 0)
    # request.session['num_visits'] = num_visits + 1
    randimages = []
    for e in randgenus:
        if len(randimages) >= num_img:
            break
        if SpcImages.objects.filter(gen=e):
            img = SpcImages.objects.filter(gen=e).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?'
                                                                                                 )[0:1]
            if img and len(img):
                randimages.append(img[0])

    random.shuffle(randimages)
    role = getRole(request)
    context = {'title': 'orchid_home', 'role': role, 'randimages': randimages, 'level': 'detail', 'tab': 'sum', }
    return render(request, 'home.html', context)


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


