import string
import re
import pytz
import logging

import django.shortcuts
import random
import os
import shutil
import json

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
# from django.contrib.auth.models import User, Group
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from django import template
from django.conf import settings
from PIL import Image
from PIL import ExifTags
from io import BytesIO
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.template import RequestContext
from itertools import chain

from django.utils import timezone
from datetime import datetime, timedelta
from utils.views import write_output

# import pytz
# MPTT stuff
# from django.views.generic.list_detail import object_list
from .forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm
from accounts.models import User, Profile
# from orchidaceae.views import mypaginator


from django.apps import apps
Family = apps.get_model('core', 'Family')
Subfamily = apps.get_model('core', 'Subfamily')
Tribe = apps.get_model('core', 'Tribe')
Subtribe = apps.get_model('core', 'Subtribe')
Region = apps.get_model('core', 'Region')
Subregion = apps.get_model('core', 'Subregion')

Genus = apps.get_model('orchidaceae', 'Genus')
GenusRelation = apps.get_model('orchidaceae', 'GenusRelation')
Intragen = apps.get_model('orchidaceae', 'Intragen')
Species = apps.get_model('orchidaceae', 'Species')
Hybrid = apps.get_model('orchidaceae', 'Hybrid')
Accepted = apps.get_model('orchidaceae', 'Accepted')
Synonym = apps.get_model('orchidaceae', 'Synonym')
Comment = apps.get_model('orchidaceae', 'Comment')

Subgenus = apps.get_model('orchidaceae', 'Subgenus')
Section = apps.get_model('orchidaceae', 'Section')
Subsection = apps.get_model('orchidaceae', 'Subsection')
Series = apps.get_model('orchidaceae', 'Series')
Distribution = apps.get_model('orchidaceae', 'Distribution')
SpcImages = apps.get_model('orchidaceae', 'SpcImages')
HybImages = apps.get_model('orchidaceae', 'HybImages')
UploadFile = apps.get_model('orchidaceae', 'UploadFile')
SpcImgHistory = apps.get_model('orchidaceae', 'SpcImgHistory')
HybImgHistory = apps.get_model('orchidaceae', 'HybImgHistory')
Photographer = apps.get_model('accounts', 'Photographer')
AncestorDescendant = apps.get_model('orchidaceae', 'AncestorDescendant')
ReidentifyHistory = apps.get_model('orchidaceae', 'ReidentifyHistory')
MAX_HYB = 500
imgdir = 'utils/images/'
hybdir = imgdir + 'hybrid/'
spcdir = imgdir + 'species/'
list_length = 1000  # Length of species_list and hybrid__list in hte navbar
logger = logging.getLogger(__name__)

# Redirect to list or browse if species/hybrid does not exist.
# TODO: Create a page for this
redirect_message = "<br><br>Species does not exist! <br>You may try <a href='/orchidaceae/species/'>" \
                   "search species list</a> or <a href='/orchidaceae/browsegen/?type=species'>browse species images.</a>"


@login_required
# Curator only - role = cur
def createhybrid(request):
    genus1 = genus2 = species1 = species2 = ''
    if 'pid1' in request.GET:
        pid1 = request.GET['pid1']
        try:
            species1 = Species.objects.get(pk=pid1)
        except Species.DoesNotExist:
            return HttpResponse(redirect_message)
        if species1.status == 'synonym':
            species1 = species1.getAccepted()

        if 'pid2' in request.GET:
            pid2 = request.GET['pid2']
            try:
                species2 = Species.objects.get(pk=pid2)
            except Species.DoesNotExist:
                return HttpResponse(redirect_message)
        else:
            species2 = ''

        if species2.status == 'synonym':
            species2 = species2.getAccepted()

        spc1 = species1.species
        if species1.infraspe:
            spc1 += ' ' + species1.infraspe
        spc2 = species2.species
        if species2.infraspe:
            spc2 += ' ' + species2.infraspe
    else:
        return HttpResponse(redirect_message)

    if 'role' in request.GET:
        role = request.GET['role']
    else:
        # Only curator can create for now. Later, may open to private users
        role = 'cur'
    if not role or role != 'cur':
        send_url = '/detail/compare/?pid=' + str(pid1)
        return HttpResponseRedirect(send_url)

    import datetime
    # Now create the new species objects
    # # Get nothogenus
    # # First, find all genus ancestors of both
    gen1 = species1.gen.pid
    gen2 = species2.gen.pid
    parent1 = GenusRelation.objects.get(gen=gen1)
    parent2 = GenusRelation.objects.get(gen=gen2)
    parentlist1 = parent1.get_parentlist()
    parentlist2 = parent2.get_parentlist()
    parentlist = parentlist1 + parentlist2
    parentlist = list(dict.fromkeys(parentlist))
    parentlist.sort()

    # Look for genus with this parent list
    result_list = GenusRelation.objects.all()
    genus = ''
    for x in result_list:
        a = x.get_parentlist()
        a.sort()
        if a == parentlist:
            genus = x.genus
            break
    if not genus:
        msgnogenus = "404"
        genus1 = species1.genus
        genus2 = species2.genus
        send_url = '/detail/compare/?pid=' + str(pid1) + '&msgnogenus=' + msgnogenus + '&genus1=' + genus1 + \
                   '&genus2=' + genus2 + '&species1=' + species1 + '&species2=' + species2
        return HttpResponseRedirect(send_url)
    # Create Species instance
    spcobj = Species()
    spcobj.genus = genus
    spcobj.species = spc1 + '-' + spc2
    spcobj.pid = Hybrid.objects.filter(pid__gt=900000000).filter(pid__lt=999999999).order_by('-pid')[0].pid_id + 1
    spcobj.source = 'INT'
    spcobj.type = 'hybrid'
    spcobj.status = 'nonregistered'
    datetime_obj = datetime.datetime.now()
    spcobj.year = datetime_obj.year
    spcobj.save()
    spcobj = Species.objects.get(pk=spcobj.pid)

    # Now create Hybrid instance
    hybobj = Hybrid()
    hybobj.pid = spcobj
    hybobj.seed_genus = species1.genus
    hybobj.pollen_genus = species2.genus
    hybobj.seed_species = spc1
    hybobj.pollen_species = spc2
    if species1.status == 'synonym':
        hybobj.seed_id = species1.getAccepted()
    else:
        hybobj.seed_id = species1
    if species2.status == 'synonym':
        hybobj.pollen_id = species2.getAccepted()
    else:
        hybobj.pollen_id = species2
    hybobj.save()
    if genus1 and genus2:
        write_output(request, str(genus1) + " " + str(species1) + " vs " + str(genus2) + " " + str(species2))
    else:
        write_output(request)
    return HttpResponseRedirect("/detail/" + str(spcobj.pid) + "/photos/?role=" + role + "&genus2=" + species2.genus)


