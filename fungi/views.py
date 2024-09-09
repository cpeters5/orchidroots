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
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.template import RequestContext
from itertools import chain

from django.utils import timezone
from datetime import datetime, timedelta
from utils.views import write_output, getRole
from utils import config
applications = config.applications

from .forms import UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm, UploadFileForm
from accounts.models import User, Profile, Photographer
from common.models import Family, Subfamily, Tribe, Subtribe, Region, SubRegion
from .models import Genus, Species, Synonym, Accepted, Hybrid, SpcImages, Distribution, UploadFile
from common.views import rank_update, quality_update
app = 'fungi'

MAX_HYB = 500
list_length = 1000  # Length of species_list and hybrid__list in hte navbar
logger = logging.getLogger(__name__)
redirect_message = "<br><br>Species does not exist! "


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
    role = getRole(request)
    family = ''
    write_output(request)
    context = {'file_list': page_list,
               'tab': 'upl', 'role': role, 'upl': 'active', 'days': days, 'family': family, 'app': app,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'section': 'Curator Corner',
               }
    return render(request, "common/curate_newupload.html", context)


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

    file_list = SpcImages.objects.filter(rank=0)

    if days:
        file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days))
    file_list = file_list.order_by('-created_date')

    num_show = 5
    page_length = 100
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)
    family = ''

    role = getRole(request)
    write_output(request)
    context = {'file_list': page_list, 'type': ortype,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days, 'family': family, 'app': app,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               }
    return render(request, 'common/curate_pending.html', context)


@login_required
def reidentify(request, orid, pid):
    source_file_name = ''
    role = getRole(request)
    old_species = Species.objects.get(pk=pid)
    old_family = old_species.gen.family
    if role != 'cur':
        url = "%s?role=%s" % (reverse('display:photos', args=(app, pid,)), role)
        return HttpResponseRedirect(url)

    if old_species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        old_species = Species.objects.get(pk=pid)

    form = SpeciesForm(request.POST or None)
    old_img = SpcImages.objects.get(pk=orid)

    if request.method == 'POST':
        if form.is_valid():
            new_pid = form.cleaned_data.get('species')
            try:
                new_species = Species.objects.get(pk=new_pid)
            except Species.DoesNotExist:
                url = "%s?role=%s" % (reverse('display:photos', args=(app, pid,)), role)
                return HttpResponseRedirect(url)

            # If re-idenbtified to same genus. Just change pid
            if new_species.genus == old_species.genus:
                new_img = SpcImages.objects.get(pk=old_img.id)
                new_img.pid = new_species
                if source_file_name:
                    new_img.source_file_name = source_file_name
                new_img.pk = None
            else :
                if old_img.image_file:
                    new_img = SpcImages(pid=new_species)
                    from_path = os.path.join(settings.STATIC_ROOT, old_img.image_dir() + old_img.image_file)
                    if new_species.gen.family.application == 'orchidaceae':
                        to_path = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(new_species.gen.family.application) + "/" + old_img.image_file)
                    else:
                        to_path = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(new_species.gen.family) + "/" + old_img.image_file)
                    os.rename(from_path, to_path)
                else:
                    url = "%s?role=%s" % (reverse('display:photos', args=(app, new_species.pid,)), role)
                    return HttpResponseRedirect(url)
                if source_file_name:
                    new_img.source_file_name = source_file_name
            new_img.author = old_img.author
            new_img.pk = None
            new_img.source_url = old_img.source_url
            new_img.image_url = old_img.image_url
            new_img.image_file = old_img.image_file
            new_img.name = old_img.name
            new_img.variation = old_img.variation
            new_img.form = old_img.form
            new_img.text_data = old_img.text_data
            new_img.description = old_img.description
            new_img.created_date = old_img.created_date
            # point to the new record, Who requested this change?
            new_img.user_id = request.user

            # ready to save
            new_img.save()

            # Delete old record
            old_img.delete()

            write_output(request, old_species.textname() + " ==> " + new_species.textname())
            url = "%s?role=%s" % (reverse('display:photos', args=(app, new_species.pid,)), role)
            return HttpResponseRedirect(url)
    context = {'form': form, 'species': old_species, 'img': old_img, 'role': 'cur', 'family': old_family, 'app': app, }
    return render(request, 'fungi/reidentify.html', context)


