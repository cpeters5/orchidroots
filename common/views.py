import string
import re
import os
import logging
import random
import shutil

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse, reverse_lazy, resolve
from django.utils import timezone
from itertools import chain
import django.shortcuts
from django.apps import apps
from fuzzywuzzy import fuzz, process
from datetime import datetime, timedelta
from utils import config
from utils.views import write_output, getRole, paginator, get_author, get_family_list, getModels, pathinfo
from core.models import Family, Subfamily, Tribe, Subtribe, Region, SubRegion
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages
from accounts.models import User, Photographer, Sponsor
from .forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm

epoch = 1740
alpha_list = string.ascii_uppercase
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
alpha_list = config.alpha_list


def getAllGenera():
    # Call this when Family is not provided
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    return OrGenus, OtGenus


def getFamilyImage(family):
    SpcImages = apps.get_model(family.application, 'SpcImages')
    return SpcImages.objects.filter(rank__lt=7).order_by('-rank','quality', '?')[0:1][0]


def orchid_home(request):
    ads_insert = 0
    sponsor = ''
    all_list = []
    role = getRole(request)
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']

        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)

    num_samples = 4
    # 3 major families + succulent + carnivorous
    # (3 other families form the last row.)
    num_blocks = 5

    # Get a sample image of orchids
    SpcImages = apps.get_model('orchidaceae', 'SpcImages')
    orcimage = SpcImages.objects.filter(rank__lt=7).filter(rank__gt=0).order_by('-rank','quality', '?')[0:1][0]
    all_list = all_list + [['orchidaceae', orcimage]]

    # Get random other families
    SpcImages = apps.get_model('other', 'SpcImages')
    Genus = apps.get_model('other', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            other_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            continue
        all_list = all_list + [[other_obj.pid.family, other_obj]]

    # get random suculents
    sample_genus = Genus.objects.filter(is_succulent=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    try:
        succulent_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        succulent_obj = ''
    all_list = all_list + [['Succulent', succulent_obj]]

    # get random carnivorous
    sample_genus = Genus.objects.filter(is_carnivorous=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    carnivorous_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    all_list = all_list + [['Carnivorous', carnivorous_obj]]

    # get random parasitic
    sample_genus = Genus.objects.filter(is_parasitic=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    parasitic_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    all_list = all_list + [['Parasitic', parasitic_obj]]

    ads_insert = int(random.random() * num_blocks) + 1
    sponsor = Sponsor.objects.filter(is_active=1).order_by('?')[0:1][0]
    random.shuffle(all_list)

    context = {'orcimage': orcimage, 'all_list': all_list, 'succulent_obj': succulent_obj,
               'carnivorous_obj': carnivorous_obj, 'parasitic_obj': parasitic_obj,
               'ads_insert': ads_insert, 'sponsor': sponsor, 'role': role }
    return render(request, 'orchid_home.html', context)


def require_get(view_func):
    def wrap(request, *args, **kwargs):
        if request.method != "GET":
            return HttpResponseBadRequest("Expecting GET request")
        return view_func(request, *args, **kwargs)
    wrap.__doc__ = view_func.__doc__
    wrap.__dict__ = view_func.__dict__
    wrap.__name__ = view_func.__name__
    return wrap

@login_required
def taxonomy(request):
    family_list, alpha = get_family_list(request)
    context = {'family_list': family_list,
               }
    return render(request, "common/taxonomy.html", context)

@login_required
def genera(request):
    myspecies = ''
    author = ''
    path = resolve(request.path).url_name
    role = getRole(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    family_list, alpha = get_family_list(request)
    if 'myspecies' in request.GET:
        myspecies = request.GET['myspecies']
        if myspecies:
            author = Photographer.objects.get(user_id=request.user)
    if family:
        if subtribe:
            genus_list = Genus.objects.filter(subtribe=subtribe)
        elif tribe:
            genus_list = Genus.objects.filter(tribe=tribe)
        elif subfamily:
            genus_list = Genus.objects.filter(subfamily=subfamily)
        elif family:
            genus_list = Genus.objects.filter(family=family)
    else:
        # No family (e.g. first landing on this page), show all non-Orchidaceae genera
        OrGenus, OtGenus = getAllGenera()
        if alpha:
            fam_list = family_list.values_list('family', flat=True)
            otgenus_list = OtGenus.objects.filter(family__in=fam_list)
        else:
            otgenus_list = OtGenus.objects.all()
        genus_list = otgenus_list
    # If private request
    if myspecies and author:
        pid_list = SpcImages.objects.filter(author_id=author).values_list('gen', flat=True).distinct()
        genus_list = genus_list.filter(pid__in=pid_list)


    # Complete building genus list
    # Define sort
    talpha = ''
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if talpha:
        genus_list = genus_list.filter(genus__istartswith=talpha)
    if request.GET.get('sort'):
        sort = request.GET['sort']
        sort.lower()

    total = len(genus_list)
    write_output(request, str(family))
    context = {
        'genus_list': genus_list,  'app': app, 'total':total, 'talpha': talpha,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'family_list': family_list, 'myspecies': myspecies,
        'alpha_list': alpha_list, 'alpha': alpha,
        'path': path
    }
    return render(request, "common/genera.html", context)


@login_required
def species(request):
    # path = resolve(request.path).url_name
    myspecies = ''
    author = ''
    genus_obj = ''
    from_path = pathinfo(request)
    genus = ''
    talpha = ''
    path_link = 'information'
    if str(request.user) == 'chariya':
        path_link = 'photos'
    role = getRole(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'genus' in request.GET:
        genus = request.GET['genus']
        if genus:
            try:
                genus_obj = Genus.objects.get(genus=genus)
            except Genus.DoesNotExist:
                genus_obj = ''
    if 'myspecies' in request.GET:
        myspecies = request.GET['myspecies']
        if myspecies:
            author = Photographer.objects.get(user_id=request.user)

    # If Orchidaceae, go to full table.
    if family and family.family == 'Orchidaceae':
        url = "%s?role=%s&family=%s" % (reverse('orchidaceae:species'), role, family)
        if genus_obj:
            url = url + "&genus=" + str(genus_obj)
        return HttpResponseRedirect(url)
    max_items = 3000

    syn = ''
    if 'syn' in request.GET:
        syn = request.GET['syn']

    if genus_obj:
        species_list = Species.objects.filter(type='species').filter(
            cit_status__isnull=True).exclude(cit_status__exact='').filter(genus=genus_obj)
        # new genus has been selected. Now select new species/hybrid
    elif from_path == 'research':
        species_list = []
    elif family and from_path != 'research':
        species_list = Species.objects.filter(type='species').filter(
            cit_status__isnull=True).exclude(cit_status__exact='')
        genus_list = Genus.objects.filter(family=family)
        if subtribe:
            genus_list = genus_list.filter(subtribe=subtribe)
        elif tribe:
            genus_list = genus_list.filter(tribe=tribe)
        elif subfamily:
            genus_list = genus_list.filter(subfamily=subfamily)
        genus_list = genus_list.values_list('genus', flat=True)
        species_list = species_list.filter(genus__in=genus_list)
    else:
        # app = 'other'
        # Species = apps.get_model(app, 'Species')
        species_list = Species.objects.filter(type='species')
        species_list = species_list.filter(gen__family__application=app)

    if syn == 'N':
        species_list = species_list.exclude(status='synonym')
        syn = 'N'
    else:
        syn = 'Y'
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if talpha != '':
        species_list = species_list.filter(species__istartswith=talpha)
    if myspecies and author:
        pid_list = SpcImages.objects.filter(author_id=author).values_list('pid', flat=True).distinct()
        species_list = species_list.filter(pid__in=pid_list)


    total = len(species_list)
    msg = ''

    if total > max_items:
        species_list = species_list[0:max_items]
        msg = "List too long, truncated to " + str(max_items) + ". Please refine your search criteria."
        total = max_items
    # if 'alpha' in request.GET:
    #     alpha = request.GET['alpha']
    # family_list, alpha = get_family_list(request)

    write_output(request, str(family))
    context = {
        'genus': genus, 'species_list': species_list, 'app': app, 'total':total, 'syn': syn, 'max_items': max_items,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'alpha_list': alpha_list, 'talpha': talpha, 'myspecies': myspecies,
        'msg': msg, 'path_link': path_link, 'from_path': 'species',
    }
    return render(request, "common/species.html", context)


@login_required
def hybrid(request):
    myspecies = ''
    author = ''
    path = resolve(request.path).url_name
    path = 'genera'
    genus = ''
    talpha = ''
    role = getRole(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'genus' in request.GET:
        genus = request.GET['genus']
    if genus:
        try:
            genus = Genus.objects.get(genus=genus)
        except Genus.DoesNotExist:
            genus = ''
    if family and family.family == 'Orchidaceae':
        url = "%s?role=%s&family=%s" % (reverse('orchidaceae:hybrid'), role, family)
        if genus:
            url = url + "&genus=" + str(genus)
        return HttpResponseRedirect(url)
    if 'myspecies' in request.GET:
        myspecies = request.GET['myspecies']
        if myspecies:
            author = Photographer.objects.get(user_id=request.user)

    hybrid_list = []
    syn = ''
    primary = ''
    msg = ''
    max_items = 3000

    if 'syn' in request.GET:
        syn = request.GET['syn']
    if 'primary' in request.GET:
        primary = request.GET['primary']
    if genus:
        hybrid_list = Species.objects.filter(type='hybrid').filter(genus=genus)
    elif family:
        hybrid_list = Species.objects.filter(type='hybrid')
        genus_list = Genus.objects.filter(family=family)
        if subtribe:
            genus_list = genus_list.filter(subtribe=subtribe)
        elif tribe:
            genus_list = genus_list.filter(tribe=tribe)
        elif subfamily:
            genus_list = genus_list.filter(subfamily=subfamily)
        genus_list = genus_list.values_list('genus', flat=True)
        hybrid_list = hybrid_list.filter(genus__in=genus_list)
    else:
        # app = 'other'
        # Species = apps.get_model(app, 'Species')
        hybrid_list = Species.objects.filter(type='hybrid')


    if syn == 'N':
        hybrid_list = hybrid_list.exclude(status='synonym')
        syn = 'N'
    else:
        syn = 'Y'
    if primary == 'Y':
        hybrid_list = hybrid_list.filter(hybrid__seed_type='species').filter(hybrid__pollen_type='species')
        primary = 'Y'
    else:
        primary = 'N'

    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if talpha != '':
        hybrid_list = hybrid_list.filter(species__istartswith=talpha)
    if myspecies and author:
        if family and family.family == 'Orchidaceae':
            pid_list = HybImages.objects.filter(author_id=author).values_list('pid', flat=True).distinct()
        else:
            pid_list = SpcImages.objects.filter(author_id=author).values_list('pid', flat=True).distinct()
        hybrid_list = hybrid_list.filter(pid__in=pid_list)

    total = len(hybrid_list)
    # hybrid_list = hybrid_list.order_by('genus', 'species')
    if total > max_items:
        hybrid_list = hybrid_list[0:max_items]
        msg = "List too long. Only show first " + str(max_items) + " items"
        total = max_items
    # family_list, alpha = get_family_list(request)
    write_output(request, str(family))
    context = {
        'genus': genus, 'hybrid_list': hybrid_list, 'app': app, 'total':total, 'syn': syn, 'max_items': max_items,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'alpha_list': alpha_list, 'talpha': talpha, 'myspecies': myspecies,
        'msg': msg, 'path': path, 'primary': primary,
    }
    return render(request, "common/hybrid.html", context)


@login_required
def uploadfile(request, pid):
    if request.user.tier.tier < 2 or not request.user.photographer.author_id:
        message = 'You dont have access to upload files. Please update your profile to gain access. ' \
                  'Or contact admin@orchidroots.org'
        return HttpResponse(message)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)

    author, author_list = get_author(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This name does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    app = species.gen.family.application
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)
    role = getRole(request)
    form = UploadFileForm(initial={'author': request.user.photographer.author_id, 'role': role})
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            write_output(request, species.textname())
            spc = form.save(commit=False)
            if isinstance(species, Species):
                spc.pid = species.pid
            spc.family = family
            spc.type = species.type
            spc.user_id = request.user
            spc.text_data = spc.text_data.replace("\"", "\'\'")
            spc.save()
            url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, species.gen.family)
            return HttpResponseRedirect(url)
        else:
            return HttpResponse('save failed')

    context = {'form': form, 'species': species, 'web': 'active', 'family': species.gen.family,
               'author_list': author_list, 'author': author,
               'role': role, 'app': app,}
    return render(request, app + '/uploadfile.html', context)


@login_required
# This is not working.  Must define a different UploadSpcWebForm for each domain (Orchidaceae, Bromeliaceae, Other, etc...)
def uploadcommonweb(request, pid, orid=None):
    sender = 'web'
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponse(redirect_message)

    # We now allow synonym view!
    # if species.status == 'synonym':
    #     synonym = Synonym.objects.get(pk=pid)
    #     pid = synonym.acc_id
    #     species = Species.objects.get(pk=pid)

    if request.method == 'POST':
        form = UploadSpcWebForm(request.POST)

        if form.is_valid():
            spc = form.save(commit=False)
            if not spc.author and not spc.credit_to:
                return HttpResponse("Please select an author, or enter a new name for credit allocation.")
            spc.user_id = request.user
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

            url = "%s?role=cur&family=%s" % (reverse('display:photos', args=(species.pid,)), species.gen.family)
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
        form = UploadSpcWebForm(instance=img)

    context = {'form': form, 'img': img, 'sender': sender, 'loc': 'active',
               'species': species, 'family': family,
               'role': role, 'app': app,}
    return render(request, app + '/uploadweb.html', context)


def rank_update(request, SpcImages):
    rank = 0
    if 'rank' in request.GET:
        rank = request.GET['rank']
        rank = int(rank)
        if 'id' in request.GET:
            orid = request.GET['id']
            orid = int(orid)
            image = ''
            try:
                image = SpcImages.objects.get(pk=orid)
            except SpcImages.DoesNotExist:
                return 0
                # acc = Accepted.objects.get(pk=pid)
            image.rank = rank
            image.save()
    return rank


def quality_update(request, SpcImages):
    if request.user.is_authenticated and request.user.tier.tier > 2 and 'quality' in request.GET:
        quality = request.GET['quality']
        quality = int(quality)
        if 'id' in request.GET:
            orid = request.GET['id']
            orid = int(orid)
            image = ''
            try:
                image = SpcImages.objects.get(pk=orid)
            except SpcImages.DoesNotExist:
                return 3
            image.quality = quality
            image.save()
    return


def getphotolist(author, family, species, Species, UploadFile, SpcImages, HybImages):
    # Get species and hybrid lists that the user has at least one photo
    myspecies_list = Species.objects.exclude(status='synonym').filter(type='species')
    myhybrid_list = Species.objects.exclude(status='synonym').filter(type='hybrid')

    upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
    spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    if app == 'orchidaceae' and species.type == 'hybrid':
        hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    else:
        hyb_list = []
    myspecies_list = myspecies_list.filter(Q(pid__in=upl_list) | Q(pid__in=spc_list)).order_by('genus', 'species')
    myhybrid_list = myhybrid_list.filter(Q(pid__in=upl_list) | Q(pid__in=hyb_list)).order_by('genus', 'species')

    if species:
        upload_list = UploadFile.objects.filter(author=author).filter(pid=species.pid)  # Private photos
        if app == 'orchidaceae' and species.type == 'hybrid':
            public_list = HybImages.objects.filter(pid=species.pid)  # public photos
        else:
            public_list = SpcImages.objects.filter(pid=species.pid)  # public photos

        private_list = public_list.filter(rank=0)  # rejected photos
        public_list  = public_list.filter(rank__gt=0)    # rejected photos
    else:
        private_list = public_list = upload_list = []

    return private_list, public_list, upload_list, myspecies_list, myhybrid_list


def getmyphotos(author, app, species, Species, UploadFile, SpcImages, HybImages, role):
    # Get species and hybrid lists that the user has at least one photo
    myspecies_list = Species.objects.exclude(status='synonym').filter(type='species')
    myhybrid_list = Species.objects.exclude(status='synonym').filter(type='hybrid')

    my_upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
    my_spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    if app == 'orchidaceae':
        my_hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    else:
        my_hyb_list = []
    # list for dropdown select
    myspecies_list = myspecies_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_spc_list)).order_by('genus', 'species')
    myhybrid_list = myhybrid_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_hyb_list)).order_by('genus', 'species')

    # Get list for display
    if species:
        if app == 'orchidaceae' and species.type == 'hybrid':
            public_list = HybImages.objects.filter(pid=species.pid)  # public photos
        else:
            public_list = SpcImages.objects.filter(pid=species.pid)  # public photos
        upload_list = UploadFile.objects.filter(pid=species.pid)  # All upload photos
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            upload_list = upload_list.filter(author=author) # Private photos
            private_list = private_list.filter(author=author) # Private photos

        # Display all rank > 0 or rank = 0 if author matches
        public_list  = public_list.filter(Q(rank__gt=0) | Q(author=author))
    else:
        private_list = public_list = upload_list = []

    return private_list, public_list, upload_list, myspecies_list, myhybrid_list


def browsegen(request):
    app = ''
    family = ''
    newfamily = ''
    talpha = ''
    num_show = 5
    page_length = 20
    ads_insert = 0
    start_ad = 3        # Minimum images to display sponsor ad.
    sponsor = ''
    my_full_list = []
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
        if (family == '' or family == None) and 'family' in request.GET:
            family = request.GET['family']
    if 'app' in request.GET:
        app = request.GET['app']

    if family and family != 'other':
        family = Family.objects.get(family=family)
        app = family.application
    else:
        app = 'other'
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request, family)

    page_range = page_list = last_page = next_page = prev_page = page = first_item = last_item = total = ''
    display = ''
    # Get requested parameters
    role = getRole(request)
    if 'display' in request.GET:
        display = request.GET['display']
    if not display:
        display = ''

    if app == 'orchidaceae':
        Genus = apps.get_model(app.lower(), 'Genus')
    else:
        Genus = apps.get_model(app.lower(), 'Genus')

    pid_list = Genus.objects.all()

    if talpha:
        pid_list = pid_list.filter(genus__istartswith=talpha)

    if pid_list:
        if family:
            pid_list = pid_list.filter(family=family.family)
        else:
            pid_list = pid_list.filter(family__application='other')

        if display == 'checked':
            pid_list = pid_list.filter(num_spcimage__gt=0)
        pid_list = pid_list.order_by('genus')
        total = len(pid_list)
        page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
            = mypaginator(request, pid_list, page_length, num_show)

        if len(page_list) > start_ad:
            ads_insert = int(random.random() * len(page_list)) + 1
            sponsor = Sponsor.objects.filter(is_active=1).order_by('?')[0:1][0]

        # if switch display, restart pagination
        if 'prevdisplay' in request.GET:
            page = 1

        for x in page_list:
            x.imgobj = x.get_best_img()
            if x.get_best_img():
                if family:
                    if family.family == 'Orchidaceae':
                        x.image_dir = 'utils/images/' + str(x.type) + '/'
                    else:
                        x.image_dir = 'utils/images/' + str(x.family) + '/'
                else:
                    x.image_dir = 'utils/images/' + str(x.family) + '/'

                x.image_file = x.get_best_img().image_file
                x.img_pid = x.get_best_img().pid
            else:
                x.image_file = 'utils/images/noimage_light.jpg'
            my_full_list.append(x)

    write_output(request, str(family))
    context = {'family':family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
        'page_list': my_full_list, 'display': display,
        'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
        'page': page, 'total': total, 'talpha': talpha,
        'ads_insert': ads_insert, 'sponsor': sponsor,
        'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
        'role': role,
    }

    return render(request, 'common/browsegen.html', context)