# All access - at least role = pub
def compare(request, pid=None):
    # TODO:  Use Species form instead
    infraspr1 = infraspe1 = author1 = year1 = spc1 = gen1 = ''
    pid2 = species2 = genus2 = infraspr2 = infraspe2 = author2 = year2 = spc2 = gen2 = ''
    spcimg1_list = spcimg2_list = []
    role = 'pub'

    # Initial species
    if not pid and 'pid' in request.GET:
        pid = request.GET['pid']
        if pid:
            pid = int(pid)
        else:
            return HttpResponseRedirect("/")
    else:
        return HttpResponseRedirect("/")
    if pid > 0:
        try:
            species = Species.objects.get(pk=pid)
            pid = species.pid
            genus = species.genus
            species1 = species
        except Species.DoesNotExist:
            return HttpResponseRedirect("/")
    else:
        return HttpResponse("/")

    # Handfle request. Should use SpcForm instead.
    if 'species1' in request.GET:
        spc1 = request.GET['species1']
        spc1 = spc1.strip()
    if 'genus1' in request.GET:
        gen1 = request.GET['genus1']
        gen1 = gen1.strip()
    if 'infraspe1' in request.GET:
        infraspe1 = request.GET['infraspe1']
        infraspe1 = infraspe1.strip()
    if 'infraspr1' in request.GET:
        infraspr1 = request.GET['infraspr1']
        infraspr1 = infraspr1.strip()
    if 'author1' in request.GET:
        author1 = request.GET['author1']
        author1 = author1.strip()
    if 'year1' in request.GET:
        year1 = request.GET['year1']
        year1 = year1.strip()
        if year1:
            year1 = int(year1)

    if 'species2' in request.GET:
        spc2 = request.GET['species2']
        spc2 = spc2.strip()
    if 'genus2' in request.GET:
        gen2 = request.GET['genus2']
        gen2 = gen2.strip()
    if 'infraspe2' in request.GET:
        infraspe2 = request.GET['infraspe2']
        infraspe2 = infraspe2.strip()
    if 'infraspr2' in request.GET:
        infraspr2 = request.GET['infraspr2']
        infraspr2 = infraspr2.strip()
    if 'author2' in request.GET:
        author2 = request.GET['author2']
        author2 = author2.strip()
    if 'year2' in request.GET:
        year2 = request.GET['year2']
        if year2:
            year2 = year2.strip()

    if 'role' in request.GET:
        role = request.GET['role']

    if gen1:  # Request new genus1:
        try:
            genus1 = Genus.objects.get(genus__iexact=gen1)
            genus = genus1
        except Genus.DoesNotExist:
            # Fallback to initial species
            message = "genus, " + gen1 + ' does not exist'
            context = {'species': species, 'genus': genus, 'pid': pid,  # original
                       'genus1': species.genus, 'species1': species, 'infraspr1': infraspr1, 'infraspe1': infraspe1,
                       'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                       'message1': message,
                       'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
            return render(request, 'detail/compare.html', context)
        if spc1:
            species1 = Species.objects.filter(species__iexact=spc1).filter(genus__iexact=gen1)
            if infraspe1:
                species1 = species1.filter(infraspe=infraspe1).filter(infraspr=infraspr1)
            if author1:
                species1 = species1.filter(author=author1)
            if year1:
                species1 = species1.filter(year=year1)

            if len(species1) == 0:
                message = "species, <b>" + str(gen1) + ' ' + spc1 + '</b> does not exist'
                context = {'species': species, 'genus': genus, 'pid': pid,  # original
                           'genus1': species.genus, 'species1': species, 'infraspr1': infraspr1, 'infraspe1': infraspe1,
                           'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                           'message1': message,
                           'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
                return render(request, 'detail/compare.html', context)
            elif len(species1) > 1:
                if infraspe1 and infraspr1:
                    species1 = species1.filter(infraspe__icontains=infraspe1).filter(infraspr__icontains=infraspr1)
                else:
                    species1 = species1.filter(infraspe__isnull=True).filter(infraspr__isnull=True)
                if year1:
                    species1 = species1.filter(year=year1)
                if len(species1) == 1:  # Found unique species
                    species1 = species1[0]
                    species = species1
                    pid1 = species1.pid
                    pid = ''
                elif len(species1) > 1:  # MULTIPLE SPECIES RETURNED
                    message = "species, <b>" + str(gen1) + ' ' + spc1 + '</b> returns more than one values'
                    context = {'species': species, 'genus': genus, 'pid': pid,  # original
                               'genus1': species.genus, 'species1': species, 'infraspr1': infraspr1,
                               'infraspe1': infraspe1,
                               'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                               'message1': message,
                               'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
                    return render(request, 'detail/compare.html', context)
                else:  # length = 0  This could be a synonym
                    message = "species, <b>" + str(gen1) + ' ' + spc1 + '</b> returned none'
                    context = {'species': species, 'genus': genus, 'pid': pid,  # original
                               'genus1': species.genus, 'species1': species, 'infraspr1': infraspr1,
                               'infraspe1': infraspe1,
                               'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                               'message1': message,
                               'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
                    return render(request, 'detail/compare.html', context)
            else:  # Unique species found
                species1 = species1[0]
                species = species1
                pid1 = species1.pid
                pid = ''
        else:
            pid1 = ''
    else:
        # species 1 was not requested. use initial species
        genus1 = species.genus
        species1 = species
        pid1 = pid

    if not genus1 and not species1 and not genus2 and not species2 and not pid1 and not pid2:
        send_url = "/detail/photos/" + str(species.pid) + "/?role=cur"
        return HttpResponseRedirect(send_url)

    if species1:
        # logger.error("species = " + str(species1) + " - pid = " + str(pid1))
        if species1.type == 'species':
            spcimg1_list = SpcImages.objects.filter(pid=pid1).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]
        else:
            spcimg1_list = HybImages.objects.filter(pid=pid1).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]
    if gen2:
        try:
            genus2 = Genus.objects.get(genus__iexact=gen2)
        except Genus.DoesNotExist:
            # Fallback to initial species
            message = "genus <b>" + gen2 + '</b> does not exist'
            context = {'species1': species1, 'genus1': genus1,
                       'pid1': species1.pid,
                       'spcimg1_list': spcimg1_list,
                       'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                       'message2': message,
                       'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
            return render(request, 'detail/compare.html', context)
        if spc2:
            species2 = Species.objects.filter(species__iexact=spc2).filter(genus__iexact=gen2)
            if len(species2) == 0:
                message = "species, <b>" + str(gen2) + ' ' + spc2 + '</b> does not exist'
                context = {'species': species, 'genus': genus, 'pid': pid,  # original
                           'genus1': species1.genus, 'species1': species1, 'spcimg1_list': spcimg1_list,
                           'genus2': gen2, 'species2': spc2,
                           'message2': message,
                           'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
                return render(request, 'detail/compare.html', context)
            elif len(species2) > 1:
                if infraspe2 and infraspr2:
                    species2 = species2.filter(infraspe__icontains=infraspe2).filter(infraspr__icontains=infraspr2)
                else:
                    species2 = species2.filter(infraspe__isnull=True).filter(infraspr__isnull=True)
                if year2:
                    species2 = species2.filter(year=year2)
                if author2:
                    species2 = species2.filter(author=author2)

                if len(species2) == 1:  # Found unique species
                    species2 = species2[0]
                    pid2 = species2.pid
                elif len(species2) > 1:  # MULTIPLE SPECIES RETURNED
                    message = "species, <b>" + str(gen2) + ' ' + spc2 + '</b> returns more than one value'
                    context = {'species': species, 'genus': genus, 'pid': pid,  # original
                               'genus1': species.genus, 'species1': species, 'infraspr1': infraspr1,
                               'infraspe1': infraspe1,
                               'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                               'message2': message,
                               'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
                    return render(request, 'detail/compare.html', context)
                else:  # length = 0
                    message = "species, <b>" + str(gen2) + ' ' + spc2 + '</b> returned none'
                    context = {'species': species, 'genus': genus, 'pid': pid,  # original
                               'genus1': species.genus, 'species1': species, 'infraspr1': infraspr1,
                               'infraspe1': infraspe1,
                               'genus2': genus, 'species2': species2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                               'message1': message,
                               'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
                    return render(request, 'detail/compare.html', context)
            else:
                species2 = species2[0]
                pid2 = species2.pid
        else:
            pid2 = ''

    cross = ''
    message1 = message2 = accepted1 = accepted2 = ''

    if species1 and species1.status == 'synonym':
        pid1 = species1.getAcc()
        accepted1 = species1.getAccepted()
    if species2 and species2.status == 'synonym':
        pid2 = species2.getAcc()
        accepted2 = species2.getAccepted()

    if pid1 and pid2:
        cross = Hybrid.objects.filter(seed_id=pid1).filter(pollen_id=pid2)
        if not cross:
            cross = Hybrid.objects.filter(seed_id=pid2).filter(pollen_id=pid1)
        if cross:
            cross = cross[0]
        else:
            cross = ''

    if species1:
        if species1.type == 'species':
            spcimg1_list = SpcImages.objects.filter(pid=pid1).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]
        else:
            spcimg1_list = HybImages.objects.filter(pid=pid1).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]

    if species2:
        if species2.type == 'species':
            spcimg2_list = SpcImages.objects.filter(pid=pid2).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]
        else:
            spcimg2_list = HybImages.objects.filter(pid=pid2).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]

    msgnogenus = ''
    if 'msgnogenus' in request.GET:
        msgnogenus = request.GET['msgnogenus']

    write_output(request, str(genus1) + " " + str(species1) + " vs " + str(genus2) + " " + str(species2))
    context = {'pid': pid, 'genus': genus, 'species': species,
               'pid1': pid1, 'pid2': pid2, 'accepted1': accepted1, 'accepted2': accepted2,  # pid of accepted species
               'genus1': genus1, 'species1': species1, 'spcimg1_list': spcimg1_list,
               'genus2': genus2, 'species2': species2, 'spcimg2_list': spcimg2_list,
               'cross': cross,
               'msgnogenus': msgnogenus, 'message1': message1, 'message2': message2,
               'title': 'compare', 'tab': 'sbs', 'sbs': 'active', 'role': role}
    return render(request, 'detail/compare.html', context)


# Curator only - role = cur
@login_required
def rank_update(request, species):
    rank = 0
    if 'rank' in request.GET:
        rank = request.GET['rank']
        rank = int(rank)
        if 'id' in request.GET:
            orid = request.GET['id']
            orid = int(orid)
            image = ''
            if species.type == 'species':
                try:
                    image = SpcImages.objects.get(pk=orid)
                except SpcImages.DoesNotExist:
                    return 0
                # acc = Accepted.objects.get(pk=pid)
            elif species.type == 'hybrid':
                try:
                    image = HybImages.objects.get(pk=orid)
                except HybImages.DoesNotExist:
                    return 0
            image.rank = rank
            image.save()
    return rank


@login_required
def quality_update(request, species):
    if request.user.tier.tier > 2 and 'quality' in request.GET:
        quality = request.GET['quality']
        quality = int(quality)
        if 'id' in request.GET:
            orid = request.GET['id']
            orid = int(orid)
            image = ''
            if species.type == 'species':
                try:
                    image = SpcImages.objects.get(pk=orid)
                except SpcImages.DoesNotExist:
                    return 3
            elif species.type == 'hybrid':
                try:
                    image = HybImages.objects.get(pk=orid)
                except HybImages.DoesNotExist:
                    return 3
            image.quality = quality
            image.save()
    # return quality


def getRole(request):
    if request.user.is_authenticated:
        if request.user.tier.tier < 2:
            role = 'pub'
        elif request.user.tier.tier == 2:
            role = 'pri'
        else:
            role = 'cur'
        if 'role' in request.GET:
            role = request.GET['role']
        return role


def ancestor(request, pid=None):
    if not pid:
        if 'pid' in request.GET:
            pid = request.GET['pid']
            pid = int(pid)
        else:
            pid = 0

    role = getRole(request)
    if 'role' in request.GET:
        role = request.GET['role']
    sort = ''
    prev_sort = ''
    state = ''
    if request.GET.get('state'):
        state = request.GET['state']
        sort.lower()

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    genus = species.gen

    if request.GET.get('sort'):
        sort = request.GET['sort']
        sort.lower()
    if sort:
        if request.GET.get('prev_sort'):
            prev_sort = request.GET['prev_sort']
        if prev_sort == sort:
            if sort.find('-', 0) >= 0:
                sort = sort.replace('-', '')
            else:
                sort = '-' + sort
        else:
            # sort = '-' + sort
            prev_sort = sort
    # List of ancestors in the left panel
    anc_list = AncestorDescendant.objects.filter(did=pid)

    if sort:
        if sort == 'pct':
            anc_list = anc_list.order_by('-pct')
        elif sort == '-pct':
            anc_list = anc_list.order_by('pct')
        elif sort == 'img':
            anc_list = anc_list.order_by('-aid__num_image')
        elif sort == '-img':
            anc_list = anc_list.order_by('aid__num_image')
        elif sort == 'name':
            anc_list = anc_list.order_by('aid__genus', 'aid__species')
        elif sort == '-name':
            anc_list = anc_list.order_by('-aid__genus', '-aid__species')

    for x in anc_list:
        x.anctype = "orchidaceae:" + x.anctype

    context = {'species': species, 'anc_list': anc_list,
               'genus': genus,
               'anc': 'active',
               'sort': sort, 'prev_sort': prev_sort,
               'level': 'detail', 'title': 'ancestor', 'role': role, 'namespace': 'detail', 'state': state,
               }
    write_output(request, species.textname())
    return render(request, 'detail/ancestor.html', context)


# All access - at least role = pub
def ancestrytree(request, pid=None):
    if not pid and 'pid' in request.GET:
        pid = request.GET['pid']
        pid = int(pid)
    else:
        pid = 0

    role = getRole(request)
    if 'role' in request.GET:
        role = request.GET['role']

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    hybrid = species
    s = p = ss = sp = ps = pp = sss = ssp = sps = spp = pss = psp = pps = ppp = ssss = sssp = ssps = sspp = spss =\
        spsp = spps = sppp = psss = pssp = psps = pspp = ppss = ppsp = ppps = pppp = None
    spc = ''

    if species.type == 'hybrid':
        hybrid.img = hybdir + get_random_img(hybrid)

        if species.hybrid.seed_id and species.hybrid.seed_id.type == 'species':
            s = Accepted.objects.get(pk=species.hybrid.seed_id)
            s.type = 'species'
            s.parent = 'seed'
            s.year = s.pid.year
            s.img = spcdir + get_random_img(s.pid)

            # tree_list = tree_list + (s,)
        elif species.hybrid.seed_id and species.hybrid.seed_id.type == 'hybrid':
            s = Hybrid.objects.get(pk=species.hybrid.seed_id)
            s.type = 'hybrid'
            s.parent = 'seed'
            s.year = s.pid.year
            img = s.pid.get_best_img()
            if img:
                s.img = hybdir + img.image_file
            else:
                s.img = imgdir + 'noimage_light.jpg'
            # tree_list = tree_list + (s,)
            # SS
            if s and s.seed_id and s.seed_id.type == 'species':
                ss = Accepted.objects.get(pk=s.seed_id)
                ss.type = 'species'
                ss.parent = 'seed'
                ss.year = ss.pid.year
                ss.img = spcdir + get_random_img(ss.pid)
                # tree_list = tree_list + (ss,)
            elif s.seed_id and s.seed_id.type == 'hybrid':
                ss = Hybrid.objects.get(pk=s.seed_id)
                ss.type = 'hybrid'
                ss.parent = 'seed'
                ss.year = s.pid.year
                ss.img = hybdir + get_random_img(ss.pid)
                # tree_list = tree_list + (ss,)
                # SSS
                if ss.seed_id and ss.seed_id.type == 'species':
                    sss = Accepted.objects.get(pk=ss.seed_id)
                    sss.type = 'species'
                    sss.parent = 'seed'
                    sss.year = sss.pid.year
                    sss.img = spcdir + get_random_img(sss.pid)
                    # tree_list = tree_list + (sss,)
                elif ss.seed_id and ss.seed_id.type == 'hybrid':
                    sss = Hybrid.objects.get(pk=ss.seed_id)
                    sss.type = 'hybrid'
                    sss.parent = 'seed'
                    sss.year = sss.pid.year
                    sss.img = hybdir + get_random_img(sss.pid)
                else:
                    s = None
                # SSP
                if ss.pollen_id and ss.pollen_id.type == 'species':
                    ssp = Accepted.objects.get(pk=ss.pollen_id)
                    ssp.type = 'species'
                    ssp.parent = 'pollen'
                    ssp.year = ssp.pid.year
                    ssp.img = spcdir + get_random_img(ssp.pid)
                    # tree_list = tree_list + (ssp,)
                elif ss.pollen_id and ss.pollen_id.type == 'hybrid':
                    ssp = Hybrid.objects.get(pk=ss.pollen_id)
                    ssp.type = 'hybrid'
                    ssp.parent = 'pollen'
                    ssp.year = ssp.pid.year
                    ssp.img = hybdir + get_random_img(ssp.pid)
                    # tree_list = tree_list + (ssp,)
                    # SSPS

            if s and s.pollen_id and s.pollen_id.type == 'species':
                sp = Accepted.objects.get(pk=s.pollen_id)
                sp.type = 'species'
                sp.parent = 'pollen'
                sp.year = sp.pid.year
                sp.img = spcdir + get_random_img(sp.pid)
                # tree_list = tree_list + (sp,)
            elif s and s.pollen_id and s.pollen_id.type == 'hybrid':
                sp = Hybrid.objects.get(pk=s.pollen_id)
                sp.type = 'hybrid'
                sp.parent = 'seed'
                sp.year = sp.pid.year
                sp.year = sp.pid.year
                sp.img = hybdir + get_random_img(sp.pid)
                # tree_list = tree_list + (sp,)
                if sp.seed_id and sp.seed_id.type == 'species':
                    sps = Accepted.objects.get(pk=sp.seed_id)
                    sps.type = 'species'
                    sps.year = sps.pid.year
                    sps.img = spcdir + get_random_img(sps.pid)
                    # tree_list = tree_list + (sps,)
                elif sp.seed_id and sp.seed_id.type == 'hybrid':
                    sps = Hybrid.objects.get(pk=sp.seed_id)
                    sps.type = 'hybrid'
                    sps.year = sps.pid.year
                    sps.img = hybdir + get_random_img(sps.pid)
                    # tree_list = tree_list + (sps,)

                if sp.pollen_id and sp.pollen_id.type == 'species':
                    spp = Accepted.objects.get(pk=sp.pollen_id)
                    spp.type = 'species'
                    spp.year = spp.pid.year
                    spp.img = spcdir + get_random_img(spp.pid)
                    # tree_list = tree_list + (spp,)
                elif sp.pollen_id and sp.pollen_id.type == 'hybrid':
                    spp = Hybrid.objects.get(pk=sp.pollen_id)
                    spp.type = 'hybrid'
                    spp.year = spp.pid.year
                    spp.img = hybdir + get_random_img(spp.pid)
                    # tree_list = tree_list + (spp,)
            # else:
            #     s = ''
        # P - pollenparent
        if species.hybrid.pollen_id and species.hybrid.pollen_id.type == 'species':
            p = Accepted.objects.get(pk=species.hybrid.pollen_id)
            p.type = p.pid.type
            p.parent = 'pollen'
            p.year = p.pid.year
            p.img = spcdir + get_random_img(p.pid)
            # tree_list = tree_list + (s,)
        elif species.hybrid.pollen_id and species.hybrid.pollen_id.type == 'hybrid':
            p = Hybrid.objects.get(pk=species.hybrid.pollen_id)
            p.type = 'hybrid'
            p.parent = 'pollen'
            p.year = p.pid.year
            p.img = hybdir + get_random_img(p.pid)
            # tree_list = tree_list + (s,)
            # SS
            if p.seed_id and p.seed_id.type == 'species':
                ps = Accepted.objects.get(pk=p.seed_id)
                ps.type = 'species'
                ps.parent = 'seed'
                ps.year = ps.pid.year
                ps.img = spcdir + get_random_img(ps.pid)
                # tree_list = tree_list + (ss,)
            elif p.seed_id and p.seed_id.type == 'hybrid':
                ps = Hybrid.objects.get(pk=p.seed_id)
                ps.type = 'hybrid'
                ps.parent = 'seed'
                ps.year = ps.pid.year
                ps.img = hybdir + get_random_img(ps.pid)
                # tree_list = tree_list + (ss,)
                # SSS
                if ps.seed_id and ps.seed_id.type == 'species':
                    pss = Accepted.objects.get(pk=ps.seed_id)
                    pss.type = 'species'
                    pss.parent = 'seed'
                    pss.year = pss.pid.year
                    pss.img = spcdir + get_random_img(pss.pid)
                    # tree_list = tree_list + (sss,)
                elif ps.seed_id and ps.seed_id.type == 'hybrid':
                    pss = Hybrid.objects.get(pk=ps.seed_id)
                    pss.type = 'hybrid'
                    pss.parent = 'seed'
                    pss.year = pss.pid.year
                    pss.img = hybdir + get_random_img(pss.pid)
                    # tree_list = tree_list + (sss,)
                    # SSSS
                # SSP
                if ps.pollen_id and ps.pollen_id.type == 'species':
                    psp = Accepted.objects.get(pk=ps.pollen_id)
                    psp.type = 'species'
                    psp.parent = 'pollen'
                    psp.year = psp.pid.year
                    psp.img = spcdir + get_random_img(psp.pid)
                    # tree_list = tree_list + (ssp,)
                elif ps.pollen_id and ps.pollen_id.type == 'hybrid':
                    psp = Hybrid.objects.get(pk=ps.pollen_id)
                    psp.type = 'hybrid'
                    psp.parent = 'pollen'
                    psp.year = psp.pid.year
                    psp.img = hybdir + get_random_img(psp.pid)
            # -- SP
            if p.pollen_id and p.pollen_id.type == 'species':
                pp = Accepted.objects.get(pk=p.pollen_id)
                pp.type = 'species'
                pp.parent = 'pollen'
                pp.year = pp.pid.year
                pp.img = spcdir + get_random_img(pp.pid)
                # tree_list = tree_list + (sp,)
            elif p.pollen_id and p.pollen_id.type == 'hybrid':
                pp = Hybrid.objects.get(pk=p.pollen_id)
                pp.type = 'hybrid'
                pp.parent = 'pollen'
                pp.year = pp.pid.year
                pp.img = hybdir + get_random_img(pp.pid)
                # tree_list = tree_list + (sp,)
                if pp.seed_id and pp.seed_id.type == 'species':
                    pps = Accepted.objects.get(pk=pp.seed_id)
                    pps.type = 'species'
                    pps.img = spcdir + get_random_img(pps.pid)
                    pps.parent = 'seed'
                    pps.year = pps.pid.year
                    # tree_list = tree_list + (sps,)
                elif pp.seed_id and pp.seed_id.type == 'hybrid':
                    pps = Hybrid.objects.get(pk=pp.seed_id)
                    pps.type = 'hybrid'
                    pps.img = hybdir + get_random_img(pps.pid)
                    pps.parent = 'seed'
                    pps.year = pps.pid.year
                    # tree_list = tree_list + (sps,)
                if pp.pollen_id and pp.pollen_id.type == 'species':
                    ppp = Accepted.objects.get(pk=pp.pollen_id)
                    ppp.type = 'species'
                    ppp.img = spcdir + get_random_img(ppp.pid)
                    ppp.parent = 'pollen'
                    ppp.year = ppp.pid.year
                    # tree_list = tree_list + (spp,)
                elif pp.pollen_id and pp.pollen_id.type == 'hybrid':
                    ppp = Hybrid.objects.get(pk=pp.pollen_id)
                    ppp.type = 'hybrid'
                    ppp.img = hybdir + get_random_img(ppp.pid)
                    ppp.parent = 'pollen'
                    ppp.year = ppp.pid.year
                    # tree_list = tree_list + (spp,)

    context = {'species': species,
               'spc': spc, 'tree': 'active',
               's': s, 'ss': ss, 'sp': sp, 'sss': sss, 'ssp': ssp, 'sps': sps, 'spp': spp,
               'ssss': ssss, 'sssp': sssp, 'ssps': ssps, 'sspp': sspp, 'spss': spss, 'spsp': spsp, 'spps': spps,
               'sppp': sppp,
               'p': p, 'ps': ps, 'pp': pp, 'pss': pss, 'psp': psp, 'pps': pps, 'ppp': ppp,
               'psss': psss, 'pssp': pssp, 'psps': psps, 'pspp': pspp, 'ppss': ppss, 'ppsp': ppsp, 'ppps': ppps,
               'pppp': pppp,
               'level': 'detail', 'title': 'ancestrytree', 'role': role, 'namespace': 'detail',
               }
    write_output(request, species.textname())
    return render(request, 'detail/ancestrytree.html', context)


def comment(request):
    from string import digits
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/accounts/login/')
        else:
            species = Species.objects.get(pid=request.POST['pid'])
            comm = Comment()
            comm.user = request.user
            comm.type = species.type  # request.POST['type']
            comm.pid = species
            # comm.species = species
            comm.memo = request.POST['memo']
            comm.reason = request.POST['reason']
            send_url = '/detail/' + str(species.pid) + "/" + species.type
            if len(comm.memo.lstrip(digits).strip()) == 0:
                return HttpResponseRedirect(send_url)

            orid = 0
            if 'id' in request.POST:
                orid = request.POST['id']
                if orid:
                    orid = int(orid)
                else:
                    orid = 0

            # If this comment is a misident report, update quality
            if orid > 0:
                comm.id_list = orid
                orid = int(orid)
                if species.type == 'species':
                    obj = SpcImages.objects.get(pk=orid)
                else:
                    obj = HybImages.objects.get(pk=orid)

                if comm.reason == "report" and obj.quality != 'CH':
                    obj.quality = 'CH'  # misident report
                    obj.save(update_fields=['quality'])

            comm.save()
            return HttpResponseRedirect(send_url)
    else:
        return HttpResponseRedirect('/')


def is_int(s):
    try:
        int(s)
    except ValueError:
        return False
    return True


def requestlog(request, pid=None):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    print(request)

    if pid:
        logger.error(">>> pid = " + str(pid))
    # logger.error(">>> method = " + request.method)
    logger.error(">>> ip = " + ip + " - user = " + str(request.user) + " - url = " + request.build_absolute_uri())


def information(request, pid=None):
    distribution_list = ()
    ps_list = pp_list = ss_list = sp_list = seedimg_list = pollimg_list = ()
    role = getRole(request)
    if not pid and 'pid' in request.GET:
        pid = request.GET['pid']

    if not pid or not is_int(pid):
        # requestlog(request, pid)
        return HttpResponseRedirect('/')

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')
    genus = species.gen

    if species.status == 'pending':
        return HttpResponseRedirect('/')
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=species.pid)
        return HttpResponseRedirect("/detail/information/?pid=" + str(synonym.acc_id) + "&role=" + role)

    display_items = []
    synonym_list = Synonym.objects.filter(acc=pid).order_by('sgenus', 'sspecies')
    if pid and species.type == 'species':
        accepted = species.accepted
        images_list = SpcImages.objects.filter(pid=species.pid).order_by('-rank', 'quality', '?')
        distribution_list = Distribution.objects.filter(pid=species.pid)
    else:
        accepted = species.hybrid
        images_list = HybImages.objects.filter(pid=species.pid).order_by('-rank', 'quality', '?')

    if images_list:
        i_1, i_2, i_3, i_4, i_5, i_7, i_8 = 0, 0, 0, 0, 0, 0, 0
        for x in images_list:
            if x.rank == 1 and i_1 <= 0:
                i_1 += 1
                display_items.append(x)
            elif x.rank == 2 and i_2 <= 0:
                i_2 += 1
                display_items.append(x)
            elif x.rank == 3 and i_3 <= 1:
                i_3 += 1
                display_items.append(x)
            elif x.rank == 4 and i_4 <= 3:
                i_4 += 1
                display_items.append(x)
            elif x.rank == 5 and i_5 <= 3:
                i_5 += 1
                display_items.append(x)
            elif x.rank == 7 and i_7 <= 2:
                i_7 += 1
                display_items.append(x)
            elif x.rank == 8 and i_8 < 2:
                i_8 += 1
                display_items.append(x)
    seed_list = Hybrid.objects.filter(seed_id=species.pid).order_by('pollen_genus', 'pollen_species')
    pollen_list = Hybrid.objects.filter(pollen_id=species.pid)
    # Remove duplicates. i.e. if both parents are synonym.
    temp_list = pollen_list
    for x in temp_list:
        if x.seed_status() == 'syn' and x.pollen_status() == 'syn':
            pollen_list = pollen_list.exclude(pid=x.pid_id)
    pollen_list = pollen_list.order_by('seed_genus', 'seed_species')
    offspring_list = chain(list(seed_list), list(pollen_list))
    offspring_test = chain(list(seed_list), list(pollen_list))
    offspring_count = len(seed_list) + len(pollen_list)
    if offspring_count > 5000:
        offspring_list = ()

    if species.type == 'hybrid':
        if accepted.seed_id and accepted.seed_id.type == 'species':
            seed_obj = Species.objects.get(pk=accepted.seed_id.pid)
            seedimg_list = SpcImages.objects.filter(pid=seed_obj.pid).filter(rank__lt=7). \
                               order_by('-rank', 'quality', '?')[0: 3]
        elif accepted.seed_id and accepted.seed_id.type == 'hybrid':
            seed_obj = Hybrid.objects.get(pk=accepted.seed_id)
            if seed_obj:
                seedimg_list = HybImages.objects.filter(pid=seed_obj.pid.pid).filter(rank__lt=7).order_by('-rank',
                                                                                                          'quality',
                                                                                                          '?')[0: 3]
                assert isinstance(seed_obj, object)
                if seed_obj.seed_id:
                    ss_type = seed_obj.seed_id.type
                    if ss_type == 'species':
                        ss_list = SpcImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).order_by(
                            '-rank', 'quality', '?')[: 1]
                    elif ss_type == 'hybrid':
                        ss_list = HybImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).order_by(
                            '-rank', 'quality', '?')[: 1]
                if seed_obj.pollen_id:
                    sp_type = seed_obj.pollen_id.type
                    if sp_type == 'species':
                        sp_list = SpcImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(
                            rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
                    elif sp_type == 'hybrid':
                        sp_list = HybImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(
                            rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
        # Pollen
        if accepted.pollen_id and accepted.pollen_id.type == 'species':
            pollen_obj = Species.objects.get(pk=accepted.pollen_id.pid)
            pollimg_list = SpcImages.objects.filter(pid=pollen_obj.pid).filter(rank__lt=7).order_by('-rank', 'quality',
                                                                                                    '?')[0: 3]
        elif accepted.pollen_id and accepted.pollen_id.type == 'hybrid':
            pollen_obj = Hybrid.objects.get(pk=accepted.pollen_id)
            pollimg_list = HybImages.objects.filter(pid=pollen_obj.pid.pid).filter(rank__lt=7). \
                               order_by('-rank', 'quality', '?')[0: 3]
            if pollen_obj.seed_id:
                ps_type = pollen_obj.seed_id.type
                if ps_type == 'species':
                    ps_list = SpcImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7). \
                                  order_by('-rank', 'quality', '?')[: 1]
                elif ps_type == 'hybrid':
                    ps_list = HybImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7). \
                                  order_by('-rank', 'quality', '?')[: 1]
            if pollen_obj.pollen_id:
                pp_type = pollen_obj.pollen_id.type
                if pp_type == 'species':
                    pp_list = SpcImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7). \
                                  order_by('-rank', 'quality', '?')[: 1]
                elif pp_type == 'hybrid':
                    pp_list = HybImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7). \
                                  order_by('-rank', 'quality', '?')[: 1]

    ancspc_list = AncestorDescendant.objects.filter(did=species.pid).filter(anctype='species').order_by('-pct')
    for x in ancspc_list:
        img = x.aid.get_best_img()
        if img:
            x.img = img.image_file

    context = {'pid': species.pid, 'species': species, 'synonym_list': synonym_list, 'accepted': accepted,
               'title': 'information', 'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus,
               'display_items': display_items, 'distribution_list': distribution_list,
               'ancspc_list': ancspc_list, 'offspring_list': offspring_list, 'offspring_count': offspring_count,
               'offspring_test': offspring_test, 'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'level': 'detail', 'role': role, 'namespace': 'detail',
               }
    return render(request, 'detail/information.html', context)


