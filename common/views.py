import string
import re
import os
import logging
import random
import shutil

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
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
from utils.views import write_output, getRole, get_author, get_reqauthor, get_taxonomy, getSuperGeneric, pathinfo, get_random_sponsor, get_application
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
default_genus = config.default_genus

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


def taxonomy(request, app=None):
    if not app:
        app = request.GET.get('app', 'orchidaceae')
        if app not in applications:
            app = 'orchidaceae'

        canonical_url = request.build_absolute_uri(f'/common/genera/{app}/')
        # Redirect permanent to preferred url
        return HttpResponsePermanentRedirect(canonical_url)

    canonical_url = request.build_absolute_uri(f'/common/taxonomy/{app}/')
    alpha = request.GET.get('alpha','')
    family_list = get_taxonomy(request, app, alpha)
    context = {'family_list': family_list, 'app': app, 'alpha': alpha, 'alpha_list': alpha_list,
               'canonical_url': canonical_url,
               }
    return render(request, "common/taxonomy.html", context)


def family(request, app=None):
    if not app:
        app = request.GET.get('app', '')
        if not app or app not in applications:
            app = 'orchidaceae'

        canonical_url = request.build_absolute_uri(f'/common/genera/{app}/')
        # Redirect permanent to preferred url
        return HttpResponsePermanentRedirect(canonical_url)

    canonical_url = request.build_absolute_uri(f'/common/family/{app}/')
    alpha = request.GET.get('alpha','')
    family_list = Family.objects.filter(application=app)
    if alpha:
        family_list = family_list.filter(family__istartswith=alpha)

    context = {
        'app': app, 'alpha': alpha,
        'family': family,
        'family_list': family_list,
        'alpha_list': alpha_list,
        'canonical_url': canonical_url,
    }
    return render(request, "common/family.html", context)


def genera(request, app=None):
    # If app is not given (non canonical_url for old code)
    if not app:
        app = request.GET.get('app', '')
        if not app or app not in applications:
            app = 'orchidaceae'

        canonical_url = request.build_absolute_uri(f'/common/genera/{app}/')
        # Redirect permanent to preferred url
        return HttpResponsePermanentRedirect(canonical_url)

    canonical_url = request.build_absolute_uri(f'/common/genera/{app}/')
    alpha = request.GET.get('alpha','')
    subfamily = ''
    tribe = ''
    subtribe = ''
    family_list = []
    family = request.GET.get('family', '')
    if family:
        try:
            family = Family.objects.get(family=family)
        except Family.DoesNotExist:
            family = ''
    if isinstance(family, Family) and family.application != app:
        family = ''

    Genus = apps.get_model(app, 'Genus')
    if app == 'orchidaceae':
        # Orchid genera
        subfamily, tribe, subtribe = getSuperGeneric(request)
        # subfamily = request.GET.get('subfamily', '')
        # tribe = request.GET.get('tribe', '')
        # subtribe = request.GET.get('subtribe', '')

        genus_list = Genus.objects.exclude(status='synonym')
        if subtribe:
            genus_list = genus_list.filter(subtribe=subtribe)
        if tribe:
            genus_list = genus_list.filter(tribe=tribe)
        if subfamily:
            genus_list = genus_list.filter(subfamily=subfamily)

    else:
        if not family:
            genus_list = Genus.objects.all()
        else:
            genus_list = Genus.objects.filter(family=family)


    # Complete building genus list
    if alpha:
        genus_list = genus_list.filter(genus__istartswith=alpha)


    write_output(request, str(family))
    context = {
        'genus_list': genus_list,  'app': app, 'alpha': alpha,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
        'alpha_list': alpha_list,
        'canonical_url': canonical_url,
    }
    return render(request, "common/genera.html", context)


