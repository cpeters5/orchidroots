
# For Orchidaceae family only. Will be moved to common app

import string
import re
import pytz
import logging

import django.shortcuts
import random
import os
import shutil

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from django import template
from django.conf import settings
from PIL import Image
from PIL import ExifTags
from io import BytesIO
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.template import RequestContext
from itertools import chain

from django.utils import timezone
from datetime import datetime, timedelta
from utils.views import write_output, getRole, get_reqauthor, handle_bad_request

from .forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm
from accounts.models import User, Profile
from common.views import quality_update, rank_update, deletephoto

from django.apps import apps
Family = apps.get_model('common', 'Family')
Subfamily = apps.get_model('common', 'Subfamily')
Tribe = apps.get_model('common', 'Tribe')
Subtribe = apps.get_model('common', 'Subtribe')
Region = apps.get_model('common', 'Region')
Subregion = apps.get_model('common', 'Subregion')

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
Photographer = apps.get_model('accounts', 'Photographer')
AncestorDescendant = apps.get_model('orchidaceae', 'AncestorDescendant')
ReidentifyHistory = apps.get_model('orchidaceae', 'ReidentifyHistory')
MAX_HYB = 500
list_length = 1000  # Length of species_list and hybrid__list in hte navbar
logger = logging.getLogger(__name__)

app = 'orchidaceae'
# Redirect to list or browse if species/hybrid does not exist.
# TODO: Create a page for this
redirect_message = "<br><br>Species does not exist! <br>You may try <a href='/common/species/'>" \
                   "search species list</a> or <a href='/common/browsegen/?type=species'>browse species images.</a>"


@login_required
# Curator only - role = cur
def createhybrid(request):
    genus1 = genus2 = species1 = species2 = ''
    pid1 = request.GET.get('pid1', None)
    if not pid1:
        return HttpResponse(redirect_message)
    try:
        species1 = Species.objects.get(pk=pid1)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)
    if species1.status == 'synonym':
        species1 = species1.getAccepted()

    pid2 = request.GET.get('pid2', none)
    if not pid2:
        species2 = ''
    else:
        try:
            species2 = Species.objects.get(pk=pid2)
        except Species.DoesNotExist:
            return HttpResponse(redirect_message)
    if species2.status == 'synonym':
        species2 = species2.getAccepted()

    spc1 = species1.species
    if species1.infraspe:
        spc1 += ' ' + species1.infraspe
    spc2 = species2.species
    if species2.infraspe:
        spc2 += ' ' + species2.infraspe

    role = getRole(request)
    if not role or role != 'cur':
        send_url = '/detail/compare/' + str(pid1) + '/'
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
        send_url = '/detail/compare/' + str(pid1) + '/?msgnogenus=' + msgnogenus + '&genus1=' + genus1 + \
                   '&genus2=' + genus2 + '&species1=' + str(species1) + '&species2=' + str(species2)
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
    return HttpResponseRedirect("/display/photos/" + str(spcobj.pid) + "/?role=" + role + "&genus2=" + species2.genus + "&family=" + str(species2.gen.family))