@login_required
def comments(request):
    # Handle sort
    sort = ''
    if request.GET.get('sort'):
        sort = request.GET['sort']
        sort.lower()

    from django.db.models import Max
    comment_list = []
    com_latest = Comment.objects.values('pid').annotate(latest=Max('created_date'))
    if sort == '-latest':
        com_latest = com_latest.order_by('-latest')
    elif sort == 'latest':
        com_latest = com_latest.order_by('latest')

    for i in com_latest:
        pid = i['pid']
        date = i['latest'].date()
        spc = Species.objects.get(pk=pid)
        com = Comment.objects.filter(pid=pid).order_by('-created_date')[0]
        memo = com.memo
        if len(memo) > 80:
            memo = memo[0: 80] + '...'
        send_url = '/detail/' + str(spc.pid) + '/' + spc.type + "_detail"

        item = [spc, date, memo, send_url]
        comment_list.append(item)

    if sort == '-name':
        comment_list.sort(key=lambda k: (k[0].name()), reverse=True)
    elif sort == 'name':
        comment_list.sort(key=lambda k: (k[0].name()))
    if 'role' in request.GET:
        role = request.GET['role']
    else:
        role = 'pub'

    write_output(request)
    context = {'comment_list': comment_list, 'sort': sort, 'role': role, 'namespace': 'detail', }
    return render(request, 'detail/comments.html', context)