def species(request, app=None):
    # path = resolve(request.path).url_name
    # Determine application if not given

    no_app = 0;
    if not app:
        no_app = 1
        app = request.GET.get('app', '')
        if not app or app not in applications:
            #  Default to orchid
            app = 'orchidaceae'

    syn = request.GET.get('syn', '')
    req_genus = request.GET.get('genus', '')
    if not req_genus:
        req_genus = default_genus[app]

    canonical_url = request.build_absolute_uri(f'/common/species/{app}/?genus={req_genus}')
        # Redirect permanent to preferred url
    if no_app:
        return HttpResponsePermanentRedirect(canonical_url)

    alpha = request.GET.get('alpha','')
    role = request.GET.get('role','pub')
    req_type = request.GET.get('type', 'species')

    req_family = request.GET.get('family', '')
    # if new family requested, it must be family in the same application
    if req_family:
        try:
            req_family = Family.objects.get(family=req_family)
            app = req_family.application
        except Family.DoesNotExist:
            req_family = ''
        # Ifnore requested family if it is not in the application.
        if isinstance(req_family, Family) and req_family.application != app:
            req_family = ''


    # Define a default genus for large sections

    # hybrids are in Orchidaceae only.
    if req_family == 'Orchidaceae':
        if req_type == 'hybrid':
            url = "%s?family=%s&genus=%s&type=hybrid&alpha=%s" % (reverse('orchidaceae:hybrid'), req_family, req_genus, alpha)
        # else:
        #     url = "%s?family=%s&genus=%s&type=species&alpha=%s" % (reverse('orchidaceae:species'), req_family, req_genus, alpha)
            return HttpResponseRedirect(url)

    max_items = 3000
    Genus = apps.get_model(app, 'Genus')
    Species = apps.get_model(app, 'Species')
    species_list = []

    if req_genus:
        # Case 1: Genus is given, list only species of that genus
        try:
            req_genus = Genus.objects.get(genus=req_genus)
        except Genus.DoesNotExist:
            # No genus found in this category, go to the next.
            req_genus = ''
        if req_genus:
            species_list = Species.objects.filter(genus=req_genus)
            # if req_type:
            #     this_species_list = this_species_list.filter(type=req_type)
            # if alpha:
            #     this_species_list = this_species_list.filter(species__istartswith=alpha)
            # if syn == 'N':
            #     this_species_list = this_species_list.exclude(status='synonym')
            #     syn = 'N'
            # else:
            #     syn = 'Y'
    if not req_genus:
        if req_family and req_family != '':
            # Case 2: Family is given, search for species in teh family
            # Large cases were already fall back to default.
            species_list = Species.objects.filter(family=req_family)
        else:
            species_list = Species.objects.all()

    if req_type != '':
        species_list = species_list.filter(type=req_type)
    if alpha != '':
        species_list = species_list.filter(species__istartswith=alpha)
    if syn == 'N':
        species_list = species_list.exclude(status='synonym')
        syn = 'N'
    else:
        syn = 'Y'

    if len(species_list) > max_items:
        if not alpha:
            alpha = 'A'
            species_list = species_list.filter(species__istartswith=alpha)
        if len(species_list) > max_items:
            species_list = species_list[0:max_items]
        msg = "List too long, truncated to " + str(max_items) + ". Please refine your search criteria."


    write_output(request, str(app))
    context = {
        'genus': req_genus, 'species_list': species_list, 'app': app,
        'syn': syn, 'type': req_type, 'role':role,
        'family': req_family,
        'alpha_list': alpha_list, 'alpha': alpha,
        'canonical_url': canonical_url,
    }
    return render(request, "common/species.html", context)


def rank_update(rank, orid, SpcImages):
    try:
        image = SpcImages.objects.get(pk=orid)
    except SpcImages.DoesNotExist:
        return 0
    image.rank = rank
    image.save()
    return rank


def quality_update(quality, orid, SpcImages):
    try:
        image = SpcImages.objects.get(pk=orid)
    except SpcImages.DoesNotExist:
        return 0
    image.quality = quality
    image.save()
    return quality