def browse(request):
    app = ''
    myspecies = ''
    author = ''
    family = ''
    newfamily = ''
    talpha = ''
    num_show = 5
    page_length = 20
    ads_insert = 0
    start_ad = 3        # Minimum images to display sponsor ad.
    sponsor = ''
    my_full_list = []
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
        if (family == '' or family == None) and 'family' in request.GET:
            family = request.GET['family']
    if family and family != 'other':
        family = Family.objects.get(family=family)
        app = family.application
    else:
        app = 'other'

    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request, family)
    if 'myspecies' in request.GET:
        myspecies = request.GET['myspecies']
        if myspecies:
            author = Photographer.objects.get(user_id=request.user)

    # reqsubgenus = reqsection = reqsubsection = reqseries = ''
    # subgenus_obj = section_obj = subsection_obj = series_obj = ''
    # subgenus_list = section_list = subsection_list = series_list = []
    page_range = page_list = last_page = next_page = prev_page = page = first_item = last_item = total = ''
    display = ''
    seed_genus = pollen_genus = seed = pollen = ''
    reqgenus = ''
    group = ''
    # Get requested parameters
    role = getRole(request)
    if 'display' in request.GET:
        display = request.GET['display']
    if not display:
        display = ''
    if 'type' in request.GET:
        type = request.GET['type']
    else:
        type = 'species'
    if 'group' in request.GET:
        group = request.GET['group']
    # else:
    #     group = ''

    # if type == 'species':
    #     if 'subgenus' in request.GET:
    #         reqsubgenus = request.GET['subgenus']
    #         if reqsubgenus:
    #             try:
    #                 subgenus_obj = Subgenus.objects.get(pk=reqsubgenus)
    #             except Subgenus.DoesNotExist:
    #                 subgenus_obj = ''
    #     if 'section' in request.GET:
    #         reqsection = request.GET['section']
    #         if reqsection:
    #             try:
    #                 section_obj = Section.objects.get(pk=reqsection)
    #             except Section.DoesNotExist:
    #                 section_obj = ''
    #     if 'subsection' in request.GET:
    #         reqsubsection = request.GET['subsection']
    #         if reqsubsection:
    #             try:
    #                 subsection_obj = Subsection.objects.get(pk=reqsubsection)
    #             except Subsection.DoesNotExist:
    #                 subsection_obj = ''
    #     if 'series' in request.GET:
    #         reqseries = request.GET['series']
    #         if reqseries:
    #             try:
    #                 series_obj = Series.objects.get(pk=reqseries)
    #             except Series.DoesNotExist:
    #                 series_obj = ''
    if type == 'hybrid':
        if 'seed_genus' in request.GET:
            seed_genus = request.GET['seed_genus']
        if seed_genus == 'clear':
            seed_genus = ''
        if 'pollen_genus' in request.GET:
            pollen_genus = request.GET['pollen_genus']
        if pollen_genus == 'clear':
            pollen_genus = ''
        if 'seed' in request.GET:
            seed = request.GET['seed']
        if 'pollen' in request.GET:
            pollen = request.GET['pollen']
    if 'genus' in request.GET:
        reqgenus = request.GET['genus']
        if reqgenus == '------':
            reqgenus = ''

    # genus, pid_list, intragen_list = getPartialPid(reqgenus, type, 'accepted', app)

    if app == 'orchidaceae':
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
    else:
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')

    pid_list = Species.objects.filter(type=type)
    # pid_list = pid_list.exclude(status='synonym')

    if subfamily:
        pid_list = pid_list.filter(gen__subfamily=subfamily)
    if subtribe:
        pid_list = pid_list.filter(gen__subtribe=subtribe)
    elif tribe:
        pid_list = pid_list.filter(gen__tribe=tribe)

    if reqgenus:
        try:
            genus = Genus.objects.get(genus=reqgenus)
        except Genus.DoesNotExist:
            genus = ''
        if genus:
            pid_list = pid_list.filter(genus=genus)
    else:
        reqgenus = ''
    if talpha:
        pid_list = pid_list.filter(species__istartswith=talpha)

    if pid_list and group:
        if group == 'succulent':
            pid_list = pid_list.filter(gen__is_succulent=True)
        elif group == 'carnivorous':
            pid_list = pid_list.filter(gen__is_carnivorous=True)

    if pid_list:
        if family:
            pid_list = pid_list.filter(gen__family=family.family)
        else:
            pid_list = pid_list.filter(gen__family__application='other')

        if display == 'checked':
            pid_list = pid_list.filter(num_image__gt=0)
        if type == 'species':
            pid_list = pid_list.filter(type='species')
        elif type == 'hybrid':
            pid_list = pid_list.filter(type='hybrid')
            if seed_genus and pollen_genus:
                pid_list = pid_list.filter(Q(hybrid__seed_genus=seed_genus) & Q(hybrid__pollen_genus=pollen_genus) | Q(
                        hybrid__seed_genus=pollen_genus) & Q(hybrid__pollen_genus=seed_genus))
            elif seed_genus:
                pid_list = pid_list.filter(Q(hybrid__seed_genus=seed_genus) | Q(hybrid__pollen_genus=seed_genus))
            elif pollen_genus:
                pid_list = pid_list.filter(Q(hybrid__seed_genus=pollen_genus) | Q(hybrid__pollen_genus=pollen_genus))
            if seed:
                pid_list = pid_list.filter(Q(hybrid__seed_species=seed) | Q(hybrid__pollen_species=seed))
            if pollen:
                pid_list = pid_list.filter(Q(hybrid__seed_species=pollen) | Q(hybrid__pollen_species=pollen))
        if myspecies and author:
            my_list = SpcImages.objects.filter(author_id=author).values_list('pid', flat=True).distinct()
            pid_list = pid_list.filter(pid__in=my_list)

        pid_list = pid_list.order_by('genus', 'species')
        total = len(pid_list)
        page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
            = mypaginator(request, pid_list, page_length, num_show)

        if len(page_list) > start_ad:
            ads_insert = int(random.random() * len(page_list)) + 1
            sponsor = Sponsor.objects.filter(is_active=1).order_by('?')[0:1][0]

        # if switch display, restart pagination
        # if 'prevdisplay' in request.GET:
        #     page = 1

        for x in page_list:
            if x.get_best_img():
                if family and family.family == 'Orchidaceae':
                    if type == 'species':
                        x.image_dir = 'utils/images/species/'
                    else:
                        x.image_dir = 'utils/images/hybrid/'
                else:
                    x.image_dir = 'utils/images/' + str(x.gen.family) + '/'
                x.image_file = x.get_best_img().image_file
                my_full_list.append(x)
            else:
                x.image_file = 'utils/images/noimage_light.jpg'
                my_full_list.append(x)

    # family_list, alpha = get_family_list(request)
    genus_list = Genus.objects.all()
    if family:
        genus_list = genus_list.filter(family=family.family)
    if display == 'checked':
        if type == 'species':
            genus_list = genus_list.filter(num_spcimage__gt=0)
        else:
            genus_list = genus_list.filter(num_hybimage__gt=0)
    write_output(request, str(family))
    context = {'family':family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
        'page_list': my_full_list, 'type': type, 'genus': reqgenus, 'display': display, 'genus_list': genus_list,
        'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
        'page': page, 'total': total, 'talpha': talpha, 'myspecies': myspecies,
        'ads_insert': ads_insert, 'sponsor': sponsor,
        'seed_genus': seed_genus, 'seed': seed, 'pollen_genus': pollen_genus, 'pollen': pollen,
        'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
        'role': role,
    }

    return render(request, 'common/browse.html', context)