def compare(request, pid=None):
    # TODO:  Use Species form instead
    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        
    role = getRole(request)
    pid2 = species2 = genus2 = ''
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')
    if species.type == 'hybrid':
        spcimg1_list = HybImages.objects.filter(pid=pid).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]
    else:
        spcimg1_list = SpcImages.objects.filter(pid=pid).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]
    family = species.gen.family
    genus = species.genus

    # Handle comparison request. Should use SpcForm instead.
    spcimg2_list = []
    spc2 = request.GET.get('species2', '').strip()
    gen2 = request.GET.get('genus2', '').strip()
    infraspe2 = request.GET.get('infraspe2', '').strip()
    infraspr2 = request.GET.get('infraspr2', '').strip()
    author2 = request.GET.get('author2', '').strip()
    year2 = request.GET.get('year2', '').strip()
    binomial2 = gen2 + ' ' + spc2
    if infraspr2:
        binomial2 = binomial2 + ' ' + infraspr2
    if infraspe2:
        binomial2 = binomial2 + ' ' + infraspe2
    if binomial2:
        species2 = Species.objects.filter(binomial__iexact=binomial2)
        if len(species2) == 0:
            message = "species, <b>" + str(gen2) + ' ' + spc2 + '</b> does not exist in ' + family.family + ' family'
            context = {'species': species, 'genus': genus, 'pid': pid, 'family': family,
                       'spcimg1_list': spcimg1_list,
                       'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                       'message2': message,
                       'tab': 'sbs', 'sbs': 'active', 'role': role}
            return render(request, 'common/compare.html', context)
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
                message = "species, <b>" + str(gen2) + ' ' + spc2 + '</b> returns more than one value. Please specify author name or year to narrow the search.'
                context = {'species': species, 'genus': genus, 'pid': pid,  # original
                           'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                           'message2': message, 'family': family,
                           'tab': 'sbs', 'sbs': 'active', 'role': role}
                return render(request,  'common/compare.html', context)
            else:  # length = 0
                message = "species, <b>" + str(gen2) + ' ' + spc2 + '</b> returned none'
                context = {'species': species, 'genus': genus, 'pid': pid,  # original
                           'genus2': gen2, 'species2': species2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                           'message1': message, 'family': family,
                           'tab': 'sbs', 'sbs': 'active', 'role': role}
                return render(request, 'common/compare.html', context)
        else:
            species2 = species2[0]
            pid2 = species2.pid
    else:
        pid2 = ''

    cross = ''
    message1 = message2 = accepted1 = accepted2 = ''

    # A second species is found
    if pid2:
        cross = Hybrid.objects.filter(seed_id=pid).filter(pollen_id=pid2)
        if not cross:
            cross = Hybrid.objects.filter(seed_id=pid2).filter(pollen_id=pid)
        if cross:
            cross = cross[0]
        else:
            cross = ''

    if species2:
        if species2.type == 'species':
            spcimg2_list = SpcImages.objects.filter(pid=pid2).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]
        else:
            spcimg2_list = HybImages.objects.filter(pid=pid2).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]

    msgnogenus = request.GET.get('msgnogenus', '')

    write_output(request, str(genus) + " " + str(species) + " vs " + str(genus2) + " " + str(species2))
    context = {'pid': pid, 'genus': genus, 'species': species,
               'pid2': pid2, 'accepted2': accepted2,  # pid of accepted species
               'spcimg1_list': spcimg1_list,
               'genus2': gen2, 'species2': species2, 'spcimg2_list': spcimg2_list,
               'cross': cross, 'family': family,
               'msgnogenus': msgnogenus, 'message1': message1, 'message2': message2,
               'tab': 'sbs', 'sbs': 'active', 'role': role}
    return render(request, 'common/compare.html', context)


@login_required
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


@login_required
def comments(request):
    # Handle sort
    sort = request.GET.get('sort', '').lower()

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
    role = getRole(request)
    write_output(request)
    context = {'comment_list': comment_list, 'sort': sort, 'role': role,}
    return render(request, 'detail/comments.html', context)


@login_required
def curateinfospc(request, pid):
    species = Species.objects.get(pk=pid)
    genus = species.genus
    accepted = Accepted.objects.get(pk=pid)

    tab = 'ins'
    tab = request.GET.get('tab', None)
    role = getRole(request)

    distribution_list = Distribution.objects.filter(pid=species.pid)
    if request.method == 'POST':
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
                # spc.description = spc.description.replace("\"", "\'\'")
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
                # spc.etymology = spc.etymology.replace("\"", "\'\'")
                spc.etymology = spc.etymology.replace("\r", "<br>")
            spc.operator = request.user
            spc.save()

            url = "%s?role=%s&family=%s" % (reverse('display:summary', args=(app,species.pid,)), role, species.gen.family)
            return HttpResponseRedirect(url)
        else:
            return HttpResponse("POST: Somethign's wrong")
    else:
        accepted = Accepted.objects.get(pk=species.pid)
        form = AcceptedInfoForm(instance=accepted)
        context = {'form': form, 'genus': genus, 'species': species,
                   'title': 'curateinfo', 'tab': 'ins', tab: 'active', 'distribution_list': distribution_list,
                   'role': role, 'app': app,}
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
            url = "%s?tab=info" % (reverse('detail:curateinfospc', args=(species.pid,)),)
            return HttpResponseRedirect(url)

    tab = request.GET.get('tab', 'inh')
    role = getRole(request)

    hybrid = Hybrid.objects.get(pk=species.pid)
    if request.method == 'POST':
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
            # url = "%s?role=%s&family=Orchidaceae" % (reverse('display:information', args=(pid,)), role)
            url = "%s?role=%s&family=%s" % (reverse('display:summary', args=(app,species.pid,)), role, species.gen.family)
            return HttpResponseRedirect(url)
        else:
            return HttpResponse("POST: Somethign's wrong")
    else:
        form = HybridInfoForm(instance=hybrid)
        spcform = RenameSpeciesForm(instance=species)

        context = {'form': form, 'spcform': spcform, 'genus': genus, 'species': species,
                   'tab': 'inh', tab: 'active', 'title': 'curateinfo', 'role': role,
                   'app': app,
                   }
        return render(request, 'detail/curateinfohyb.html', context)