def newbrowse(request, app=None):
    write_output(request, str(app))
    if app == None:
        app = request.GET.get('app', '')
    if not app:
        app = 'fungi'

    Family = apps.get_model('common', 'Family')
    family = request.GET.get('family', '')
    if family:
        try:
            family = Family.objects.get(family=family)
        except Family.DoesNotExist:
            family = ''

    Genus = apps.get_model(app, 'Genus')
    genus = request.GET.get('genus', 'Cattleya')
    if genus:
        try:
            genus = Genus.objects.get(genus=genus)
        except Genus.DoesNotExist:
            genus = ''

    type = request.GET.get('type','species')
    alpha = request.GET.get('alpha','')
    if alpha == 'ALL':
        alpha = ''

    family_list = genus_list = species_list = [], [], []

    display = request.GET.get('display', 'checked')

    if not family and not genus:
        # Browse family images
        family_list = Family.objects.filter(application=app)

    elif family and not genus:
        # Browse genus image in the Family

        if family:
            Genus = apps.get_model(app.lower(), 'Genus')
            SpcImages = apps.get_model(app.lower(), 'SpcImages')
            # genera = Genus.objects.filter(family=family)
            if app == 'orchidaceae':
                if type == 'species':
                    genera = SpcImages.objects.filter(image_file__isnull=False).order_by('gen').values_list('gen', flat=True).distinct()
                else:
                    genera = HybImages.objects.filter(image_file__isnull=False).order_by('gen').values_list('gen', flat=True).distinct()
            else:
                genera = SpcImages.objects.filter(image_file__isnull=False).filter(family=family).order_by('gen').values_list('gen', flat=True).distinct()
            if genera:
                genus_list = []
                genera = set(genera)
                genlist = Genus.objects.filter(pid__in=genera)
                if alpha:
                    genlist = genlist.filter(genus__istartswith=alpha)
                genlist = genlist.order_by('genus')
                for gen in genlist:
                    genus_list = genus_list + [gen.get_best_img()]
                context = {'genus_list': genus_list, 'family': family, 'app': family.application, 'alpha': alpha,
                           'alpha_list': alpha_list, 'app': app,}
                return render(request, 'common/newbrowse.html', context)

    # If only app is requested, find family_list and sample image by family
    # If family is requested, get sample list by genera
    if genus:
        # Go to browse genus.species
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
        Accepted = apps.get_model(app.lower(), 'Accepted')
        try:
            genus = Genus.objects.get(genus=genus)
        except Genus.DoesNotExist:
            genus = ''
        if isinstance(genus, Genus):
            species = Species.objects.filter(genus=genus)
            if not alpha and app == 'orchidaceae' and len(species) > 2000:
                alpha = 'A'
            if alpha:
                species = species.filter(species__istartswith=alpha)
            section = request.GET.get('section', '')
            if section:
                sections = Accepted.objects.filter(gen=genus.pid).filter(section=section).values_list('pid', flat=True)
                species = species.filter(pid__in=sections)

            species = species.order_by('species')
            if len(species) > 500:
                species = species[0: 500]
            species_list = []
            for x in species:
                spcimage = x.get_best_img()
                if spcimage:
                    species_list = species_list + [spcimage]
            context = {'species_list': species_list, 'family': genus.family, 'app': app, 'genus': genus, 'alpha': alpha, 'alpha_list': alpha_list,}
            return render(request, 'common/newbrowse.html', context)

    # Neither family, nor genus were requested. Building sample by families
    #  Typically requested from navbar buttons
    families = Family.objects.filter(application=app)
    if alpha:
        families = families.filter(family__istartswith=alpha)
    families = families.order_by('family')
    Genus = apps.get_model(app, 'Genus')
    family_list = []
    for fam in families:
        genimage = Genus.objects.filter(family=fam.family).order_by('?')[0:1]
        if len(genimage) > 0 and genimage[0].get_best_img():
            family_list = family_list + [(genimage[0])]
    role = request.GET.get('role', '')
    context = {'family_list': family_list, 'app': app, 'alpha': alpha, 'alpha_list': alpha_list, 'role': role,
               'display': display}
    return render(request, 'common/newbrowse.html', context)