# Return best image file for a species object
def get_random_img(spcobj):
    if spcobj.get_best_img():
        spcobj.img = spcobj.get_best_img().image_file
    else:
        spcobj.img = 'noimage_light.jpg'
    return spcobj.img


@login_required
def curate_newupload(request):
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')
    file_list = UploadFile.objects.all().order_by('-created_date')
    days = 7
    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)
    role = 'cur'

    write_output(request)
    context = {'file_list': page_list,
               'tab': 'upl', 'role': role, 'upl': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'level': 'detail', 'title': 'curate_newupload', 'section': 'Curator Corner', 'namespace': 'detail',
               }
    return render(request, 'detail/curate_newupload.html', context)


@login_required
def curate_pending(request):
    # This page is for curators to perform mass delete. It contains all rank 0 photos sorted by date reverse.
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')

    ortype = ''
    if 'type' in request.GET:
        ortype = request.GET['type']
    if not ortype:
        ortype = 'species'

    days = 7
    if 'days' in request.GET:
        days = int(request.GET['days'])
    if not days:
        days = 7

    if ortype == 'species':
        file_list = SpcImages.objects.filter(rank=0)
    else:
        file_list = HybImages.objects.filter(rank=0)

    if days:
        file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days))
    file_list = file_list.order_by('-created_date')

    num_show = 5
    page_length = 100
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)

    role = 'cur'
    if 'role' in request.GET:
        role = request.GET['role']
    write_output(request)
    title = 'curate_pending'
    context = {'file_list': page_list, 'type': ortype,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'level': 'detail', 'title': title, 'namespace': 'detail',
               }
    return render(request, 'detail/curate_pending.html', context)