def getPartialPid(reqgenus, type, status, app):
    if app == 'orchidaceae':
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
        Intragen = apps.get_model(app.lower(), 'Intragen')
        intragen_list = Intragen.objects.all()
        if status == 'synonym' or type == 'hybrid':
            intragen_list = []
    else:
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
        intragen_list = []

    pid_list = []
    pid_list = Species.objects.filter(type=type)
    pid_list = pid_list.exclude(status='synonym')

    if reqgenus:
        if reqgenus[0] != '*' and reqgenus[-1] != '*':
            try:
                genus = Genus.objects.get(genus=reqgenus)
            except Genus.DoesNotExist:
                genus = ''
            if genus:
                pid_list = pid_list.filter(genus=genus)
                if intragen_list:
                    intragen_list = intragen_list.filter(genus=genus)
            return genus, pid_list, intragen_list

        elif reqgenus[0] == '*' and reqgenus[-1] != '*':
            mygenus = reqgenus[1:]
            pid_list = pid_list.filter(genus__iendswith=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__iendswith=mygenus)

        elif reqgenus[0] != '*' and reqgenus[-1] == '*':
            mygenus = reqgenus[:-1]
            pid_list = pid_list.filter(genus__istartswith=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__istartswith=mygenus)
        elif reqgenus[0] == '*' and reqgenus[-1] == '*':
            mygenus = reqgenus[1:-1]
            pid_list = pid_list.filter(genus__icontains=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__icontains=mygenus)
    else:
        reqgenus = ''
    return reqgenus, pid_list, intragen_list