def distribution(request):
    # For non-orchids only
    alpha = ''
    distribution = ''
    genus = ''
    commonname = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    crit = 0
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
            alpha = request.GET.get('alpha', '')
            if alpha != '':
                species_list = species_list.filter(species__istartswith=alpha)
            species_list = species_list.order_by('species')
        total = len(species_list)
    context = {'species_list': species_list, 'distribution': distribution, 'commonname': commonname,
               'family': family, 'genus': genus,
               'role': role, 'app': 'other', 'alpha': alpha, 'alpha_list': alpha_list,
               }
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
        return True
    except UploadFile.DoesNotExist:
        pass

    # Then look in the system
    if spc_obj.type == 'hybrid' and spc_obj.family.family == 'Orchidaceae':
        Images = apps.get_model(app, 'HybImages')
    else:
        Images = apps.get_model(app, 'SpcImages')
    try:
        spc = Images.objects.get(id=orid)
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
                except FileNotFoundError:
                    pass
        spc.delete()
        return True
    except Images.DoesNotExist:
        return False


def delete_bad_image_files(orid, app):
    # Delete file
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


@login_required
def deletephoto(request, orid, pid):
    app = request.GET.get('app', '')
    print("1 app", app)
    # family = request.GET.get('family', '')
    # print("1 family", family)

    # if family:
    #     try:
    #         family = Family.objects.get(family=family)
    #         app = family.application
    #     except Family.DoesNotExist:
    #         family = ''
    #         app = ''
    role = getRole(request)
    # print("2 family", family, app)


    # Something wrong here. All delete request mush have app
    if not app:
        return HttpResponseRedirect('/')

    print("2. app", app)

    Species = apps.get_model(app, 'Species')
    try:
        species = Species.objects.get(pk=pid)
        print("3 species", species, pid)
    except Species.DoesNotExist:
        message = 'This item does not exist!'
        return HttpResponse(message)

    delete_image_files(app, species, orid)
    write_output(request, str(app))

    url = "%s?role=cur&app=%s" % (reverse('display:photos', args=(species.pid,)), app)
    print(url)
    return HttpResponseRedirect(url)
def xdeletephoto(request, orid, pid):
    family = request.GET.get('family', None)
    try:
        family = Family.objects.get(family=family)
        app = family.application

    except Family.DoesNotExist:
        family = ''
        app = None
    role = getRole(request)

    if not family:
        app = request.GET.get('app', None)
        if app not in applications:
            app = None

    # Something wrong here. All delete request mush have app
    if not app:
        return HttpResponseRedirect('/')

    Species = apps.get_model('orchidaceae', 'Species')
    try:
        species = Species.objects.get(pk=pid)
        print(species, pid)
    except Species.DoesNotExist:
        message = 'This item does not exist!'
        return HttpResponse(message)

    # delete_image_files('orchidaceae', species, orid)
    # ----------------------------------------
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
    if species.type == 'hybrid' and species.family.family == 'Orchidaceae':
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
                    except FileNotFoundError:
                        pass
            spc.delete()
            return True
        except HybImages.DoesNotExist:
            return False
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
    # ----------------------------------------
    write_output(request, str(family))
    url = "%s?role=cur&family=Orchidaceae&species=%s" % (reverse('display:photos', args=(species.pid,)), species)
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
def approve_mediaphoto(request, app, pid, orid):
    from utils.views import regenerate_file
    role = getRole(request)
    if role != "cur":
        message = 'You do not have privilege to approve photos.'
        return HttpResponse(message)

    UploadFile = apps.get_model(app, 'UploadFile')
    Species = apps.get_model(app, 'Species')
    SpcImages = apps.get_model(app, 'SpcImages')
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'Pid does not exist.'
        return HttpResponse(message)

    family = species.family
    if app != family.application:
        message = 'Application and family name do not match.'
        return HttpResponse(message)

    # if species.status == 'synonym':
    #     # synonym = Synonym.objects.get(pk=pid)
    #     # pid = synonym.acc_id
    #     pid = species.getAcc()
    #     species = Species.accid

    if app == 'orchidaceae':
        if species.type == 'hybrid':
            image_dir = "utils/images/hybrid"
        else:
            image_dir = "utils/images/species"
    else:
        image_dir = "utils/images/" + str(family)

    try:
        int(orid)
    except ValueError:
        message = 'This photo does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    try:
        upl = UploadFile.objects.get(pk=orid)
    except UploadFile.DoesNotExist:
        msg = "uploaded file #" + str(orid) + "does not exist"
        url = "%s?role=%s&msg=%s&family=%s" % (reverse('display:photos', args=(species.pid,)), role, msg, app)
        return HttpResponseRedirect(url)

    if app == 'orchidaceae':
        if species.type == 'species':
            spc = SpcImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            credit_to=upl.credit_to, source_file_name=upl.source_file_name, variation=upl.variation,
                            form=upl.forma, rank=0, description=upl.description, location=upl.location,
                            created_date=upl.created_date, source_url=upl.source_url, text_data=upl.text_data)
            # hist = SpcImgHistory(pid=Species.objects.get(pk=pid), user_id=request.user, img_id=spc.id,
            #                      action='approve file')
            new_path = os.path.join(settings.STATIC_ROOT, "utils/images/species")
        else:
            spc = HybImages(pid=species.hybrid, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                            credit_to=upl.credit_to, source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                            description=upl.description, location=upl.location, created_date=upl.created_date,
                            source_url=upl.source_url, text_data=upl.text_data)
            new_path = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid")
    else:
        spc = SpcImages(
                pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, credit_to=upl.credit_to,
                source_file_name=upl.source_file_name, variation=upl.variation,
                form=upl.forma, rank=0, description=upl.description, location=upl.location,
                created_date=upl.created_date, source_url=upl.source_url)
        new_path = os.path.join(settings.STATIC_ROOT, "utils/images/", family.family)

    old_name = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
    print("old_name", old_name)
    print("new_path", new_path)
    unique_filename = regenerate_file(old_name, new_path)
    print("common", unique_filename)

    spc.approved_by = request.user
    spc.image_file = unique_filename
    status = spc.save()
    print("save status ", status)
    upl.approved = True
    upl.delete(0)
    write_output(request, str(family))
    url = "%s?role=%s&app=%s" % (reverse('display:photos', args=(species.pid,)), role, app)
    return HttpResponseRedirect(url)