@login_required
def reidentify(request, orid, pid):
    family = Family.objects.get(pk='Orchidaceae')
    source_file_name = ''
    role = getRole(request)
    if role != 'cur':
        url = "%s?role=%s" % (reverse('display:photos', args=(app, pid,)), role)
        return HttpResponseRedirect(url)

    old_species = Species.objects.get(pk=pid)
    # if old_species.status == 'synonym':
    #     synonym = Synonym.objects.get(pk=pid)
    #     pid = synonym.acc_id
    #     old_species = Species.objects.get(pk=pid)

    form = SpeciesForm(request.POST or None)
    oldtype = old_species.type
    if old_species.type == 'hybrid':
        old_img = HybImages.objects.get(pk=orid)
    elif old_species.type == 'species':
        old_img = SpcImages.objects.get(pk=orid)
    else:
        return HttpResponse("image id " + str(orid) + "does not exist")

    if request.method == 'POST':
        if form.is_valid():
            new_pid = form.cleaned_data.get('species')
            try:
                new_species = Species.objects.get(pk=new_pid)
            except Species.DoesNotExist:
                url = "%s?role=%s" % (reverse('display:photos', args=(app,pid,)), role)
                return HttpResponseRedirect(url)

            # If re-idenbtified to same type
            if new_species.type == old_species.type:
                if new_species.type == 'species':
                    new_img = SpcImages.objects.get(pk=old_img.id)
                    new_img.pid = new_species
                else:
                    new_img = HybImages.objects.get(pk=old_img.id)
                    new_img.pid = new_species
                hist = ReidentifyHistory(from_id=old_img.id, from_pid=old_species, to_pid=new_species,
                                         user_id=request.user, created_date=old_img.created_date)
                if source_file_name:
                    new_img.source_file_name = source_file_name
                new_img.pk = None
            else:
                if old_img.image_file:
                    if new_species.type == 'species':
                        new_img = SpcImages(pid=new_species.pid)
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
                    url = "%s?role=%s" % (reverse('display:photos', args=(app, new_species.pid,)), role)
                    return HttpResponseRedirect(url)
                if source_file_name:
                    new_img.source_file_name = source_file_name
            if old_img.author:
                new_img.author = old_img.author
            else:
                new_img.author = request.user.photographer

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
            url = "%s?role=%s" % (reverse('display:photos', args=(app, new_species.pid,)), role)
            return HttpResponseRedirect(url)
    context = {'form': form, 'species': old_species, 'img': old_img, 'role': 'cur', 'family': family, 'app': app,}
    return render(request, 'detail/reidentify.html', context)


def get_author(request):
    if not request.user.is_authenticated or request.user.tier.tier < 2:
        return None, None

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
    return author


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
    # request.user.photographer
    role = getRole(request)

    if request.method == 'POST':
        author = request.POST.get('author', '')
        if author:
            author = Photographer.objects.get(pk=author)
        else:
            author = request.user.photographer

        if species.type == 'hybrid':
            form = UploadHybWebForm(request.POST)
        elif species.type == 'species':
            form = UploadSpcWebForm(request.POST)
        else:
            return HttpResponse("image id " + str(orid) + "does not exist")

        if form.is_valid():
            spc = form.save(commit=False)
            spc.user_id = request.user
            spc.author = author
            spc.pid = species
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
            # logger.error(" family = " + str(species.gen.family))
            url = "%s?role=%s" % (reverse('display:photos', args=(app, species.pid,)),role)
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
        if hasattr(img, 'author'):
            author = img.author
        else:
            author = None

    context = {'form': form, 'img': img, 'sender': sender,
               'species': species, 'loc': 'active',
               'family': species.gen.family, 'author': author,
               'role': role, 'title': 'uploadweb', 'app': app,}
    return render(request, 'detail/uploadweb.html', context)