def get_species_list(application, family=None, subfamily=None, tribe=None, subtribe=None):
    Species = apps.get_model(application, 'Species')
    species_list = Species.objects.all()
    if subtribe:
        species_list = species_list.filter(gen__subtribe=subtribe)
    elif tribe:
        species_list = species_list.filter(gen__tribe=tribe)
    elif subfamily:
        species_list = species_list.filter(gen__subfamily=subfamily)
    return species_list
    # return species_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')


@login_required
def research(request):
    family = ''
    if 'family' in request.GET:
        family = request.GET['family']
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']

    from_path = pathinfo(request)
    write_output(request, '')
    context = { 'family': family, 'from_path': from_path,}
    return render(request, "common/research.html", context)


def commonname(request):
    talpha = ''
    family = 'other'
    role = ''
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'role' in request.GET:
        role = request.GET['role']
    # else:
    #     role = 'pub'

    print(">>> role = " + str(role))
    context = {'role': role,}
    if 'commonname' in request.GET:
        commonname = request.GET['commonname']
        if commonname == '':
            render(request, "common/research.html", context)

        species_list = Accepted.objects.filter(common_name__icontains=commonname).order_by('species')
        genus_list = Genus.objects.filter(common_name__icontains=commonname).order_by('genus')
        if 'talpha' in request.GET:
            talpha = request.GET['talpha']
        if talpha != '':
            species_list = species_list.filter(species__istartswith=talpha)
        total = len(species_list)
        print(">>> role = " + str(role))
        context = {'species_list': species_list, 'commonname': commonname, 'role': role,
                   'app': 'other', 'genus_list': genus_list,
                   'talpha': talpha, 'alpha_list': alpha_list}
        write_output(request, str(commonname))
        return render(request, "common/commonname.html", context)

    return render(request, "common/research.html", context)