@login_required
def myphoto(request, pid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    role = getRole(request)
    app, family = get_application(request)
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
    if not request.user.is_authenticated  or request.user.tier.tier < 2:
        url = "%s?role=%s&family=%s" % (reverse('display:information', args=(pid,)), role, species.gen.family)
        return HttpResponseRedirect(url)
    else:
        author, author_list = get_author(request)
    print("family", family)
    print("species", species)
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
               'pri': 'active', 'role': role, 'author': author, 'family': family, 'app': app,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto.html', context)


@login_required
def myphoto_list(request):
    author, author_list = get_author(request)
    role = 'pri'

    # If change family
    app_list = applications
    my_hyb_list = []
    my_list = []
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')

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
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    # author, author_list = get_author(request)
    role = 'pri'
    owner = request.GET.get('owner', 'Y')

    app, family = get_application(request)

    SpcImages = apps.get_model(app, 'SpcImages')
    try:
        author = request.user.photographer.author_id
    except Photographer.DoesNotExist:
        author = None
        context = {'type': 'species', 'family': family, 'app': app,
                   'role': role, 'brwhyb': 'active', 'author': author,
                   'myhyb': 'active', 'owner': owner,
                   }
        return render(request, 'common/myphoto_browse_hyb.html', context)
    img_list = SpcImages.objects.filter(author=author).order_by('binomial')
    if owner == 'Y':
        img_list = img_list.filter(credit_to__isnull=True)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)

    context = {'my_list': page_list, 'type': 'species', 'family': family, 'app': app,
               'role': role, 'brwspc': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'myspc': 'active', 'owner': owner,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_spc.html', context)


@login_required
def myphoto_browse_hyb(request):
    # Browse hybrid only works for orchids
    app = 'orchidaceae'
    family = 'Orchidaceae'
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login/')
    # author, author_list = get_author(request). species and hybrid are together in all other apps
    role = getRole(request)
    owner = request.GET.get('owner', 'Y')

    HybImages = apps.get_model(app, 'HybImages')
    try:
        author = request.user.photographer.author_id
    except Photographer.DoesNotExist:
        author = None
        context = {'type': 'species', 'family': family, 'app': app,
                   'role': role, 'brwhyb': 'active', 'author': author,
                   'myhyb': 'active', 'owner': owner,
                   }
        return render(request, 'common/myphoto_browse_hyb.html', context)
    img_list = HybImages.objects.filter(author=author).order_by('binomial')
    print(img_list[0].binomial)
    if owner == 'Y':
        img_list = img_list.filter(credit_to__isnull=True)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)

    context = {'my_list': page_list, 'type': 'species', 'family': family, 'app': app,
               'role': role, 'brwhyb': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'myhyb': 'active', 'owner': owner,
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_hyb.html', context)


@login_required
def curate_newupload(request):
    app, family = get_application(request)

    UploadFile = apps.get_model(app, 'UploadFile')
    filepath = os.path.join(settings.MEDIA_ROOT)
    file_list = UploadFile.objects.all().order_by('-modified_date')
    days = 7
    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)
    role = getRole(request)

    # write_output(request, str(family))
    context = {'file_list': page_list, 'family': family,
               'tab': 'upl', 'role': role, 'upl': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app, 'filepath': filepath,
               }
    return render(request, "common/curate_newupload.html", context)