@login_required
def curate_newapproved(request):
    # This page is for curators to perform mass delete. It contains all rank 0 photos sorted by date reverse.
    species = ''
    image = ''
    ortype = 'species'
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')
    if 'type' in request.GET:
        ortype = request.GET['type']
        # Request to change rank/quality
        if 'id' in request.GET:
            orid = int(request.GET['id'])
            if ortype == 'species':
                try:
                    image = SpcImages.objects.get(pk=orid)
                except SpcImages.DoesNotExist:
                    species = ''
            elif ortype == 'hybrid':
                try:
                    image = HybImages.objects.get(pk=orid)
                except HybImages.DoesNotExist:
                    species = ''
            else:
                species = ''
        if image:
            species = Species.objects.get(pk=image.pid_id)

    days = 3
    if 'days' in request.GET:
        days = int(request.GET['days'])
    if ortype == 'species':
        file_list = SpcImages.objects.filter(rank__gt=0).exclude(approved_by=request.user)
    else:
        file_list = HybImages.objects.filter(rank__gt=0).exclude(approved_by=request.user)

    if days:
        file_list = file_list.filter(created_date__gte=timezone.now() - timedelta(days=days))
    file_list = file_list.order_by('-created_date')
    if species:
        rank_update(request, species)
        quality_update(request, species)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)

    role = 'cur'
    if 'role' in request.GET:
        role = request.GET['role']
    write_output(request)
    context = {'file_list': page_list, 'type': ortype,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'level': 'detail', 'title': 'curate_newapproved', 'namespace': 'detail',
               }
    return render(request, 'detail/curate_newapproved.html', context)


@login_required
def curate(pid):
    try:
        species = Species.objects.get(pk=pid)
        send_url = "/detail/photos/" + str(species.pid) + "/?role=cur"
        return HttpResponseRedirect(send_url)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)


@login_required
def progeny(request, pid):
    if 'role' in request.GET:
        role = request.GET['role']
    else:
        role = 'pri'
    try:
        species = Species.objects.get(pk=pid)
        send_url = "/orchidaceae/progeny/" + str(species.pid) + "/?role=" + role
        return HttpResponseRedirect(send_url)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)


@login_required
def progenyimg(request, pid):
    if 'role' in request.GET:
        role = request.GET['role']
    else:
        role = 'pri'
    try:
        species = Species.objects.get(pk=pid)
        send_url = "/orchidaceae/progenyimg/" + str(species.pid) + "/?role=" + role
        return HttpResponseRedirect(send_url)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)