def distribution(request):
    # For non-orchids only
    talpha = ''
    distribution = ''
    commonname = ''
    family = ''
    genus = ''
    commonname = ''
    crit = 0
    from_path = pathinfo(request)
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'role' in request.GET:
        role = request.GET['role']
    else:
        role = 'pub'
    if 'family' in request.GET:
        reqfamily = request.GET['family']
        family = Family.objects.get(family=reqfamily)
        if family != '' and family.family != 'Orchidaceae':
            crit = 1
    if 'genus' in request.GET:
        reqgenus = request.GET['genus']
        try:
            genus = Genus.objects.get(genus=reqgenus)
            crit = 1
        except Genus.DoesNotExist:
            genus = ''
    if 'distribution' in request.GET:
        distribution = request.GET['distribution']
        if distribution != '': crit = 1
    if 'commonname' in request.GET:
        commonname = request.GET['commonname']
        if commonname != '': crit = 1

    # if distribution == '' and commonname == '':
    #     render(request, "common/research.html", {'role': role,})

        # species_list = Accepted.objects.filter(distribution__icontains=distribution)
    species_list = []
    if crit:
        # initialize species_list if family is not orchidaceae
        if family != '' and family != 'Orchidaceae':            # Avoid large dataset in case of orchids
            species_list = Species.objects.filter(family=family)
        elif family != 'Orchidaceae':
            species_list = Species.objects.filter(family__application='other')

        # filter species list if Genus is requested
        if not genus:
            genus = ''
        if genus != '':
            if species_list:
                species_list = species_list.filter(genus=genus)
            else:
                # this is orchid case with a requested genus
                species_list = Species.objects.filter(genus=genus)
        if distribution:
            # build distribution list
            if family.family != 'Orchidaceae':
                dist_list = Distribution.objects.filter(dist_id__dist__icontains=distribution).values_list('pid', flat=True)
                species_list = Species.objects.filter(pid__in=dist_list)
            else:
                # Orchidaceae has a different Distribution class
                # Build distribution list
                dist_list = []
                subreg_list = SubRegion.objects.filter(name__icontains=distribution).values_list('code', flat=True)
                if len(subreg_list) > 0:
                    dist_list = Distribution.objects.filter(subregion_code__in=subreg_list).values_list('pid', flat=True)
                # requested distribution could elther be region or subregion
                reg_list = Region.objects.filter(name__icontains=distribution).values_list('id', flat=True)
                if len(reg_list) > 0:
                    dist_list = dist_list + Distribution.objects.filter(region_id__in=reg_list).values_list('pid', flat=True)
                dist_list = list(set(dist_list))

                # Filter species list
                if species_list:
                    species_list = species_list.filter(pid__in=dist_list)
                else:
                    species_list = Species.objects.filter(pid__in=dist_list)

        if commonname:
            name_list = Accepted.objects.filter(common_name__icontains=commonname).values_list('pid', flat=True)
            if species_list:
                species_list = species_list.filter(pid__in=name_list)
            else:
                # Orchidaceae with only common name requested
                species_list = Species.objects.filter(pid__in=name_list)
        if species_list:
            if 'talpha' in request.GET:
                talpha = request.GET['talpha']
            if talpha != '':
                species_list = species_list.filter(species__istartswith=talpha)
            species_list = species_list.order_by('species')
        total = len(species_list)
    context = {'species_list': species_list, 'distribution': distribution, 'commonname': commonname,
               'family': family, 'genus': genus,
               'role': role, 'app': 'other', 'talpha': talpha, 'alpha_list': alpha_list, 'from_path': from_path}
    write_output(request, str(distribution))
    return render(request, "common/distribution.html", context)