@login_required
def curate_pending(request):
    # This page is for curators to perform mass delete. It contains all rank 0 photos sorted by date reverse.
    app, family = get_application(request)

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
    # write_output(request, str(family))
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
    app, family = get_application(request)

    ortype = request.GET.get('type', None)
    if ortype == 'hybrid' and family.family == 'Orchidaceae':
        SpcImages = apps.get_model(app, 'HybImages')
    else:
        SpcImages = apps.get_model(app, 'SpcImages')
    Species = apps.get_model(app, 'Species')

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
        orid = int(request.GET.get('id', None))
        rank = int(request.GET.get('rank', 0))
        quality = int(request.GET.get('quality', 0))
        if rank:
            rank_update(rank, orid, SpcImages)
        if quality:
            quality_update(quality, orid, SpcImages)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, file_list, page_length, num_show)

    role = getRole(request)
    # write_output(request, str(family))
    context = {'file_list': page_list, 'type': ortype, 'family': family,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app,
               }
    return render(request, 'common/curate_newapproved.html', context)


@login_required
def uploadfile(request, pid):
    app, family = get_application(request)
    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')
    role = getRole(request)
    if not request.user.is_authenticated  or not request.user.photographer.author_id:
        message = 'You dont have access to upload files. Please update your profile to gain access. ' \
                  'Or contact admin@bluenanta.com'
        return HttpResponse(message)
    species = Species.objects.get(pk=pid)
    if species.get_num_img_by_author(request.user.photographer.get_authid()) > 2:
        message = 'Each user may upload at most 3 private photos for each species/hybrid. ' \
                'Please delete one or more of your photos before uploading a new one.'
        return HttpResponse(message)

    author = get_reqauthor(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This name does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    family = species.gen.family
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)
    if app == 'animalia':
        from animalia.forms import UploadFileForm
    elif app == 'aves':
        from aves.forms import UploadFileForm
    elif app == 'fungi':
        from fungi.forms import UploadFileForm
    elif app == 'other':
        from other.forms import UploadFileForm
    elif app == 'orchidaceae':
        from detail.forms import UploadFileForm

    form = UploadFileForm(initial={'author': request.user.photographer.author_id, 'role': role, 'binomial': species.binomial})

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            write_output(request, app)
            spc = form.save(commit=False)
            if isinstance(species, Species):
                spc.pid = species
            if species.binomial != spc.binomial:
                spc.pid = None
            spc.author = request.user.photographer
            spc.type = species.type
            spc.user_id = request.user
            spc.text_data = spc.text_data.replace("\"", "\'\'")
            spc.save()
            url = "%s?role=%s&author=%s&app=%s" % (reverse('display:photos', args=(species.pid,)), role,
                                                request.user.photographer.author_id, app)
            return HttpResponseRedirect(url)

    context = {'form': form, 'species': species, 'web': 'active',
               'author': author, 'family': family,
               'role': role, 'app': app, 'title': 'uploadfile'}
    if app == 'orchidaceae':
        return render(request, 'detail/uploadfile.html', context)
    else:
        return render(request, app + '/uploadfile.html', context)