def photos(request, pid=None):
    author, author_list = get_author(request)
    if not pid and 'pid' in request.GET:
        pid = request.GET['pid']
        if pid:
            pid = int(pid)
        else:
            pid = 0
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)

    role = getRole(request)
    if 'role' in request.GET:
        role = request.GET['role']
    elif 'role' in request.POST:
        role = request.POST['role']

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    variety = ''
    tail = ''

    if species.type == 'species':
        all_list = SpcImages.objects.filter(pid=species.pid)
    else:
        all_list = HybImages.objects.filter(pid=species.pid)

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, species)

    if author:
        if role == 'pri':
            public_list = all_list.filter(Q(rank__gt=0) | Q(author=request.user.profile.current_credit_name_id))
            # Loggedin user in private mode can see owned photos only
        elif role == 'cur':
            # Loggedin user in curate mode can see all public photos and private photos in different section
            public_list = all_list.filter(rank__gt=0)
            private_list = all_list.filter(rank=0)
        else:  # Anonymous or pub role
            public_list = all_list.filter(rank__gt=0)

    else:  # anonymous
        public_list = all_list.filter(rank__gt=0)

    upload_list = UploadFile.objects.filter(pid=species.pid)
    if role != 'cur':
        if author:
            upload_list = upload_list.filter(author=author)

    rank_update(request, species)
    quality_update(request, species)
    # Handle Variety filter
    if 'variety' in request.GET:
        variety = request.GET['variety']
    if variety == 'semi alba':
        variety = 'semialba'

    # Extract first term, possibly an infraspecific
    parts = variety.split(' ', 1)
    if len(parts) > 1:
        tail = parts[1]
    var = variety
    if variety and tail:
        public_list = public_list.filter(Q(variation__icontains=var) | Q(form__icontains=var) | Q(name__icontains=var)
                                         | Q(source_file_name__icontains=var) | Q(description__icontains=var)
                                         | Q(variation__icontains=tail) | Q(form__icontains=tail)
                                         | Q(name__icontains=tail) | Q(source_file_name__icontains=tail)
                                         | Q(description__icontains=tail))
    elif variety:
        public_list = public_list.filter(Q(variation__icontains=var) | Q(form__icontains=var) | Q(name__icontains=var)
                                         | Q(source_file_name__icontains=var) | Q(description__icontains=var))

    if public_list:
        if var == "alba":
            public_list = public_list.exclude(variation__icontains="semi")
        public_list = public_list.order_by('-rank', 'quality', '?')
        if private_list:
            private_list = private_list.order_by('created_date')

    write_output(request, species.textname())
    if role == 'pri':
        author = Photographer.objects.get(user_id=request.user)
        if author:
            public_list = public_list.filter(author=author)
        context = {'species': species, 'author': author, 'author_list': author_list,
                   'variety': variety, 'pho': 'active', 'tab': 'pho',
                   'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list,
                   'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
                   'level': 'detail', 'role': role, 'title': 'photos', 'namespace': 'detail',
                   }

        return render(request, 'detail/myphoto.html', context)
    else:
        context = {'species': species, 'author': author, 'author_list': author_list,
                   'variety': variety, 'pho': 'active', 'tab': 'pho',
                   'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list,
                   'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
                   'level': 'detail', 'role': role, 'title': 'photos', 'namespace': 'detail',
                   }
        return render(request, 'detail/photos.html', context)


@login_required
def curateinfospc(request, pid):
    species = Species.objects.get(pk=pid)

    genus = species.genus
    accepted = Accepted.objects.get(pk=pid)

    tab = 'ins'
    if 'tab' in request.GET:
        tab = request.GET['tab']
    role = 'cur'
    if 'role' in request.GET:
        role = request.GET['role']

    distribution_list = Distribution.objects.filter(pid=species.pid)
    if request.method == 'POST':
        request.POST.get("role", role)
        form = AcceptedInfoForm(request.POST, instance=accepted)
        if form.is_valid():
            spc = form.save(commit=False)
            spc.pid = species

            # TODO: Put these in form.clean methods
            if spc.altitude:
                spc.altitude = spc.altitude.replace("\"", "\'\'")
                spc.altitude = spc.altitude.replace("\r", "<br>")
            if spc.description:
                spc.description = spc.description.replace("<br>", "")
                spc.description = spc.description.replace("\"", "\'\'")
                spc.description = spc.description.replace("\r", "<br>")
            if spc.culture:
                spc.culture = spc.culture.replace("<br>", "")
                spc.culture = spc.culture.replace("\"", "\'\'")
                spc.culture = spc.culture.replace("\r", "<br>")
            if spc.comment:
                spc.comment = spc.comment.replace("<br>\r", "\r")
                spc.comment = spc.comment.replace("\"", "\'\'")
                spc.comment = spc.comment.replace("\r", "<br>")
            if spc.history:
                spc.history = spc.culture.replace("<br>", "")
                spc.history = spc.history.replace("\"", "\'\'")
                spc.history = spc.history.replace("\r", "<br>")
            if spc.etymology:
                spc.etymology = spc.culture.replace("<br>", "")
                spc.etymology = spc.etymology.replace("\"", "\'\'")
                spc.etymology = spc.etymology.replace("\r", "<br>")
            spc.operator = request.user
            spc.save()

            url = "%s?pid=%s&role=%s" % (reverse('detail:information'), species.pid, role)
            return HttpResponseRedirect(url)
        else:
            return HttpResponse("POST: Somethign's wrong")
    else:
        accepted = Accepted.objects.get(pk=species.pid)
        form = AcceptedInfoForm(instance=accepted)
        context = {'form': form, 'genus': genus, 'species': species,
                   'title': 'curateinfo', 'tab': 'ins', tab: 'active', 'distribution_list': distribution_list,
                   'level': 'detail', 'role': role, 'namespace': 'detail', }
        return render(request, 'detail/curateinfospc.html', context)


@login_required
def curateinfohyb(request, pid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    genus = ''
    species = ''

    if pid:
        species = Species.objects.get(pk=pid)
        if species.status == 'synonym':
            synonym = Synonym.objects.get(pk=species.pid)
            species = Species.objects.get(pk=synonym.acc_id)
        genus = species.genus

        if species.type == 'species':
            url = "%s?tab=%s" % (reverse('detail:curateinfospc', args=(species.pid,)), 'info')
            return HttpResponseRedirect(url)

    tab = 'inh'
    if 'tab' in request.GET:
        tab = request.GET['tab']
    role = 'cur'
    if 'role' in request.GET:
        role = request.GET['role']

    hybrid = Hybrid.objects.get(pk=species.pid)
    if request.method == 'POST':
        request.POST.get("role", role)
        a = Hybrid.objects.get(pk=species.pid)
        b = Species.objects.get(pk=species.pid)
        form = HybridInfoForm(request.POST, instance=a)
        spcform = RenameSpeciesForm(request.POST, instance=b)
        if form.is_valid():
            spcspc = spcform.save(commit=False)
            spc = form.save(commit=False)
            spc.pid = species

            # TODO: Put these in form.clean_description etc...  method
            if spc.description:
                spc.description = spc.description.replace("<br>", "")
                spc.description = spc.description.replace("\"", "\'\'")
                spc.description = spc.description.replace("\r", "<br>")
            if spc.culture:
                spc.culture = spc.culture.replace("<br>", "")
                spc.culture = spc.culture.replace("\"", "\'\'")
                spc.culture = spc.culture.replace("\r", "<br>")
            if spc.comment:
                spc.comment = spc.comment.replace("<br>\r", "\r")
                spc.comment = spc.comment.replace("\"", "\'\'")
                spc.comment = spc.comment.replace("\r", "<br>")
            if spc.history:
                spc.history = spc.history.replace("<br>", "")
                spc.history = spc.history.replace("\"", "\'\'")
                spc.history = spc.history.replace("\r", "<br>")
            if spc.etymology:
                spc.etymology = spc.etymology.replace("<br>", "")
                spc.etymology = spc.etymology.replace("\"", "\'\'")
                spc.etymology = spc.etymology.replace("\r", "<br>")

            spcspc.save()
            spc.save()
            url = "%s?pid=%s&role=%s" % (reverse('detail:information'), species.pid, role)
            return HttpResponseRedirect(url)
        else:
            return HttpResponse("POST: Somethign's wrong")
    else:
        form = HybridInfoForm(instance=hybrid)
        spcform = RenameSpeciesForm(instance=species)

        context = {'form': form, 'spcform': spcform, 'genus': genus, 'species': species,
                   'tab': 'inh', tab: 'active', 'level': 'detail', 'title': 'curateinfo', 'role': role,
                   'namespace': 'detail', }
        return render(request, 'detail/curateinfohyb.html', context)


@login_required
def reidentify(request, orid, pid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')

    source_file_name = ''
    role = 'cur'
    if 'role' in request.GET:
        role = request.GET['role']
        if role != 'cur':
            url = "%s?role=%s" % (reverse('detail:photos', args=(pid,)), role)
            return HttpResponseRedirect(url)

    old_species = Species.objects.get(pk=pid)
    if old_species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        old_species = Species.objects.get(pk=pid)

    form = SpeciesForm(request.POST or None)
    if old_species.type == 'hybrid':
        old_img = HybImages.objects.get(pk=orid)
    elif old_species.type == 'species':
        old_img = SpcImages.objects.get(pk=orid)
    else:
        return HttpResponse("image id " + str(orid) + "does not exist")

    if request.method == 'POST':
        if form.is_valid():
            new_pid = form.cleaned_data.get('species')
            # logger.error(">>> Reidentify: from " + str(pid) + " to " + str(new_pid))
            try:
                new_species = Species.objects.get(pk=new_pid)
            except Species.DoesNotExist:
                url = "%s?role=%s" % (reverse('detail:photos', args=(pid,)), 'cur')
                return HttpResponseRedirect(url)

            # If re-idenbtified to same type
            if new_species.type == old_species.type:
                if new_species.type == 'species':
                    new_img = SpcImages.objects.get(pk=old_img.id)
                    new_img.pid = new_species.accepted
                else:
                    new_img = HybImages.objects.get(pk=old_img.id)
                    new_img.pid = new_species.hybrid
                hist = ReidentifyHistory(from_id=old_img.id, from_pid=old_species, to_pid=new_species,
                                         user_id=request.user, created_date=old_img.created_date)
                if source_file_name:
                    new_img.source_file_name = source_file_name
                new_img.pk = None
            else:
                if old_img.image_file:
                    if new_species.type == 'species':
                        new_img = SpcImages(pid=new_species.accepted)
                        from_path = "/webapps/static/utils/images/hybrid/" + old_img.image_file
                        to_path = "/webapps/static/utils/images/species/" + old_img.image_file
                    else:
                        new_img = HybImages(pid=new_species.hybrid)
                        from_path = "/webapps/static/utils/images/species/" + old_img.image_file
                        to_path = "/webapps/static/utils/images/hybrid/" + old_img.image_file
                    hist = ReidentifyHistory(from_id=old_img.id, from_pid=old_species, to_pid=new_species,
                                             user_id=request.user, created_date=old_img.created_date)
                    os.rename(from_path, to_path)
                else:
                    new_img = ''
                    hist = ''
                if source_file_name:
                    new_img.source_file_name = source_file_name
            if new_img:
                new_img.author = old_img.author
                new_img.pk = None
                new_img.source_url = old_img.source_url
                new_img.image_url = old_img.image_url
                new_img.image_file = old_img.image_file
                new_img.name = old_img.name
                new_img.awards = old_img.awards
                new_img.variation = old_img.variation
                new_img.form = old_img.form
                new_img.text_data = old_img.text_data
                new_img.description = old_img.description
                new_img.created_date = old_img.created_date
            # point to a new record
            # Who requested this change?
            new_img.user_id = request.user

            # ready to save
            new_img.save()
            hist.to_id = new_img.id
            hist.save()

            # Delete old record
            old_img.delete()

            write_output(request, old_species.textname() + " ==> " + new_species.textname())
            url = "%s?role=%s" % (reverse('detail:photos', args=(new_species.pid,)), role)
            return HttpResponseRedirect(url)
    context = {'form': form, 'species': old_species, 'img': old_img, 'role': 'cur', 'namespace': 'detail', }
    return render(request, 'detail/reidentify.html', context)


@login_required
def myphoto(request, pid):
    if request.user.tier.tier < 2:
        url = "%s?pid=%s&role=%s" % (reverse('detail:information'), pid, role)
        return HttpResponseRedirect(url)
    else:
        author, author_list = get_author(request)

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, species)
    author = Photographer.objects.get(user_id=request.user)
    if author:
        public_list = public_list.filter(author=author)
        private_list = private_list.filter(author=author)
    context = {'species': species, 'private_list': private_list, 'public_list': public_list, 'upload_list': upload_list,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list, 'author_list': author_list,
               'pri': 'active', 'role': 'pri', 'author': author,
               'level': 'detail', 'title': 'myphoto', 'namespace': 'detail',
               }
    write_output(request, str(species.textname()))
    return render(request, 'detail/myphoto.html', context)


@login_required
def myphoto_browse_spc(request):
    author, author_list = get_author(request)

    if request.user.tier.tier > 2 and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, '')

    my_full_list = []
    pid_list = SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct()

    img_list = Species.objects.filter(pid__in=pid_list)
    if img_list:
        img_list = img_list.order_by('genus', 'species')
        for x in img_list:
            img = x.get_best_img_by_author(request.user.photographer.author_id)
            if img:
                my_full_list.append(img)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, my_full_list, page_length, num_show)

    context = {'my_list': page_list, 'type': 'species',
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': 'pri', 'brwspc': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,
               'level': 'detail', 'title': 'myphoto_browse', 'namespace': 'detail',
               }
    write_output(request)
    return render(request, 'detail/myphoto_browse_spc.html', context)


