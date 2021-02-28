from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.apps import apps
from itertools import chain
from utils.views import write_output
from myproject import config
# from myproject import config
import logging
import random
import string
import re


# import django.shortcuts
from utils.views import write_output
from detail.views import getRole

# Create your views here.
alpha_list = config.alpha_list
logger = logging.getLogger(__name__)

from orchidaceae.models import Genus, GenusRelation, Intragen, Species, Hybrid, Accepted, Synonym,\
    Distribution, SpcImages, HybImages, UploadFile, AncestorDescendant, Subgenus, Section, Subsection, Series
from .models import Family, Subfamily, Tribe, Subtribe, Region, SubRegion, LocalRegion

User = get_user_model()

# High level lists
def family(request):
    # -- List Genuses
    family_list = Family.objects.order_by('family')
    context = {'family_list': family_list, 'alpha_list': alpha_list, 'title': 'families', }
    return render(request, 'core/family.html', context)


def subfamily(request):
    # -- List Genuses
    f = ''
    if 'f' in request.GET:
        f = request.GET['f']
    subfamily_list = Subfamily.objects.filter(family=f).order_by('subfamily')
    context = {'subfamily_list': subfamily_list, 'alpha_list': alpha_list, 'title': 'subfamilies', 'f': f}
    return render(request, 'core/subfamily.html', context)


def tribe(request):
    f, sf = '', ''
    if 'f' in request.GET:
        f = request.GET['f']
    subfamily_list = Subfamily.objects.filter(family=f)
    tribe_list = Tribe.objects.order_by('tribe').filter(family=f)
    if 'sf' in request.GET:
        sf = request.GET['sf']
        if sf:
            sf_obj = Subfamily.objects.get(pk=sf)
            if sf_obj:
                tribe_list = tribe_list.filter(subfamily=sf)
    context = {'tribe_list': tribe_list, 'title': 'tribes', 'f': f, 'sf': sf, 'subfamily_list': subfamily_list, }
    return render(request, 'core/tribe.html', context)


def subtribe(request):
    f, sf, t = '', '', ''
    if 'f' in request.GET:
        f = request.GET['f']
    subfamily_list = Subfamily.objects.filter(family=f)
    tribe_list = Tribe.objects.order_by('tribe').filter(family=f)
    subtribe_list = Subtribe.objects.filter(family=f).order_by('subtribe')
    if 'sf' in request.GET:
        sf = request.GET['sf']
        if sf:
            sf_obj = Subfamily.objects.get(pk=sf)
            if sf_obj:
                subtribe_list = subtribe_list.filter(subfamily=sf)
    if 't' in request.GET:
        t = request.GET['t']
        if t:
            t_obj = Tribe.objects.get(pk=t)
            if t_obj:
                subtribe_list = subtribe_list.filter(tribe=t)

    context = {'subtribe_list': subtribe_list, 'title': 'subtribes', 'f': f, 't': t, 'sf': sf,
               'subfamily_list': subfamily_list, 'tribe_list': tribe_list, }
    return render(request, 'core/subtribe.html', context)