def mypaginator(request, full_list, page_length, num_show):
    page_list = []
    first_item = 0
    last_item = 0
    next_page = 0
    prev_page = 0
    last_page = 0
    page = 1
    page_range = ''
    total = len(full_list)
    if page_length > 0:
        paginator = Paginator(full_list, page_length)
        if 'page' in request.GET:
            page = request.GET.get('page', '1')
        else:
            page = 0
        if not page or page == 0:
            page = 1
        else:
            page = int(page)

        try:
            page_list = paginator.page(page)
            last_page = paginator.num_pages
            if page > last_page:
                page = last_page
        except EmptyPage:
            page_list = paginator.page(1)
            last_page = 1
        next_page = page+1
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
        page_range = paginator.page_range[start_index:end_index]
    return page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item


@login_required
def deletephoto(request, orid, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    next = ''

    try:
        image = UploadFile.objects.get(pk=orid)
    except UploadFile.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    try:
        species = Species.objects.get(pk=image.pid)
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
    if 'next' in request.GET:
        next = request.GET['next']
    role = getRole(request)
    if area == 'allpending':
        # bulk delete by curators from all_pending tab
        url = "%s&page=%s&type=%s&days=%d&family=" % (reverse('common:curate_pending'), page, ortype, days, family)
    elif next == 'curate_newupload':  # from curate_newupload (all rank 0)
        # Requested from all upload photos
        url = "%s?page=%s" % (reverse('common:curate_newupload'), page)
    if next == 'photos':
        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    else:
        url = "%s?role=%s&family=%s" % (reverse('common:curate_newupload'), role, family)

    # Finally remove file if exist
    if os.path.isfile(filename):
        os.remove(filename)

    write_output(request, str(family))
    return HttpResponseRedirect(url)


@login_required
def deletewebphoto(request, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
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

        if family.family == 'Orchidaceae' and species.type == 'hybrid':
            try:
                spc = HybImages.objects.get(id=orid)
            except HybImages.DoesNotExist:
                pass
        else:
            try:
                spc = SpcImages.objects.get(id=orid)
            except SpcImages.DoesNotExist:
                pass
        if spc:
            if spc.image_file:
                filename = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid", str(spc.image_file))
                if os.path.isfile(filename):
                    os.remove(filename)
            spc.delete()
    days = 7
    area = ''
    role = getRole(request)
    if 'area' in request.GET:
        area = request.GET['area']
    if 'days' in request.GET:
        days = request.GET['days']
    if area == 'allpending':  # from curate_pending (all rank 0)
        url = "%s?role=%s&page=%s&type=%s&days=%s" % (reverse('detail:curate_pending'), role, page, type, days)
    else:
        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    write_output(request, str(family))
    return HttpResponseRedirect(url)


@login_required
def approvemediaphoto(request, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
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
        msg = "uploaded file #" + str(orid) + "does not exist"
        url = "%s?role=%s&msg=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, msg, family)
        return HttpResponseRedirect(url)
    upls = UploadFile.objects.filter(pid=pid)

    for upl in upls:
        old_name = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
        tmp_name = os.path.join("/webapps/static/tmp/", str(upl.image_file_path))

        filename, ext = os.path.splitext(str(upl.image_file_path))
        if family.family != 'Orchidaceae' or species.type == 'species':
            if family.family == 'Orchidaceae':
                spc = SpcImages(pid=species.accepted, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            else:
                spc = SpcImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            spc.approved_by = request.user
            # hist = SpcImgHistory(pid=Accepted.objects.get(pk=pid), user_id=request.user, img_id=spc.id, action='approve file')
            if family.family == 'Orchidaceae':
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/species")
            else:
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(family))

            image_file = "spc_"
        else:
            spc = HybImages(pid=species.hybrid, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            spc.approved_by = request.user
            if family.family == 'Orchidaceae':
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid")
            else:
                newdir = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(family))
            image_file = "hyb_"

        image_file = image_file + str(format(upl.pid, "09d")) + "_" + str(format(upl.id, "09d"))
        new_name = os.path.join(newdir, image_file)
        if not os.path.exists(new_name + ext):
            try:
                shutil.copy(old_name, tmp_name)
                shutil.move(old_name, new_name + ext)
            except shutil.Error:
                # upl.delete()
                url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
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
                        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
                        return HttpResponseRedirect(url)
                    spc.image_file = image_file
                    break
                i += 1

        spc.save()
        # hist.save()
        upl.approved = True
        upl.delete(0)
    write_output(request, str(family))
    url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    return HttpResponseRedirect(url)


@login_required
def myphoto(request, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)
    if 'newfamily' in request.GET:
        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    if not role or request.user.tier.tier < 2:
        url = "%s?role=%s&family=%s" % (reverse('display:information', args=(pid,)), role, species.gen.family)
        return HttpResponseRedirect(url)
    else:
        author, author_list = get_author(request)

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, species, Species, UploadFile, SpcImages, HybImages, role)
    author = Photographer.objects.get(user_id=request.user)
    if author:
        public_list = public_list.filter(author=author)
        private_list = private_list.filter(author=author)
    context = {'species': species, 'private_list': private_list, 'public_list': public_list, 'upload_list': upload_list,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list, 'author_list': author_list,
               'pri': 'active', 'role': role, 'author': author, 'family': family,
               'app': family.application,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto.html', context)


def myphoto_list(request):
    author, author_list = get_author(request)
    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']

    # If change family
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']

    app_list = ['Orchidaceae', 'other']
    my_hyb_list = []
    my_list = []
    if role == 'pub':
        send_url = "%s?family=%s" % (reverse('common:browse'), family)
        return HttpResponseRedirect(send_url)
    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')
    if family:
        app_list = [family]

    for family in app_list:
    # for family in ['Orchidaceae']:
        Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request, family)
        # private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, '', Species, UploadFile, SpcImages, HybImages, role)
        my_tmp_list = Species.objects.exclude(status='synonym')

        my_upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
        my_spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
        if app == 'orchidaceae':
            my_hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())

        my_tmp_list = my_tmp_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_spc_list) | Q(pid__in=my_hyb_list))
        if len(my_tmp_list) > 0:
            for x in my_tmp_list:
                x.family = x.gen.family
            my_tmp_list = my_tmp_list.values('pid', 'binomial', 'family', 'author', 'year', 'type')
            if (family and family.family == 'Orchidaceae') or len(app_list) == 1:
                my_list = my_tmp_list
            else:
                my_list = my_list.union(my_tmp_list)

    family_list, alpha = get_family_list(request)

    context = {'my_list': my_list, 'family': family, 'app': app,
               'my_list': my_list,
               'role': role, 'brwspc': 'active', 'author': author,
               'author_list': author_list,
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'mylist': 'active',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_list.html', context)


@login_required
def myphoto_browse_spc(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    author, author_list = get_author(request)
    role = getRole(request)

    if role == 'pub':
        send_url = "%s?family=%s" % (reverse('common:browse'), family)
        return HttpResponseRedirect(send_url)
    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, '', Species, UploadFile, SpcImages, HybImages, role)

    pid_list = SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct()

    img_list = Species.objects.filter(pid__in=pid_list)
    if img_list:
        img_list = img_list.order_by('genus', 'species')

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)

    my_list = []
    for x in page_list:
        img = x.get_best_img_by_author(request.user.photographer.author_id)
        if img:
            my_list.append(img)

    context = {'my_list': my_list, 'type': 'species', 'family': family, 'app': app,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'brwspc': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,  'myspc': 'active',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_spc.html', context)


@login_required
def myphoto_browse_hyb(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if not family:
        family = 'other'
    role = getRole(request)
    if role == 'pub':
        send_url = "%s?tab=%s" % (reverse('common:browse'), 'sum')
        return HttpResponseRedirect(send_url)
    author, author_list = get_author(request)
    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, '', Species, UploadFile, SpcImages, HybImages, role)

    if family and family == 'other':
        pid_list = SpcImages.objects.filter(author=author).filter(gen__family__application='other').filter(pid__type='hybrid').values_list('pid', flat=True).distinct()
    else:
        if family.family == 'Orchidaceae':
            pid_list = HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct()
        else:
            pid_list = SpcImages.objects.filter(author=author).filter(gen__family=family.family).filter(pid__type='hybrid').values_list('pid', flat=True).distinct()

    img_list = Species.objects.filter(pid__in=pid_list)
    if img_list:
        img_list = img_list.order_by('genus', 'species')

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)
    my_list = []
    for x in page_list:
        img = x.get_best_img_by_author(request.user.photographer.author_id)
        if img:
            my_list.append(img)

    context = {'my_list': my_list, 'type': 'hybrid', 'family': family, 'app': app,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'brwhyb': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_hyb.html', context)


@login_required
def curate_newupload(request):
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)


    file_list = UploadFile.objects.all().order_by('-created_date')
    days = 7
    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)
    role = getRole(request)

    write_output(request, str(family))
    context = {'file_list': page_list, 'family': family,
               'tab': 'upl', 'role': role, 'upl': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app,
               }
    return render(request, "common/curate_newupload.html", context)