@login_required
def myphoto_browse_hyb(request):
    if not request.user.is_authenticated or request.user.tier.tier < 2:
        send_url = "%s?tab=%s" % (reverse('orchidaceae:browse'), 'sum')
        return HttpResponseRedirect(send_url)
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')

    author, author_list = get_author(request)
    if request.user.tier.tier > 2 and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, '')

    my_full_list = []
    pid_list = HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct()

    img_list = Species.objects.filter(pid__in=pid_list)
    if img_list:
        img_list = img_list.order_by('genus', 'species')
        for x in img_list:
            img = x.get_best_img_by_author(request.user.photographer.author_id)
            if img:
                my_full_list.append(img)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, my_full_list, page_length, num_show)

    context = {'my_list': page_list, 'type': 'hybrid',
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': 'pri', 'brwhyb': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,
               'level': 'detail', 'title': 'myphoto_browse', 'namespace': 'detail',
               }
    write_output(request)
    return render(request, 'detail/myphoto_browse_hyb.html', context)


def getmyphotos(author, species):
    # Get species and hybrid lists that the user has at least one photo
    myspecies_list = Species.objects.exclude(status='synonym').filter(type='species')
    myhybrid_list = Species.objects.exclude(status='synonym').filter(type='hybrid')

    upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
    spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    myspecies_list = myspecies_list.filter(Q(pid__in=upl_list) | Q(pid__in=spc_list)).order_by('genus', 'species')
    myhybrid_list = myhybrid_list.filter(Q(pid__in=upl_list) | Q(pid__in=hyb_list)).order_by('genus', 'species')

    if species:
        upload_list = UploadFile.objects.filter(author=author).filter(pid=species.pid)  # Private photos
        if species.type == 'species':
            public_list = SpcImages.objects.filter(author=author).filter(pid=species.pid)  # public photos
        elif species.type == 'hybrid':
            public_list = HybImages.objects.filter(author=author).filter(pid=species.pid)  # public photos
        else:
            message = 'How did we get here???.'
            return HttpResponse(message)

        private_list = public_list.filter(rank=0)  # rejected photos
        # public_list  = public_list.filter(rank__gt=0)    # rejected photos
    else:
        private_list = public_list = upload_list = []

    return private_list, public_list, upload_list, myspecies_list, myhybrid_list


@login_required
def deletephoto(request, orid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    try:
        image = UploadFile.objects.get(pk=orid)
        species = Species.objects.get(pk=image.pid_id)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=species.pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    ortype = 'hybrid'
    if 'type' in request.GET:
        ortype = request.GET['type']

    if 'page' in request.GET:
        page = request.GET['page']
    else:
        page = "1"

    upl = UploadFile.objects.get(id=orid)
    filename = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
    upl.delete()
    area = ''
    if 'area' in request.GET:
        area = request.GET['area']
    role = 'cur'
    if 'role' in request.GET:
        role = request.GET['role']

    if area == 'allpending':
        # bulk delete by curators from all_pending tab
        url = "%s&page=%s&type=%s&days=%d" % (reverse('detail:curate_pending'), page, ortype, days)
    elif area == 'curate_newupload':  # from curate_newupload (all rank 0)
        # Requested from all upload photos
        url = "%s?page=%s" % (reverse('detail:curate_newupload'), page)
    elif role == 'pri':
        # Requested from private view
        url = "%s?role=%s" % (reverse('detail:myphoto', args=(species.pid,)), role)
    else:
        url = "%s?role=%s" % (reverse('detail:photos', args=(species.pid,)), role)

    # Finally remove file if exist
    if os.path.isfile(filename):
        os.remove(filename)

    return HttpResponseRedirect(url)


@login_required
def deletewebphoto(request, pid):
    species = Species.objects.get(pk=pid)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)
    spc = ''

    if 'page' in request.GET:
        page = request.GET['page']
    else:
        page = "1"

    if 'id' in request.GET:
        orid = request.GET['id']
        orid = int(orid)

        if species.type == 'species':
            try:
                spc = SpcImages.objects.get(id=orid)
                hist = SpcImgHistory(pid=Accepted.objects.get(pk=pid), user_id=request.user, img_id=spc.id,
                                     action='delete')
            except SpcImages.DoesNotExist:
                hist = ''
                pass
        else:
            try:
                spc = HybImages.objects.get(id=orid)
                hist = HybImgHistory(pid=Hybrid.objects.get(pk=pid), user_id=request.user, img_id=spc.id,
                                     action='delete')
            except HybImages.DoesNotExist:
                hist = ''
                pass
        if spc:
            if spc.image_file:
                filename = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid", str(spc.image_file))
                hist.save()
                if os.path.isfile(filename):
                    os.remove(filename)
            spc.delete()
    days = 7
    area = ''
    role = 'cur'
    if 'role' in request.GET:
        role = request.GET['role']
    if 'area' in request.GET:
        area = request.GET['area']
    if 'days' in request.GET:
        days = request.GET['days']
    if area == 'allpending':  # from curate_pending (all rank 0)
        url = "%s?role=%s&page=%s&type=%s&days=%s" % (reverse('detail:curate_pending'), role, page, type, days)
    else:
        url = "%s?role=%s" % (reverse('detail:photos', args=(species.pid,)), role)
    return HttpResponseRedirect(url)