@login_required
def uploadweb(request, pid, orid=None):
    sender = 'web'
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)

    # For Other application only
    family = species.gen.family
    author = request.POST.get('author','')
    try:
        author = Photographer.objects.get(pk=author)
    except Photographer.DoesNotExist:
        author = ''
    # We now allow synonym view
    # if species.status == 'synonym':
    #     synonym = Synonym.objects.get(pk=pid)
    #     pid = synonym.acc_id
    #     species = Species.objects.get(pk=pid)

    role = getRole(request)

    if request.method == 'POST':
        form = UploadSpcWebForm(request.POST)

        if form.is_valid():
            spc = form.save(commit=False)
            spc.user_id = request.user
            author = request.POST.get('author', '')
            try:
                author = Photographer.objects.get(pk=author)
            except Photographer.DoesNotExist:
                author = ''
            if author:
                spc.author = author
            else:
                spc.author = request.user.photographer
            # if not spc.author and not spc.credit_to:
            #     return HttpResponse("Please select an author, or enter a new name for credit allocation.")
            spc.pid = species
            spc.text_data = spc.text_data.replace("\"", "\'\'")
            if orid and orid > 0:
                spc.id = orid

            # If new author name is given, set rank to 0 to give it pending status. Except curator (tier = 3)
            # if spc.author.user_id and request.user.tier.tier < 3:
            #     if (spc.author.user_id.id != spc.user_id.id) or role == 'pri':
            #         spc.rank = 0
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

            url = "%s?role=cur" % (reverse('display:photos', args=(app, species.pid,)))
            write_output(request, species.textname())
            return HttpResponseRedirect(url)

    if not orid:  # upload, initialize author. Get image count
        if species.type == 'species':
            form = UploadSpcWebForm(initial={'author': request.user.photographer.author_id})
        else:
            form = UploadHybWebForm(initial={'author': request.user.photographer.author_id})
        img = ''
    else:  # update. initialize the form iwht current image
        img = SpcImages.objects.get(pk=orid)
        if not img.image_url:
            sender = 'file'
            img.image_url = "temp.jpg"
        else:
            sender = 'web'
        if hasattr(img, 'author'):
            author = img.author
        else:
            author = None
    form = UploadSpcWebForm(instance=img)
    context = {'form': form, 'img': img, 'sender': sender, 'loc': 'active',
               'species': species, 'family': family, 'app': app, 'author': author,
               'role': role}
    return render(request, 'fungi/uploadweb.html', context)


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


@login_required
def curateinfospc(request, pid):
    species = Species.objects.get(pk=pid)
    family = species.gen.family
    accepted = Accepted.objects.get(pk=pid)
    genus = species.genus
    tab = 'ins'
    if 'tab' in request.GET:
        tab = request.GET['tab']
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
            # if spc.history:
            #     spc.history = spc.history.replace("<br>", "")
            #     spc.history = spc.history.replace("\"", "\'\'")
            #     spc.history = spc.history.replace("\r", "<br>")
            if spc.etymology:
                spc.etymology = spc.etymology.replace("<br>", "")
                # spc.etymology = spc.etymology.replace("\"", "\'\'")
                spc.etymology = spc.etymology.replace("\r", "<br>")
            spc.operator = request.user
            spc.save()

            url = "%s?role=%s&family=%s" % (reverse('display:information', args=(species.pid,)), role, species.gen.family)
            return HttpResponseRedirect(url)
        else:
            return HttpResponse("POST: Somethign's wrong")
    else:
        accepted = Accepted.objects.get(pk=species.pid)
        form = AcceptedInfoForm(instance=accepted)
        context = {'form': form, 'genus': genus, 'species': species, 'family': family, 'app': app,
                   'tab': 'ins', tab: 'active', 'distribution_list': distribution_list,
                   'role': role,}
        return render(request, 'fungi/curateinfospc.html', context)


@login_required
def approvemediaphoto(request, pid):
    # !!! UNTESTED
    # Move to a utiles method
    if 'family' in request.GET:
        family = request.GET['family']
        try:
            family = Family.objects.get(family=family)
            if family != '' and family.family != 'Orchidaceae':
                crit = 1

        except Family.DoesNotExist:
            family = ''
            app = None
    if not family:
        if 'app' in request.GET:
            app = request.GET['app']
            if app not in applications:
                app = ''

    species = Species.objects.get(pk=pid)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    image_dir = "utils/images/" + str(family)
    newdir = os.path.join(settings.STATIC_ROOT, image_dir)
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
        msg = "uploaded file #" + str(orid) + "does not exist"
        url = "%s?role=%s&msg=%s" % (reverse('display:photos', args=(app, species.pid,)), role, msg)
        return HttpResponseRedirect(url)
    upls = UploadFile.objects.filter(pid=pid)

    for upl in upls:
        old_name = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
        tmp_name = os.path.join("/webapps/static/tmp/", str(upl.image_file_path))

        filename, ext = os.path.splitext(str(upl.image_file_path))
        spc = SpcImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name,
                    source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                    description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
        spc.approved_by = request.user

        image_file = species.genus + '_' + str(format(upl.pid.pid, "09d")) + "_" + str(format(upl.id, "09d"))
        newpath = os.path.join(newdir, image_file)
        if not os.path.exists(newpath + ext):
            try:
                shutil.copy(old_name, tmp_name)
                shutil.move(old_name, newpath + ext)
            except shutil.Error:
                url = "%s?role=%s" % (reverse('display:photos', args=(app, species.pid,)), role)
                return HttpResponseRedirect(url)
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
                        url = "%s?role=%s" % (reverse('display:photos', args=(app, species.pid,)), role)
                        return HttpResponseRedirect(url)
                    spc.image_file = image_file
                    break
                i += 1
        # spc.image_file_path = image_dir + image_file
        spc.save()
        upl.approved = True
        upl.delete(0)
    write_output(request, str(family))
    url = "%s?role=%s" % (reverse('display:photos', args=(app, species.pid,)), role)
    return HttpResponseRedirect(url)