@login_required
def curate_pending(request):
    # This page is for curators to perform mass delete. It contains all rank 0 photos sorted by date reverse.
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)

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

    if ortype == 'hybrid' and family and family.family == 'Orchidaceae':
        file_list = SpcImages.objects.filter(rank=0).exclude(approved_by=1)
    else:
        file_list = HybImages.objects.filter(rank=0).exclude(approved_by=1)

    file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days))
    if days >= 30:
        file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days)).exclude(modified_date__gte=timezone.now() - timedelta(days=20))
    elif days >= 20:
        file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days)).exclude(modified_date__gte=timezone.now() - timedelta(days=7))
    file_list = file_list.order_by('-created_date')

    num_show = 5
    page_length = 100
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)

    role = getRole(request)
    write_output(request, str(family))
    context = {'file_list': page_list, 'type': ortype, 'family': family,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app,
               }
    return render(request, 'common/curate_pending.html', context)


@login_required
def curate_newapproved(request):
    # This page is for curators to perform mass delete. It contains all rank 0 photos sorted by date reverse.
    species = ''
    image = ''
    ortype = 'species'
    if request.user.is_authenticated and request.user.tier.tier < 2:
        return HttpResponseRedirect('/')

    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)

    if 'type' in request.GET:
        ortype = request.GET['type']
        # Request to change rank/quality
        if 'id' in request.GET:
            orid = int(request.GET['id'])
            try:
                image = SpcImages.objects.get(pk=orid)
            except SpcImages.DoesNotExist:
                species = ''
        if image:
            species = Species.objects.get(pk=image.pid_id)

    days = 3
    if 'days' in request.GET:
        days = int(request.GET['days'])
    file_list = SpcImages.objects.filter(rank__gt=0).exclude(approved_by=request.user)

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

    role = getRole(request)
    write_output(request, str(family))
    context = {'file_list': page_list, 'type': ortype, 'family': family,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app,
               }
    return render(request, 'common/curate_newapproved.html', context)