@login_required
def approvemediaphoto(request, pid):
    species = Species.objects.get(pk=pid)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    # Only curator can approve
    role = getRole(request)
    if role != "cur":
        message = 'You do not have privilege to approve photos.'
        return HttpResponse(message)

    if 'id' in request.GET:
        orid = request.GET['id']
        orid = int(orid)
    else:
        message = 'This photo does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    try:
        upl = UploadFile.objects.get(pk=orid)
    except UploadFile.DoesNotExist:
        write_output(request, ">>> approvemediaphoto FAIL: " + species.textname() + "-" + str(orid))
        msg = "uploaded file #" + str(orid) + "does not exist"
        url = "%s?role=%s&msg=%s" % (reverse('detail:photos', args=(species.pid,)), role, msg)
        return HttpResponseRedirect(url)

    old_name = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
    tmp_name = os.path.join("/webapps/static/tmp/", str(upl.image_file_path))

    filename, ext = os.path.splitext(str(upl.image_file_path))
    # imgdir, filename = os.path.split(filename)
    if species.type == 'species':
        spc = SpcImages(pid=species.accepted, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                        source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                        description=upl.description, location=upl.location, created_date=upl.created_date)
        spc.approved_by = request.user
        hist = SpcImgHistory(pid=Accepted.objects.get(pk=pid), user_id=request.user, img_id=spc.id,
                             action='approve file')
        newdir = os.path.join(settings.STATIC_ROOT, "utils/images/species")
        image_file = "spc_"
    else:
        spc = HybImages(pid=species.hybrid, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                        source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                        description=upl.description, location=upl.location, created_date=upl.created_date)
        spc.approved_by = request.user
        hist = HybImgHistory(pid=Hybrid.objects.get(pk=pid), user_id=request.user, img_id=spc.id, action='approve file')
        newdir = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid")
        image_file = "hyb_"

    image_file = image_file + str(format(upl.pid_id, "09d")) + "_" + str(format(upl.id, "09d"))
    new_name = os.path.join(newdir, image_file)
    if not os.path.exists(new_name + ext):
        try:
            shutil.copy(old_name, tmp_name)
            shutil.move(old_name, new_name + ext)
        except shutil.Error:
            # upl.delete()
            url = "%s?role=%s" % (reverse('detail:photos', args=(species.pid,)), role)
            return HttpResponseRedirect(url)
        # logger.error(">>> approvemediaphoto: " + str(request.user) + " " + str(species.pid) + " " + old_name)
        spc.image_file = image_file + ext
    else:
        i = 1
        while True:
            image_file = image_file + "_" + str(i) + ext
            x = os.path.join(newdir, image_file)
            if not os.path.exists(x):
                try:
                    shutil.copy(old_name, tmp_name)
                    shutil.move(old_name, x)
                except shutil.Error:
                    upl.delete()
                    url = "%s?role=%s" % (reverse('detail:photos', args=(species.pid,)), role)
                    return HttpResponseRedirect(url)
                spc.image_file = image_file
                break
            i += 1

    spc.save()
    hist.save()
    upl.approved = True
    upl.delete(0)
    # logger.error(">>> Status changed to approved")
    write_output(request, species.textname() + "-" + str(orid))
    url = "%s?role=%s" % (reverse('detail:photos', args=(species.pid,)), role)
    return HttpResponseRedirect(url)


@login_required
def uploadfile(request, pid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    if request.user.is_authenticated and (request.user.tier.tier < 2 or not request.user.photographer.author_id):
        message = 'You dont have access to upload files. Please update your profile to gain access. ' \
                  'Or contact admin@orchidroots.org'
        return HttpResponse(message)

    author, author_list = get_author(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)
    role = 'pri'
    if 'role' in request.GET:
        role = request.GET['role']
    elif 'role' in request.POST:
        role = request.POST['role']

    form = UploadFileForm(initial={'author': request.user.photographer.author_id, 'role': role})

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            write_output(request, species.textname())
            role = request.POST['role']
            spc = form.save(commit=False)
            spc.pid = species
            spc.type = species.type
            spc.user_id = request.user
            spc.text_data = spc.text_data.replace("\"", "\'\'")
            spc.save()
            if role == 'pri':
                url = "%s?role=%s&author=%s" % (reverse('detail:myphoto', args=(species.pid,)), role,
                                                request.user.photographer.author_id)
            else:
                url = "%s?role=%s&author=%s" % (reverse('detail:photos', args=(species.pid,)), role,
                                                request.user.photographer.author_id)
            return HttpResponseRedirect(url)
        else:
            return HttpResponse('save failed')

    context = {'form': form, 'species': species, 'web': 'active', 'level': 'detail',
               'author_list': author_list, 'author': author,
               'role': role, 'namespace': 'detail', 'title': 'uploadfile'}
    return render(request, 'detail/uploadfile.html', context)


def get_author(request):
    if not request.user.is_authenticated or request.user.tier.tier < 2:
        return None, None

    author_list = Photographer.objects.exclude(user_id__isnull=True).order_by('displayname')
    author = None
    if request.user.tier.tier > 2 and 'author' in request.GET:
        author = request.GET['author']
        if author:
            author = Photographer.objects.get(pk=author)
        else:
            author = None
    if not author and request.user.tier.tier > 1:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')
    return author, author_list


@login_required
def uploadweb(request, pid, orid=None):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    if request.user.is_authenticated and request.user.tier.tier < 2:
        message = 'You dont have access to upload files. Please update your profile to gain access.'
        return HttpResponse(message)
    sender = 'web'
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)

    # The photo
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    role = 'pri'
    if 'role' in request.GET:
        role = request.GET['role']

    if request.method == 'POST':
        role = request.POST['role']
        if species.type == 'hybrid':
            accepted = species.hybrid
            form = UploadHybWebForm(request.POST)
        elif species.type == 'species':
            accepted = species.accepted
            form = UploadSpcWebForm(request.POST)
        else:
            return HttpResponse("image id " + str(orid) + "does not exist")

        if form.is_valid():
            spc = form.save(commit=False)
            if not spc.author and not spc.credit_to:
                return HttpResponse("Please select an author, or enter a new name for credit allocation.")
            spc.user_id = request.user
            spc.pid = accepted
            spc.text_data = spc.text_data.replace("\"", "\'\'")
            if orid and orid > 0:
                spc.id = orid
            # set rank to 0 if private status is requested
            if spc.is_private is True or request.user.tier.tier < 3:
                spc.rank = 0

            # If new author name is given, set rank to 0 to give it pending status. Except curator (tier = 3)
            if spc.author.user_id and request.user.tier.tier < 3:
                if (spc.author.user_id.id != spc.user_id.id) or role == 'pri':
                    spc.rank = 0
            if spc.image_url == 'temp.jpg':
                spc.image_url = None
            if spc.image_file == 'None':
                spc.image_file = None
            if spc.created_date == '' or not spc.created_date:
                spc.created_date = timezone.now()
            spc.save()

            if request.user.is_authenticated and role == 'cur' and request.user.tier.tier > 2:
                url = "%s?role=cur" % (reverse('detail:photos', args=(species.pid,)))

            else:
                # Public role shouldn't get to this '
                url = "%s?role=pub" % (reverse('detail:myphoto', args=(species.pid,)))
            write_output(request, species.textname())
            return HttpResponseRedirect(url)

    if not orid:  # upload, initialize author. Get image count
        if species.type == 'species':
            form = UploadSpcWebForm(initial={'author': request.user.photographer.author_id})
        else:
            form = UploadHybWebForm(initial={'author': request.user.photographer.author_id})
        img = ''
    else:  # update. initialize the form iwht current image
        if species.type == 'species':
            img = SpcImages.objects.get(pk=orid)
            if not img.image_url:
                sender = 'file'
                img.image_url = "temp.jpg"
            else:
                sender = 'web'
            form = UploadSpcWebForm(instance=img)
        else:
            img = HybImages.objects.get(pk=orid)
            if not img.image_url:
                img.image_url = "temp.jpg"
                sender = 'file'
            else:
                sender = 'web'
            form = UploadHybWebForm(instance=img)

    context = {'form': form, 'img': img, 'sender': sender,
               'species': species, 'loc': 'active',
               'role': role, 'level': 'detail', 'namespace': 'detail', 'title': 'uploadweb'}
    return render(request, 'detail/uploadweb.html', context)


def mypaginator(request, full_list, page_length, num_show):
    page_list = []
    first_item = 0
    last_item = 0
    next_page = 0
    prev_page = 0
    last_page = 0
    page = 0
    page_range = 0
    total = len(full_list)
    if page_length > 0:
        paginator = Paginator(full_list, page_length)
        if 'page' in request.GET:
            page = request.GET.get('page', '1')
        if not page or page == 0:
            page = 1
        else:
            page = int(page)

        try:
            page_list = paginator.page(page)
            last_page = paginator.num_pages
        except EmptyPage:
            page_list = paginator.page(1)
            last_page = 1
        next_page = page + 1
        if next_page > last_page:
            next_page = last_page
        prev_page = page - 1
        if prev_page < 1:
            prev_page = 1

        first_item = (page - 1) * page_length + 1
        last_item = first_item + page_length - 1
        if last_item > total:
            last_item = total
        # Get the index of the current page
        index = page_list.number - 1  # edited to something easier without index
        # This value is maximum index of your pages, so the last page - 1
        max_index = len(paginator.page_range)
        # You want a range of 7, so lets calculate where to slice the list
        start_index = index - num_show if index >= num_show else 0
        end_index = index + num_show if index <= max_index - num_show else max_index
        # My new page range
        page_range = paginator.page_range[start_index: end_index]
    return page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item
