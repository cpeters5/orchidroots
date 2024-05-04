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
from utils.views import write_output, getRole, paginator, get_author, get_taxonomy, getSuperGeneric, pathinfo, get_random_sponsor, get_application
from common.models import Family, Subfamily, Tribe, Subtribe, Region, SubRegion
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages
from accounts.models import User, Photographer

epoch = 1740
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
alpha_list = config.alpha_list
applications = config.applications

def getAllGenera():
    # Call this when Family is not provided
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    FuGenus = apps.get_model('fungi', 'Genus')
    return OrGenus, OtGenus


def getFamilyImage(family):
    SpcImages = apps.get_model(family.application, 'SpcImages')
    return SpcImages.objects.filter(rank__lt=7).order_by('-rank','quality', '?')[0:1][0]


def home(request):
    all_list = []
    role = getRole(request)
    num_samples = 1
    num_orchids = 4

    # Get sample images of orchids
    SpcImages = apps.get_model('orchidaceae', 'SpcImages')
    Genus = apps.get_model('orchidaceae', 'Genus')
    genera = Genus.objects.order_by('?')
    orcimage = []
    for x in genera:
        if x.get_best_img():
            orcimage = orcimage + [x.get_best_img()]
        if len(orcimage) > 3:
            break

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
    try:
        sample_genus = Genus.objects.filter(is_succulent=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    except:
        sample_genus = ''
    try:
        succulent_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        succulent_obj = ''
    all_list = all_list + [['Succulent', succulent_obj]]

    # get random carnivorous
    try:
        sample_genus = Genus.objects.filter(is_carnivorous=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    except:
        sample_genus = ''

    try:
        carnivorous_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        carnivorous_obj = ''

    all_list = all_list + [['Carnivorous', carnivorous_obj]]

    # get random parasitic
    try:
        sample_genus = Genus.objects.filter(is_parasitic=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    except:
        sample_genus = ''

    try:
        parasitic_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        parasitic_obj = ''
    all_list = all_list + [['Parasitic', parasitic_obj]]

    num_samples = 1
    # Get random fungi families
    SpcImages = apps.get_model('fungi', 'SpcImages')
    Genus = apps.get_model('fungi', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            fungi_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            fungi_obj = ''
        all_list = all_list + [["Fungi", fungi_obj]]

    num_samples = 1
    # Get random bird families
    SpcImages = apps.get_model('aves', 'SpcImages')
    Genus = apps.get_model('aves', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            aves_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            aves_obj = ''
        all_list = all_list + [["Aves", aves_obj]]

    num_samples = 1
    # Get random bird families
    SpcImages = apps.get_model('animalia', 'SpcImages')
    Genus = apps.get_model('animalia', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            animalia_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            animalia_obj = ''
        all_list = all_list + [["Aves", animalia_obj]]

    # Advertisement
    # num_blocks = 5
    # ads_insert = int(random.random() * num_blocks) + 1
    # sponsor = get_random_sponsor()
    random.shuffle(all_list)

    context = {'orcimage': orcimage, 'all_list': all_list, 'succulent_obj': succulent_obj,
               # 'orchid_list': orchid_list,
               'carnivorous_obj': carnivorous_obj, 'parasitic_obj': parasitic_obj, 'role': role,
               # 'ads_insert': ads_insert, 'sponsor': sponsor,
               }
    return render(request, 'home.html', context)


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
    family_list, alpha = get_taxonomy(request)
    context = {'family_list': family_list,
               }
    return render(request, "common/taxonomy.html", context)


@login_required
def genera(request):
    author = ''
    path = resolve(request.path).url_name
    talpha = request.GET.get('talpha','')
    subfamily = ''
    tribe = ''
    subtribe = ''
    family_list = []
    family = request.GET.get('family','')
    try:
        family = Family.objects.get(family=family)
        app = family.application
        family_list = Family.objects.filter(application=app)
    except Family.DoesNotExist:
        family = ''
        app = request.GET.get('app',None)
        if app == 'orchidaceae':
            family = Family.objects.get(family='Orchidaceae')
        else:
            family_list = Family.objects.filter(application=app)

    if app:
        Genus = apps.get_model(app, 'Genus')
    else:
        return render(request, "common/family.html", {})
    if family_list and talpha:
        family_list = family_list.filter(family__istartswith=talpha)

    if family:
        newfamily, subfamily, tribe, subtribe = getSuperGeneric(request)
        if subtribe:
            genus_list = Genus.objects.filter(subtribe=subtribe)
        elif tribe:
            genus_list = Genus.objects.filter(tribe=tribe)
        elif subfamily:
            genus_list = Genus.objects.filter(subfamily=subfamily)
        elif family:
            genus_list = Genus.objects.filter(family=family.family)
    elif family_list:
        # No family (e.g. first landing on this page), show all non-Orchidaceae genera
        # OrGenus, OtGenus = getAllGenera()
        Genus = apps.get_model(app, 'Genus')
        genus_list = Genus.objects.filter(family__in=family_list.values_list('family', flat=True))
    else:
        genus_list = ''
    # If private request
    if genus_list or family:
        # Complete building genus list
        if talpha:
            genus_list = genus_list.filter(genus__istartswith=talpha)

        total = len(genus_list)
        write_output(request, str(family))
        context = {
            'genus_list': genus_list,  'app': app, 'total':total, 'talpha': talpha,
            'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
            'alpha_list': alpha_list,
            'path': path
        }
        return render(request, "common/genera.html", context)
    else:
        context = {
            'app': app, 'total':len(family_list), 'talpha': talpha,
            'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
            'family_list': family_list,
            'alpha_list': alpha_list,
            'path': path
        }
        return render(request, "common/family.html", context)


@login_required
def species(request):
    # path = resolve(request.path).url_name
    path_link = 'information'
    talpha = request.GET.get('talpha','')
    if str(request.user) == 'chariya':
        path_link = 'photos'
    req_type = request.GET.get('type', 'species')
    req_family = request.GET.get('family', None)
    req_genus = request.GET.get('genus', None)
    alpha = request.GET.get('alpha', '')
    syn = request.GET.get('syn', None)

    # If Orchidaceae, go to full table.
    if req_family == 'Orchidaceae':
        if req_type == 'hybrid':
            url = "%s?family=%s&genus=%s&type=hybrid" % (reverse('orchidaceae:hybrid'), req_family, req_genus)
        else:
            url = "%s?family=%s&genus=%s&type=species" % (reverse('orchidaceae:species'), req_family, req_genus)

        return HttpResponseRedirect(url)
    max_items = 3000
    genus_list = []
    species_list = []
    if req_family:
        try:
            req_family = Family.objects.get(family=req_family)
            app = req_family.application
        except Family.DoesNotExist:
            app = ''
            req_family = ''
    if req_family and req_family != '':
        Genus = apps.get_model(app, 'Genus')
        Species = apps.get_model(app, 'Species')
        if req_genus != '':
            try:
                req_genus = Genus.objects.get(genus=req_genus)
            except Genus.DoesNotExist:
                req_genus = ''
            # If genus object found, build species list
            if req_genus != '':
                species_list = Species.objects.filter(genus=req_genus).filter(family=req_family)
                if req_type != '':
                    species_list = species_list.filter(type=req_type)
                if talpha != '':
                    species_list = species_list.filter(species__istartswith=talpha)
                if syn == 'N':
                    species_list = species_list.exclude(status='synonym')
                    syn = 'N'
                else:
                    syn = 'Y'
        else:
            # If requested genus in not valid return list of genera
            genus_list = Genus.objects.filter(family=req_family)
    elif req_genus != '':
        # Get list of req_genus species from all applications
        species_list = []
        for app in applications:
            # Go through all applications
            Genus = apps.get_model(app, 'Genus')
            Species = apps.get_model(app, 'Species')
            try:
                req_genus = Genus.objects.get(genus=req_genus)
            except Genus.DoesNotExist:
                continue
            species_list = None
            if req_genus != '':
                this_species_list = Species.objects.filter(genus=req_genus)
                if req_type != '':
                    this_species_list = this_species_list.filter(type=req_type)
                if talpha != '':
                    this_species_list = this_species_list.filter(species__istartswith=talpha)
                if syn == 'N':
                    this_species_list = this_species_list.exclude(status='synonym')
                    syn = 'N'
                else:
                    syn = 'Y'
                if this_species_list:
                    if not species_list:
                        species_list = this_species_list
                    else:
                        species_list = species_list.union(this_species_list)
    if not genus_list and not species_list and not req_genus:
        #     No filter requested, return family list
        family_list = Family.objects.all()
        req_app = request.GET.get('app', None)
        if req_app in applications:
            family_list = family_list.filter(application=req_app)
        context = {
            'family_list': family_list,  'app': req_app,
            'alpha_list': alpha_list,
        }
        return render(request, "common/family.html", context)

    total = len(species_list)
    msg = ''
    if total > max_items:
        species_list = species_list[0:max_items]
        msg = "List too long, truncated to " + str(max_items) + ". Please refine your search criteria."
        total = max_items
    role = ''
    if request.user.tier.tier > 2:
        role = 'cur'
    write_output(request, str(req_family))
    context = {
        'genus': req_genus, 'genus_list': genus_list, 'species_list': species_list, 'app': app, 'total':total,
        'syn': syn, 'type': req_type, 'role':role,
        'family': req_family,
        'alpha_list': alpha_list, 'talpha': talpha,
        'msg': msg, 'path_link': path_link, 'from_path': 'species',
    }
    return render(request, "common/species.html", context)


def rank_update(request, SpcImages):
    rank = int(request.GET.get('rank', 0))
    orid = int(request.GET.get('id', 0))
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
        quality = int(request.GET.get('quality', 3))
        orid = int(request.GET.get('id', 0))
        image = ''
        try:
            image = SpcImages.objects.get(pk=orid)
        except SpcImages.DoesNotExist:
            return 3
        image.quality = quality
        image.save()
    return


def newbrowse(request):
    # Application must be in request
    talpha = request.GET.get('talpha','')
    if talpha == 'ALL':
        talpha = ''

    app = request.GET.get('app','')
    family = request.GET.get('family', '')
    genus = request.GET.get('genus', '')

    # if app == 'orchidaceae':
        # Special case for orchids
        # family = 'Orchidaceae'

    if family and not genus:
        # Family is requested
        try:
            family = Family.objects.get(family=family)
        except Family.DoesNotExist:
            family = None

        if family:
            app = family.application
            Genus = apps.get_model(app.lower(), 'Genus')
            SpcImages = apps.get_model(app.lower(), 'SpcImages')
            # genera = Genus.objects.filter(family=family)
            if app == 'orchidaceae':
                genera = SpcImages.objects.filter(image_file__isnull=False).order_by('gen').values_list('gen',
                                                                                                        flat=True).distinct()
            else:
                genera = SpcImages.objects.filter(image_file__isnull=False).filter(family=family).order_by(
                    'gen').values_list('gen', flat=True).distinct()
            if genera:
                genus_list = []
                genera = set(genera)
                genlist = Genus.objects.filter(pid__in=genera)
                if talpha:
                    genlist = genlist.filter(genus__istartswith=talpha)
                genlist = genlist.order_by('genus')
                for gen in genlist:
                    genus_list = genus_list + [gen.get_best_img()]
                context = {'genus_list': genus_list, 'family': family, 'app': family.application, 'talpha': talpha,
                           'alpha_list': alpha_list, }
                return render(request, 'common/newbrowse.html', context)


    if app in applications:
        # If app is requested, find family_list and sample image by family
        # If family is requested, get sample list by genera
        genus = request.GET.get('genus', None)
        if genus:
            # Go to browse genus.species
            Genus = apps.get_model(app.lower(), 'Genus')
            Species = apps.get_model(app.lower(), 'Species')
            try:
                genus = Genus.objects.get(genus=genus)
            except Genus.DoesNotExist:
                genus = ''
            if genus:
                species = Species.objects.filter(genus=genus)
                if not talpha and app == 'orchidaceae':
                    talpha = 'A'
                if talpha:
                    species = species.filter(species__istartswith=talpha)
                species = species.order_by('species')
                if len(species) > 500:
                    species = species[0: 500]
                species_list = []
                for x in species:
                    spcimage = x.get_best_img()
                    if spcimage:
                        species_list = species_list + [spcimage]
                context = {'species_list': species_list, 'family': genus.family, 'app': genus.family.application, 'genus': genus, 'talpha': talpha, 'alpha_list': alpha_list,}
                return render(request, 'common/newbrowse.html', context)

        # Building sample by families
        families = Family.objects.filter(application=app)
        if talpha:
            families = families.filter(family__istartswith=talpha)
        families = families.order_by('family')
        Genus = apps.get_model(app.lower(), 'Genus')
        family_list = []
        for fam in families:
            genimage = Genus.objects.filter(family=fam.family).order_by('?')[0:1]
            if len(genimage) > 0:
                family_list = family_list + [(genimage[0])]
        context = {'family_list': family_list, 'app': app, 'talpha': talpha, 'alpha_list': alpha_list,}
        return render(request, 'common/newbrowse.html', context)

    # Bad application, and neither families nor genus are valid, list all genera in the app
    write_output(request, str(family))
    return HttpResponseRedirect('/')

    # Now we get family_list of sample genera


# def getPartialPid(reqgenus, type, status, app):
#     if app == 'orchidaceae':
#         Genus = apps.get_model(app.lower(), 'Genus')
#         Species = apps.get_model(app.lower(), 'Species')
#         Intragen = apps.get_model(app.lower(), 'Intragen')
#         intragen_list = Intragen.objects.all()
#         if status == 'synonym' or type == 'hybrid':
#             intragen_list = []
#     else:
#         Genus = apps.get_model(app.lower(), 'Genus')
#         Species = apps.get_model(app.lower(), 'Species')
#         intragen_list = []
#
#     pid_list = []
#     pid_list = Species.objects.filter(type=type)
#     pid_list = pid_list.exclude(status='synonym')
#
#     if reqgenus:
#         if reqgenus[0] != '*' and reqgenus[-1] != '*':
#             try:
#                 genus = Genus.objects.get(genus=reqgenus)
#             except Genus.DoesNotExist:
#                 genus = ''
#             if genus:
#                 pid_list = pid_list.filter(genus=genus)
#                 if intragen_list:
#                     intragen_list = intragen_list.filter(genus=genus)
#             return genus, pid_list, intragen_list
#
#         elif reqgenus[0] == '*' and reqgenus[-1] != '*':
#             mygenus = reqgenus[1:]
#             pid_list = pid_list.filter(genus__iendswith=mygenus)
#             if intragen_list:
#                 intragen_list = intragen_list.filter(genus__iendswith=mygenus)
#
#         elif reqgenus[0] != '*' and reqgenus[-1] == '*':
#             mygenus = reqgenus[:-1]
#             pid_list = pid_list.filter(genus__istartswith=mygenus)
#             if intragen_list:
#                 intragen_list = intragen_list.filter(genus__istartswith=mygenus)
#         elif reqgenus[0] == '*' and reqgenus[-1] == '*':
#             mygenus = reqgenus[1:-1]
#             pid_list = pid_list.filter(genus__icontains=mygenus)
#             if intragen_list:
#                 intragen_list = intragen_list.filter(genus__icontains=mygenus)
#     else:
#         reqgenus = ''
#     return reqgenus, pid_list, intragen_list


def distribution(request):
    # For non-orchids only
    talpha = ''
    distribution = ''
    genus = ''
    commonname = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    crit = 0
    from_path = pathinfo(request)
    role = request.GET.get('role', 'pub')
    family = request.GET.get('family', None)
    if family:
        try:
            family = Family.objects.get(family=family)
            if family != '' and family.family != 'Orchidaceae':
                crit = 1
            app = family.application
        except Family.DoesNotExist:
            family = ''
            app = None
    else:
        app = request.GET.get('app', None)
        if not app:
            return render(request, "common/distribution.html", {})
    Genus = apps.get_model(app, 'Genus')
    Species = apps.get_model(app, 'Species')
    Distribution = apps.get_model(app, 'Distribution')

    reqgenus = request.GET.get('genus', None)
    if genus:
        try:
            genus = Genus.objects.get(genus=reqgenus)
            crit = 1
        except Genus.DoesNotExist:
            genus = None

    distribution = request.GET.get('distribution', '')
    if distribution != '': crit = 1

    species_list = []
    if crit:
        # initialize species_list if family is not orchidaceae
        species_list = Species.objects.filter(family=family)

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

        if species_list:
            talpha = request.GET.get('talpha', '')
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
        page = int(request.GET.get('page', '1'))

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



def delete_image_files(app, spc_obj, orid):
    # look in uploaded files first
    try:
        UploadFile = apps.get_model(app, 'UploadFile')
        upl = UploadFile.objects.get(id=orid)
        filename = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
        if os.path.isfile(filename):
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass
        upl.delete()
    except UploadFile.DoesNotExist:
        pass

    # Then look in the system
    if spc_obj.type == 'hybrid' and spc_obj.family.family == 'Orchidaceae':
        try:
            HybImages = apps.get_model(app, 'HybImages')
            spc = HybImages.objects.get(id=orid)
            if spc.image_file:
                filename = os.path.join(settings.STATIC_ROOT, str(spc.image_dir() + spc.image_file))
                if os.path.isfile(filename):
                    try:
                        os.remove(filename)
                    except FileNotFoundError:
                        pass
                filename = os.path.join(settings.STATIC_ROOT, str(spc.thumb_dir() + spc.image_file))
                if os.path.isfile(filename):
                    try:
                        os.remove(filename)
                        # print("Thumb File deleted successfully.")
                    except FileNotFoundError:
                        pass
            spc.delete()
        except HybImages.DoesNotExist:
            pass
    else:
        try:
            SpcImages = apps.get_model(app, 'SpcImages')
            spc = SpcImages.objects.get(id=orid)

            if spc.image_file:
                filename = os.path.join(settings.STATIC_ROOT, str(spc.image_dir()), str(spc.image_file))
                if os.path.isfile(filename) and spc.image_file:
                    os.remove(filename)


                filename = os.path.join(settings.STATIC_ROOT, str(spc.thumb_dir()), str(spc.image_file))
                if os.path.isfile(filename):
                    os.remove(filename)
            spc.delete()
        except SpcImages.DoesNotExist:
            pass


@login_required
def deletephoto(request, orid, pid):
    family = request.GET.get('family', None)
    try:
        family = Family.objects.get(family=family)
        app = family.application

    except Family.DoesNotExist:
        family = ''
        app = None

    if not family:
        app = request.GET.get('app', None)
        if app not in applications:
            app = None
    if not app:
        # url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), '', '')
        return render(request, "display/photos.html", {})

    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    delete_image_files(app, species, orid)

    # (Historical) synonym files may be tagged as accepted species
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=species.pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    delete_image_files(app, species, orid)

    next = request.GET.get('next','photos')
    role = getRole(request)
    if next == 'photos':
        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    else:
        url = "%s?role=%s&family=%s" % (reverse('common:curate_newupload'), role, family)

    write_output(request, str(family))
    return HttpResponseRedirect(url)



@login_required
def deletewebphoto(request, pid):
    family = request.GET.get('family', None)
    try:
        family = Family.objects.get(family=family)
        if family and family.family != 'Orchidaceae':
            crit = 1
        app = family.application

    except Family.DoesNotExist:
        family = ''
        app = None
    if not family:
        app = request.GET.get('app', None)
        if app not in applications:
            app = None
    if not app:
        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), '', '')
        return HttpResponseRedirect(url)
        # return render(request, "display/photos.html", {})

    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')

    species = Species.objects.get(pk=pid)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    orid = int(request.GET.get('id', None))
    if orid:
        delete_image_files(app, species, orid)

    days = 7
    area = ''
    role = getRole(request)
    area = request.GET.get('area', None)
    days = int(request.GET.get('days', 3))
    page = int(request.GET.get('page', 1))
    if area == 'allpending':  # from curate_pending (all rank 0)
        url = "%s?role=%s&page=%s&type=%s&days=%s" % (reverse('detail:curate_pending'), role, page, type, days)
    else:
        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    write_output(request, str(family))
    return HttpResponseRedirect(url)


@login_required
def approvemediaphoto(request, pid):
    # !!! UNTESTED
    # Move to a utiles method
    family = request.GET.get('family', None)
    if family:
        try:
            family = Family.objects.get(family=family)
            if family.family != 'Orchidaceae':
                crit = 1
            app = family.application

        except Family.DoesNotExist:
            family = None
            app = None
    if not family:
        app = request.GET.get('app', None)
        if app not in applications:
            app = None
        else:
            url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), '', '')
            return render(request, "display/photos.html", {})

    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')
    UploadFile = apps.get_model(app, 'UploadFile')

    species = Species.objects.get(pk=pid)
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    image_dir = "utils/images/"
    if family.family == 'Orchidaceae':
        if species.type == 'species':
            image_dir = image_dir + "species"
        else:
            image_dir = image_dir + "hybrid"
    else:
        image_dir = image_dir + str(family)
    newdir = os.path.join(settings.STATIC_ROOT, image_dir)
    # Only curator can approve
    role = getRole(request)
    if role != "cur":
        message = 'You do not have privilege to approve photos.'
        return HttpResponse(message)

    orid = int(request.GET.get('id', ''))
    if not orid:
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
            SpcImages = apps.get_model(app, 'SpcImages')
            if family.family == 'Orchidaceae':
                spc = SpcImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            else:
                SpcImages = apps.get_model(app, 'SpcImages')
                spc = SpcImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            spc.approved_by = request.user
            image_file = "spc_"
        else:
            spc = HybImages(pid=species.hybrid, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date, source_url=upl.source_url)
            spc.approved_by = request.user
            # if family.family == 'Orchidaceae':
            #     newdir = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid")
            # else:
            #     newdir = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(family))
            image_file = "hyb_"

        image_file = image_file + str(format(upl.pid.pid, "09d")) + "_" + str(format(upl.id, "09d"))
        newpath = os.path.join(newdir, image_file)
        if not os.path.exists(newpath + ext):
            try:
                shutil.copy(old_name, tmp_name)
                shutil.move(old_name, newpath + ext)
            except shutil.Error:
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
        # spc.image_file_path = image_dir + image_file
        spc.save()
        upl.approved = True
        upl.delete(0)
    write_output(request, str(family))
    url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, family)
    return HttpResponseRedirect(url)


@login_required
def myphoto(request, pid):
    role = getRole(request)
    app, family = get_application(request)
    if app == '':
        return HttpResponseRedirect('/')

    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')
    UploadFile = apps.get_model(app, 'UploadFile')
    SpcImages = apps.get_model(app, 'SpcImages')
    if app == 'orchidaceae':
        HybImages = apps.get_model(app, 'HybImages')

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

    if species:
        syn_list = Synonym.objects.filter(acc_id=species.pid).values_list('spid')
        if app == 'orchidaceae' and species.type == 'hybrid':
            if species.status == 'synonym':      # input pid is a synonym, just get images of the requested synonym
                public_list = HybImages.objects.filter(pid=species.pid)  # public photos
            else:                   # input pid is an accepted species, include images of its synonyms
                public_list = HybImages.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # public photos
        else:
            if species.status == 'synonym':
                public_list = SpcImages.objects.filter(pid=species.pid)  # public photos
            else:
                public_list = SpcImages.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # public photos
        upload_list = UploadFile.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # All upload photos
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            upload_list = upload_list.filter(author=author) # Private photos
            private_list = private_list.filter(author=author) # Private photos

    else:
        private_list = public_list = upload_list = []

    if not request.user.is_authenticated or request.user.tier.tier < 2:  # Display only rank > 0
        public_list  = public_list.filter(rank__gt=0)
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

    # If change family
    app_list = applications
    my_hyb_list = []
    my_list = []
    if role == 'cur':
        author = request.GET.get('author', None)
        if author:
            author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')
    app, family = get_application(request)
    if family:
        app_list = [family]

    for family in app_list:
        app, family = get_application(request)
        Species = apps.get_model(app, 'Species')
        UploadFile = apps.get_model(app, 'UploadFile')
        SpcImages = apps.get_model(app, 'SpcImages')
        my_tmp_list = Species.objects.exclude(status='synonym')
        my_upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
        my_spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
        if app == 'orchidaceae':
            HybImages = apps.get_model(app, 'HybImages')
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

    context = {'my_list': my_list, 'family': family, 'app': app,
               'my_list': my_list,
               'role': role, 'brwspc': 'active', 'author': author,
               'author_list': author_list,
               'alpha_list': alpha_list, 'mylist': 'active',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_list.html', context)


@login_required
def myphoto_browse_spc(request):
    author, author_list = get_author(request)
    role = getRole(request)

    app, family = get_application(request)
    if app == '':
        return HttpResponseRedirect('/')

    Species = apps.get_model(app, 'Species')
    SpcImages = apps.get_model(app, 'SpcImages')

    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    pid_list = SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct()

    img_list = Species.objects.filter(pid__in=pid_list).order_by('genus', 'species')
    # if img_list:
    #     img_list = img_list.order_by('genus', 'species')

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)

    my_list = []
    for x in page_list:
        img = x.get_best_img_by_author(request.user.photographer.author_id)
        if img:
            my_list.append(img)

    myspecies_list = img_list.filter(type='species')
    myhybrid_list = img_list.filter(type='hybrid')

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
    app, family = get_application(request)
    if app == '':
        return HttpResponseRedirect('/')

    Species = apps.get_model(app, 'Species')
    SpcImages = apps.get_model(app, 'SpcImages')
    if app == 'orchidaceae':
        HybImages = apps.get_model(app, 'HybImages')
    else:
        HybImages = apps.get_model(app, 'SpcImages')


    if not family:
        family = 'other'
    role = getRole(request)
    author, author_list = get_author(request)
    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

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
               'role': role, 'brwhyb': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_hyb.html', context)


@login_required
def curate_newupload(request):
    app, family = get_application(request)
    if app == '':
        return HttpResponseRedirect('/')

    UploadFile = apps.get_model(app, 'UploadFile')

    file_list = UploadFile.objects.all().order_by('-modified_date')
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
    app, family = get_application(request)
    if app == '':
        return HttpResponseRedirect('/')

    SpcImages = apps.get_model(app, 'SpcImages')
    if app == 'orchidaceae':
        HybImages = apps.get_model(app, 'HybImages')

    ortype = request.GET.get('type', '')

    days = 7
    days = int(request.GET.get('days', 3))
    if not days:
        days = 7

    if ortype == 'hybrid' and family and family.family == 'Orchidaceae':
        file_list = HybImages.objects.filter(rank=0).exclude(approved_by=1)
    else:
        file_list = SpcImages.objects.filter(rank=0).exclude(approved_by=1)

    # file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days))
    # if days >= 30:
    #     file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days)).exclude(modified_date__gte=timezone.now() - timedelta(days=20))
    # elif days >= 20:
    #     file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days)).exclude(modified_date__gte=timezone.now() - timedelta(days=7))
    # file_list = file_list.order_by('-modified_date')

    days = int(request.GET.get('days', 3))
    file_list = file_list.filter(rank=0)
    file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days))
    if days == 7:
        file_list = file_list.exclude(modified_date__gt=timezone.now() - timedelta(days=3))
    elif days == 20:
        file_list = file_list.exclude(modified_date__gt=timezone.now() - timedelta(days=7))
    elif days == 30:
        file_list = file_list.exclude(modified_date__gt=timezone.now() - timedelta(days=20))

    file_list = file_list.order_by('-modified_date')


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
    app, family = get_application(request)
    if app == '':
        return HttpResponseRedirect('/')

    SpcImages = apps.get_model(app, 'SpcImages')
    Species = apps.get_model(app, 'Species')

    ortype = request.GET.get('type', None)
    # Request to change rank/quality
    orid = int(request.GET.get('id', 0))
    try:
        image = SpcImages.objects.get(pk=orid)
    except SpcImages.DoesNotExist:
        species = ''
    if image:
        species = Species.objects.get(pk=image.pid_id)

    days = int(request.GET.get('days', 3))
    file_list = SpcImages.objects.filter(rank__gt=0)
    file_list = file_list.filter(modified_date__gte=timezone.now() - timedelta(days=days))
    if days == 7:
        file_list = file_list.exclude(modified_date__gt=timezone.now() - timedelta(days=3))
    elif days == 20:
        file_list = file_list.exclude(modified_date__gt=timezone.now() - timedelta(days=7))
    elif days == 30:
        file_list = file_list.exclude(modified_date__gt=timezone.now() - timedelta(days=20))

    file_list = file_list.order_by('-modified_date')
    if species:
        rank = int(request.GET.get('rank', 0))
        orid = int(request.GET.get('id', None))
        image = ''

        try:
            image = SpcImages.objects.get(pk=orid)
            image.rank = rank
            image.save()
        except SpcImages.DoesNotExist:
            pass

        # rank_update(request, species)
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