def get_new_uploads(request):
    context = {}
    UploadFile = apps.get_model('orchidaceae', 'UploadFile')
    orchidaceae_upl = UploadFile.objects.all()
    if len(orchidaceae_upl):
        context['orchidaceae_upl'] = orchidaceae_upl

    UploadFile = apps.get_model('animalia', 'UploadFile')
    animalia_upl = UploadFile.objects.all()
    if len(animalia_upl):
        context['animalia_upl'] = animalia_upl

    UploadFile = apps.get_model('aves', 'UploadFile')
    aves_upl = UploadFile.objects.all()
    if len(aves_upl):
        context['aves_upl'] = aves_upl

    UploadFile = apps.get_model('fungi', 'UploadFile')
    fungi_upl = UploadFile.objects.all()
    if len(fungi_upl):
        context['fungi_upl'] = fungi_upl

    UploadFile = apps.get_model('other', 'UploadFile')
    other_upl = UploadFile.objects.all()
    if len(other_upl):
        context['other_upl'] = other_upl

    return render(request, 'common/get_new_uploads.html', context)


def compare(request, pid):
    # TODO:  Use Species form instead
    role = getRole(request)
    pid2 = species2 = genus2 = infraspr2 = infraspe2 = author2 = year2 = spc2 = gen2 = ''
    app, family = get_application(request)

    # get Species, Genus, classes
    Species = apps.get_model(app, 'Species')
    Hybrid = apps.get_model(app, 'Hybrid')


    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')
    if app == 'orchidaceae' and species.type == 'hybrid':
        SpcImages = apps.get_model(app, 'HybImages')
    else:
        SpcImages = apps.get_model(app, 'SpcImages')


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
            message = binomial2 + ' does not exist in ' + family.family + ' family'
            context = {'species': species, 'genus': genus, 'pid': pid, 'family': family,
                       'spcimg1_list': spcimg1_list,
                       'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                       'message2': message,
                       'tab': 'sbs', 'sbs': 'active', 'role': role, 'app': app}
            return render(request, 'common/compare.html', context)
        elif len(species2) > 1:
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
                           'tab': 'sbs', 'sbs': 'active', 'role': role, 'app': app}
                return render(request,  'common/compare.html', context)
            else:  # No match found
                message = "species, <b>" + str(gen2) + ' ' + spc2 + '</b> returned none'
                context = {'species': species, 'genus': genus, 'pid': pid,  # original
                           'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                           'message1': message, 'family': family,
                           'tab': 'sbs', 'sbs': 'active', 'role': role, 'app': app,}
                return render(request, 'common/compare.html', context)
        else:
            species2 = species2[0]
            pid2 = species2.pid
    else:
        # No binomial found,  This is the initial request
        pid2 = ''

    cross = ''
    message1 = message2 = accepted2 = ''

    # Convert synonym to accepted
    if species2 and species2.status == 'synonym':
        pid2 = species2.getAcc()
        accepted2 = species2.getAccepted()

    # Choose correct image class based on type.
    if species2.type == 'hybrid':
        SpcImages = apps.get_model(app, 'HybImages')
    else:
        SpcImages = apps.get_model(app, 'SpcImages')

    # A second species is found
    if pid2:
        cross = Hybrid.objects.filter(seed_id=pid).filter(pollen_id=pid2)
        if not cross:
            cross = Hybrid.objects.filter(seed_id=pid2).filter(pollen_id=pid)
        if cross:
            cross = cross[0]
        else:
            cross = ''
            spcimg2_list = SpcImages.objects.filter(pid=pid2).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]

    msgnogenus = ''
    if 'msgnogenus' in request.GET:
        msgnogenus = request.GET['msgnogenus']

    write_output(request, str(species.binomial) + " vs " + str(species2.binomial))
    context = {'pid': pid, 'genus': genus, 'species': species,
               'pid2': pid2, 'accepted2': accepted2,  # pid of accepted species
               'spcimg1_list': spcimg1_list,
               'genus2': gen2, 'species2': spc2, 'spcimg2_list': spcimg2_list,
               'cross': cross, 'family': family, 'binomial2': binomial2,
               'msgnogenus': msgnogenus, 'message1': message1, 'message2': message2,
               'tab': 'sbs', 'sbs': 'active', 'role': role, 'app': app, }
    return render(request, 'common/compare.html', context)