@login_required
def uploadfile(request, pid):
    role = getRole(request)
    species = Species.objects.get(pk=pid)
    if request.user.tier.tier < 2 or not request.user.photographer.author_id:
        message = 'You dont have access to upload files. Please update your profile to gain access. ' \
                  'Or contact admin@bluenanta.com'
        return HttpResponse(message)
    if request.user.tier.tier < 3 and species.get_num_img_by_author(request.user.photographer.get_authid()) > 2:
        message = 'Each user may upload at most 3 private photos for each species/hybrid. ' \
                'Please delete one or more of your photos before uploading a new one.'
        return HttpResponse(message)

    author = get_reqauthor(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This name does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    # Orchid is a speciel case
    family = species.gen.family
    # if species.status == 'synonym':
    #     synonym = Synonym.objects.get(pk=pid)
    #     pid = synonym.acc_id
    #     species = Species.objects.get(pk=pid)

    name_message = 'Scientific name or registered hybrid name (if different from the title, otherwise, leave it blank)'
    form = UploadFileForm(initial={'author': request.user.photographer.author_id, 'role': role })

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            write_output(request, species.textname())
            spc = form.save(commit=False)
            if isinstance(species, Species):
                spc.pid = species
            if not spc.binomial:
                spc.binomial = species.binomial
            else:
                spc.pid = None
            spc.author = request.user.photographer
            spc.type = species.type
            spc.user_id = request.user
            spc.text_data = spc.text_data.replace("\"", "\'\'")
            spc.save()
            url = "%s?role=%s&author=%s" % (reverse('display:photos', args=(app, species.pid,)), role,
                                                request.user.photographer.author_id)
            return HttpResponseRedirect(url)

    context = {'form': form, 'species': species, 'web': 'active',
               'author': author, 'family': family,
               'role': role, 'app': app, 'title': 'uploadfile'}
    return render(request, 'detail/uploadfile.html', context)

# Redirect old urls to display app.
# Convert dynamic to static pid parameter
def information(request):
    pid = request.GET.get('pid')
    try:
        pid = int(pid)  # Try to convert pid to an integer
        # If conversion is successful, redirect to canonical url
        new_url = f'/display/summary/orchidaceae/{pid}/'
        return HttpResponsePermanentRedirect(new_url)
    except (TypeError, ValueError):
        # If pid is not found or not an integer, send to summary to handle missing pid
        return HttpResponsePermanentRedirect('/')

def photos(request):
    pid = request.GET.get('pid')
    try:
        pid = int(pid)  # Try to convert pid to an integer
        # If conversion is successful, redirect to canonical url
        new_url = f'/display/photos/orchidaceae/{pid}/'
        return HttpResponsePermanentRedirect(new_url)
    except (TypeError, ValueError):
        # If pid is not found or not an integer, send to summary to handle missing pid
        return HttpResponsePermanentRedirect('/')

@login_required
def ancestrytree(request):
    pid = request.GET.get('pid')
    try:
        pid = int(pid)  # Try to convert pid to an integer
        # If conversion is successful, redirect to canonical url
        new_url = f'/orchidaceae/ancestrytree/{pid}/'
        return HttpResponsePermanentRedirect(new_url)
    except (TypeError, ValueError):
        # If pid is not found or not an integer, send to summary to handle missing pid
        return HttpResponsePermanentRedirect('/')

@login_required
def ancestor(request):
    pid = request.GET.get('pid')
    try:
        pid = int(pid)  # Try to convert pid to an integer
        # If conversion is successful, redirect to canonical url
        new_url = f'/orchidaceae/ancestor/{pid}/'
        return HttpResponsePermanentRedirect(new_url)
    except (TypeError, ValueError):
        # If pid is not found or not an integer, send to summary to handle missing pid
        return HttpResponsePermanentRedirect('/')
