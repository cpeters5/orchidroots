
import re
import os
import logging
import random
import shutil

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse, reverse_lazy, resolve
from django.utils import timezone
from itertools import chain
import django.shortcuts
from collections import defaultdict

from django.apps import apps
from fuzzywuzzy import fuzz, process
from datetime import datetime, timedelta
from utils import config
from utils.views import write_output, getRole, get_author, get_reqauthor, getSuperGeneric, pathinfo, get_application
from common.models import Family, Subfamily, Tribe, Subtribe, Region, SubRegion
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages, GenusStat

from accounts.models import User, Photographer
# import utils.config

epoch = 1740
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
alpha_list = config.alpha_list
applications = config.applications
app_names = config.app_names
default_genus = config.default_genus

# Note:  common.views applied to all domains (animalia, aves, fungi, orchidaceae and other)

def home(request):
    all_list = []
    role = getRole(request)
    num_samples = 1
    num_orchids = 4

    # Get sample images of orchids
    SpcImages = apps.get_model('orchidaceae', 'SpcImages')
    Genus = apps.get_model('orchidaceae', 'Genus')
    GenusStat = apps.get_model('orchidaceae', 'GenusStat')
    genera = Genus.objects.filter(genusstat__best_image__isnull=False).select_related('genusstat').order_by('?')
    orcimage = []
    for x in genera:
        # TODO: Replace genus.get_best_img() method with stat best_img data.
        if x.get_best_img():
            orcimage = orcimage + [x.get_best_img()]
            if len(orcimage) > 3:
                break

    # Get random other families
    SpcImages = apps.get_model('other', 'SpcImages')
    Genus = apps.get_model('other', 'Genus')
    sample_families = Genus.objects.filter(genusstat__num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        other_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        if isinstance(other_obj, SpcImages):
            all_list = all_list + [[other_obj.pid.family, other_obj]]

    # get random suculents
    try:
        sample_genus = Genus.objects.filter(is_succulent=True).filter(genusstat__num_spcimage__gt=0).order_by('?')[0:1][0]
    except:
        sample_genus = ''
    try:
        succulent_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        succulent_obj = ''
    all_list = all_list + [['Succulent', succulent_obj]]

    # get random carnivorous
    try:
        sample_genus = Genus.objects.filter(is_carnivorous=True).filter(genusstat__num_spcimage__gt=0).order_by('?')[0:1][0]
    except:
        sample_genus = ''

    try:
        carnivorous_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        carnivorous_obj = ''

    all_list = all_list + [['Carnivorous', carnivorous_obj]]

    # get random parasitic
    try:
        sample_genus = Genus.objects.filter(is_parasitic=True).filter(genusstat__num_spcimage__gt=0).order_by('?')[0:1][0]
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
    sample_families = Genus.objects.filter(genusstat__num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
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
    sample_families = Genus.objects.filter(genusstat__num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
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
    sample_families = Genus.objects.filter(genusstat__num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    for fam in sample_families:
        try:
            animalia_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            animalia_obj = ''
        all_list = all_list + [["Aves", animalia_obj]]

    random.shuffle(all_list)
    canonical_url = request.build_absolute_uri(f'/').replace('www.orchidroots.com', 'orchidroots.com')

    context = {'orcimage': orcimage, 'all_list': all_list, 'succulent_obj': succulent_obj,
               'carnivorous_obj': carnivorous_obj, 'parasitic_obj': parasitic_obj, 'role': role,
               'canonical_url': canonical_url,
               }
    return render(request, 'home.html', context)


def taxonomy(request, app=None):
    if not app:
        app = request.GET.get('app', 'orchidaceae')
        if app not in applications:
            app = 'orchidaceae'

    canonical_url = request.build_absolute_uri(f'/common/taxonomy/{app}/').replace('www.orchidroots.com', 'orchidroots.com')
    # non canonical url
    if 'app' in request.GET:
        # Redirect permanent to preferred url
        return HttpResponsePermanentRedirect(canonical_url)

    taxonomy_list = Family.objects.filter(application=app)
    context = {'taxonomy_list': taxonomy_list, 'app': app,
               'canonical_url': canonical_url,
               }
    return render(request, "common/taxonomy.html", context)


def family(request, app=None):
    if not app:
        app = request.GET.get('app', '')
        if not app or app not in applications:
            app = 'orchidaceae'

    alpha = request.GET.get('alpha','')
    if alpha and alpha != 'All':
        canonical_url = request.build_absolute_uri(f'/common/family/{app}/?alpha={alpha}').replace('www.orchidroots.com', 'orchidroots.com')
    else:
        canonical_url = request.build_absolute_uri(f'/common/family/{app}/').replace('www.orchidroots.com', 'orchidroots.com')

    if 'app' in request.GET:
        # Redirect permanent to preferred url
        return HttpResponsePermanentRedirect(canonical_url)

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
    # If app is not given (non canonical_url)
    if not app:
        app = request.GET.get('app', '')
        if not app or app not in applications:
            app = 'orchidaceae'

    alpha = request.GET.get('alpha','')
    if alpha and alpha != 'All':
        canonical_url = request.build_absolute_uri(f'/common/genera/{app}/?alpha={alpha}').replace('www.orchidroots.com', 'orchidroots.com')
    else:
        canonical_url = request.build_absolute_uri(f'/common/genera/{app}/').replace('www.orchidroots.com', 'orchidroots.com')

    if 'app' in request.GET:
        # Non canonical_url. redirect to canonical
        return HttpResponsePermanentRedirect(canonical_url)

    family = request.GET.get('family', '')
    if family:
        try:
            family = Family.objects.get(family=family)
        except Family.DoesNotExist:
            family = ''
    if isinstance(family, Family) and family.application != app:
        family = ''

    Genus = apps.get_model(app, 'Genus')
    genus_list = Genus.objects.exclude(status='synonym')

    # This happens when a user clicks on one of the suprageneric ranks.
    subfamily, tribe, subtribe = getSuperGeneric(request)
    if subtribe:
        genus_list = genus_list.filter(subtribe=subtribe)
    if tribe:
        genus_list = genus_list.filter(tribe=tribe)
    if subfamily:
        genus_list = genus_list.filter(subfamily=subfamily)

    if alpha:
        genus_list = genus_list.filter(genus__istartswith=alpha)

    write_output(request, str(family))
    context = {
        'genus_list': genus_list,  'app': app, 'alpha': alpha,
        'family': family,
        'alpha_list': alpha_list,
        'canonical_url': canonical_url,
    }
    return render(request, "common/genera.html", context)

def get_regions(pid):
    region_ids = Distribution.objects.filter(pid=pid).values_list('region_id', flat=True)
    regions = Region.objects.filter(id__in=region_ids).values_list('name', flat=True)
    return ', '.join(regions)


def species(request, app=None):
    # Determine application if not given
    if not app:
        app = request.GET.get('app', '')
        if not app or app not in applications:
            #  Default to orchid
            app = 'orchidaceae'

    syn = request.GET.get('syn', 'N')
    req_genus = request.GET.get('genus', '')
    req_type = request.GET.get('type', 'species')
    if not req_genus:
        req_genus = default_genus[app]

    # Build canonical url
    alpha = request.GET.get('alpha', '')
    if alpha and alpha != 'All':
        canonical_url = request.build_absolute_uri(f'/common/species/{app}/?genus={req_genus}&alpha={alpha}&type={req_type}').replace('www.orchidroots.com', 'orchidroots.com')
    else:
        canonical_url = request.build_absolute_uri(f'/common/species/{app}/?genus={req_genus}&type={req_type}').replace('www.orchidroots.com', 'orchidroots.com')

    #  Permanently redirect noncanonical to canonical url
    if 'app' in request.GET:
        return HttpResponsePermanentRedirect(canonical_url)

    role = request.GET.get('role','pub')

    # Note: orchidaceae app has only one family, Orchidaceae
    if app == 'orchidaceae':
        req_family = 'Orchidaceae'
    else:
        # For other apps, user may request a family
        req_family = request.GET.get('family', '')
        if req_family:
            try:
                req_family = Family.objects.get(family=req_family)
                app = req_family.application
            except Family.DoesNotExist:
                req_family = ''
            # Ifnore requested family if it is not in the same application.
            if isinstance(req_family, Family) and req_family.application != app:
                req_family = ''
    Genus = apps.get_model(app, 'Genus')
    Species = apps.get_model(app, 'Species')
    species_list = []

    if req_genus:
        # Case 1: Genus is given, list only species of that genus
        try:
            req_genus = Genus.objects.get(genus=req_genus)
            species_list = Species.objects.filter(genus=req_genus)
        except Genus.DoesNotExist:
            # No genus found in this category, go to the next.
            req_genus = ''

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

    #  If user request one of the subgeneric ranks (by clicking on a link in the subgeneric column)
    # Orchid only
    if app == 'orchidaceae':
        subgenus = request.GET.get('subgenus', '')
        section = request.GET.get('section', '')
        subsection = request.GET.get('subsection', '')
        series = request.GET.get('series', '')
        if subgenus:
            species_list = species_list.filter(accepted__subgenus=subgenus)
        if section:
            species_list = species_list.filter(accepted__section=section)
        if subsection:
            species_list = species_list.filter(accepted__subsection=subsection)
        if series:
            species_list = species_list.filter(accepted__series=series)

    # Finally truncate the list if it is too long.
    # A work around to prevent large transactions. Can be removed after serverside dtatatable is implemented
    max_items = 3000
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


def hybrid(request, app):
    # Handle bad url due to a typo in sitemap.
    # app is always 'orchidaceae'
    alpha = request.GET.get('alpha', '')
    req_genus = request.GET.get('genus', '')
    if alpha and alpha != 'All':
        canonical_url = request.build_absolute_uri(f'/common/species/{app}/?genus={req_genus}&alpha={alpha}&type=hybrid').replace('www.orchidroots.com', 'orchidroots.com')
    else:
        canonical_url = request.build_absolute_uri(f'/common/species/{app}/?genus={req_genus}&type=hybrid').replace('www.orchidroots.com', 'orchidroots.com')

    #  Permanently redirect noncanonical to canonical url
    return HttpResponsePermanentRedirect(canonical_url)


def synonym(request, app, pid):
    role = getRole(request)
    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    #  If requested species is a synonym, convert it to accepted species
    if species.status == 'synonym':
        species = species.getAccepted()

    write_output(request, species.binomial)
    genus = species.genus
    synonym_list = Synonym.objects.filter(acc_id=species.pid)

    canonical_url = request.build_absolute_uri(f'/{app}/synonym/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')

    context = {'synonym_list': synonym_list, 'species': species,
               'tab': 'syn', 'syn': 'active', 'genus': genus,
               'role': role, 'app': app,
               'canonical_url': canonical_url,
               }
    return render(request, 'common/synonym.html', context)


def distribution(request, app, pid):
    Species = apps.get_model(app, 'Species')
    Distribution = apps.get_model(app, 'Distribution')
    role = getRole(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    if species.status == 'synonym':
        accid = species.synonym.acc_id
    else:
        accid = pid
    dist_list = Distribution.objects.filter(pid=accid)
    tuples = []
    for x in dist_list:
        region_name = ''
        subregion_name = ''
        if x.region_id:
            region_name = x.region_id.name
        if x.subregion_id:
            subregion_name = x.subregion_id.name
        if region_name or subregion_name:
            tupl = (region_name, subregion_name)
            tuples.append(tupl)

    grouped = defaultdict(list)
    for key, value in tuples:
        grouped[key].append(value)

    # Convert to a list of tuples for template compatibility
    grouped_list = [(k, grouped[k]) for k in grouped]


    context = {'grouped': grouped_list, 'species': species,'tab': 'dist', 'dist': 'active', 'role': role,
               'title': 'distribution', 'app': app,
               }
    write_output(request, species.binomial)
    return render(request, 'orchidaceae/distribution.html', context)


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
    # Serves 3 different cases:
    # 1. Browse sample images by families.  Non orchidaceae only
    # 2. Browse sample images of genera in a selected family
    # 3. Browse sample images of species in requested genus
    write_output(request, str(app))
    if app == None:
        #  Will redirect this to canonical
        app = request.GET.get('app', 'orchidaceae')
    if not app:
        app = 'orchidaceae'
    # handle request
    Family = apps.get_model('common', 'Family')
    family = request.GET.get('family', '')
    if family:
        try:
            family = Family.objects.get(family=family)
        except Family.DoesNotExist:
            family = ''

    # requested genus?
    Genus = apps.get_model(app, 'Genus')
    genus = request.GET.get('genus', '')
    if genus:
        try:
            genus = Genus.objects.get(genus=genus)
        except Genus.DoesNotExist:
            genus = ''

    # Orchidaceae has only one family Orchidaceae;
    if app == 'orchidaceae' and not family and not genus:
        family = 'Orchidaceae'

    type = request.GET.get('type','species')
    display = request.GET.get('display', 'checked')
    alpha = request.GET.get('alpha','')
    role = request.GET.get('role', '')
    if alpha == 'ALL':
        alpha = ''

    #  No family/genus requested, browse image sample of each Family (non-orchidaceae only)
    if not family and not genus:
        families = Family.objects.filter(application=app)
        if alpha:
            families = families.filter(family__istartswith=alpha)
        families = families.order_by('family')

        family_list = []
        for fam in families:
            if fam.get_best_img():
                family_list = family_list + [fam.get_best_img()]
        context = {'family_list': family_list, 'app': app, 'alpha': alpha, 'alpha_list': alpha_list, 'role': role,
                   'display': display, 'type': type,}
        return render(request, 'common/newbrowse.html', context)

    elif genus:
        # browse images of species in requested genus
        Species = apps.get_model(app.lower(), 'Species')
        Accepted = apps.get_model(app.lower(), 'Accepted')
        try:
            genus = Genus.objects.get(genus=genus)
        except Genus.DoesNotExist:
            genus = ''
        if isinstance(genus, Genus):
            species = Species.objects.filter(genus=genus).exclude(status='synonym')
            if type:
                species = species.filter(type=type)

            # For large cases, limit to alpha =A
            if not alpha and app == 'orchidaceae' and len(species) > 2000:
                alpha = 'A'
            if alpha:
                species = species.filter(species__istartswith=alpha)
            # If request a section
            section = request.GET.get('section', '')
            if section:
                sections = Accepted.objects.filter(gen=genus.pid).filter(section=section).values_list('pid', flat=True)
                species = species.filter(pid__in=sections)

            species = species.order_by('species')
            if len(species) > 500:
                species = species[0: 500]
            species_list = species
            context = {'species_list': species_list, 'family': genus.family, 'app': app, 'genus': genus, 'alpha': alpha, 'alpha_list': alpha_list, 'type': type,}
            return render(request, 'common/newbrowse.html', context)

    elif family:
        # Browse genus image in the Family
        genlist = Genus.objects.filter(genusstat__best_image__isnull=False).select_related('genusstat')
        if alpha:
            genlist = genlist.filter(genus__istartswith=alpha)
        genlist = genlist.order_by('genus')
        genus_list = []
        for gen in genlist:
            if gen.get_best_img():
                genus_list = genus_list + [gen.get_best_img()]
        context = {'genus_list': genus_list, 'family': family, 'app': app, 'alpha': alpha,
                   'alpha_list': alpha_list, 'app': app, 'type': type, }
        return render(request, 'common/newbrowse.html', context)

    context = {'genus_list': '', 'family': family, 'app': app, 'alpha': alpha,
               'alpha_list': alpha_list, 'type': type,}
    return render(request, 'common/newbrowse.html', context)


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


def delete_file(app, orid):
    # Check uploaded files and delete uploaded image
    UploadFile = apps.get_model(app, 'UploadFile')
    try:
        upl = UploadFile.objects.get(id=orid)
    except UploadFile.DoesNotExist:
        return False
    # Begin removing file in the media area
    filename = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
    if os.path.isfile(filename):
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
    # Delete UploadFile instance
    upl.delete()
    return True


def delete_image(app, orid, spc_obj):
    # Delete spcimages or hybridInstance and delete image file if already ingested.
    if spc_obj.type == 'hybrid' and spc_obj.family.family == 'Orchidaceae':
        Images = apps.get_model(app, 'HybImages')
    else:
        Images = apps.get_model(app, 'SpcImages')
    try:
        spc = Images.objects.get(id=orid)
    except Images.DoesNotExist:
        # This image is in the upload file area
        return False

    #  Begin removing image
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
    # Delete record
    spc.delete()
    return True


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
def deletephoto(request, orid, pid=None):
    app = request.GET.get('app', '')
    st = False
    # Something wrong here. All delete request mush have app
    if not app:
        return HttpResponseRedirect('/')

    Species = apps.get_model(app, 'Species')
    if pid:
        # Get instance
        try:
            species = Species.objects.get(pk=pid)
        except Species.DoesNotExist:
            species = ''

        # Delete record in SpcImages
        if isinstance(species, Species):
            st = delete_image(app, orid, species)

    if not st:
        # Delete record in UploadFile (pid may or may not exist)
        x = delete_file(app, orid)

    write_output(request, str(app))

    if pid:
        url = "%s?role=cur" % (reverse('display:photos', args=(app, species.pid,)))
    else:
        url = "%s?app=%s&role=cur" % (reverse('common:curate_newupload'), app)
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
        url = "%s?role=%s" % (reverse('display:photos', args=(app, species.pid,)), role)
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
        st = delete_image(app, orid, species)
        if st:
            delete_file(app, orid)

    days = 7
    area = ''
    role = getRole(request)
    area = request.GET.get('area', None)
    days = int(request.GET.get('days', 3))
    page = int(request.GET.get('page', 1))
    if area == 'allpending':  # from curate_pending (all rank 0)
        url = "%s?role=%s&page=%s&type=%s&days=%s" % (reverse('detail:curate_pending'), role, page, type, days)
    else:
        url = "%s?role=%s" % (reverse('display:photos', args=(app, species.pid,)), role)
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
        url = "%s?role=%s&msg=%s" % (reverse('display:photos', args=(app, species.pid,)), role, msg)
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
            spc = HybImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
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
    unique_filename = regenerate_file(old_name, new_path)

    spc.approved_by = request.user
    spc.user_id = request.user
    spc.image_file = unique_filename
    status = spc.save()
    upl.approved = True
    upl.delete(0)
    os.remove(old_name)
    write_output(request, str(family))
    url = "%s?role=%s" % (reverse('display:photos', args=(app, species.pid,)), role)
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
    if not request.user.is_authenticated or request.user.tier.tier < 2:
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
    img_list = SpcImages.objects.filter(author=author).order_by('pid__binomial')
    if owner == 'Y':
        img_list = img_list.filter(credit_to__isnull=True)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)

    context = {'my_list': page_list, 'type': 'species', 'family': family, 'app': app,
               'role': role, 'brwspc': 'active', 'author': author, 'app_name': app_names[app],
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
    if owner == 'Y':
        img_list = img_list.filter(credit_to__isnull=True)

    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
        request, img_list, page_length, num_show)

    context = {'my_list': page_list, 'type': 'species', 'family': family, 'app': app,
               'role': role, 'brwhyb': 'active', 'author': author, 'app_name': app_names[app],
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
    file_list = SpcImages.objects.filter(rank__gt=0, pid__isnull=False)
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
    form = UploadFileForm(initial={'author': request.user.photographer.author_id, 'role': role })
    # form = UploadFileForm(initial={'author': request.user.photographer.author_id, 'role': role, 'binomial': species.binomial})

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            write_output(request, app)
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

@login_required
def newcross(request, pid1, pid2):
    # Create a new hybrid (pid x pid2)
    # The cross doesn't exist.
    # Need to identify nothogenus
    import datetime
    # Assume both pids are accepted
    # Assume cross does not exist
    app, family = get_application(request)
    Species = apps.get_model(app, 'Species')
    Hybrid = apps.get_model(app, 'Hybrid')
    species1 = Species.objects.get(pk=pid1)
    species2 = Species.objects.get(pk=pid2)

    #  Find if Nothogenus (genus1 x genus2) has been defined by checking in existing hybrids with same genus cross.
    #  If not, the cross cannot be created
    genus1 = species1.genus
    genus2 = species2.genus
    spc2 =species2.species
    genus = Hybrid.objects.filter(Q(seed_genus=genus1, pollen_genus=genus2) | Q(seed_genus=genus2, pollen_genus=genus1))
    genus = genus.exclude(pid__status='synonym').filter(pid__source='RHS').first()
    if genus:
        nothogenus = genus.pid.genus
    elif genus1 == genus2:
        nothogenus = genus1
    else:
        nothogenus = ''

    if nothogenus:
        # Create new cross here
        # ------------------------------------------------
        spcobj = Species()
        spcobj.genus = nothogenus
        spcobj.species = species1.species + '-' + species2.species
        if species2.infraspe:
            spcobj.species = spcobj.species + '-' + species2.infraspe
        spcobj.pid = Hybrid.objects.filter(pid__gt=900000000).filter(pid__lt=999999999).order_by('-pid')[0].pid_id + 1
        spcobj.source = 'INT'
        spcobj.originator = request.user.username
        spcobj.type = 'hybrid'
        spcobj.status = 'nonregistered'
        datetime_obj = datetime.datetime.now()
        spcobj.year = datetime_obj.year
        spcobj.save()

        # Now create Hybrid instance
        hybobj = Hybrid()
        hybobj.pid = spcobj
        hybobj.seed_genus = species1.genus
        hybobj.pollen_genus = species2.genus
        hybobj.seed_species = species1.species
        hybobj.pollen_species = species2.species
        hybobj.seed_id = species1
        hybobj.pollen_id = species2
        hybobj.save()

        write_output(request, str(species1.binomial) + " vs " + str(species2.binomial))
        return HttpResponseRedirect("/display/summary/orchidaceae/" + str(spcobj.pid) + "/")
        # ---------------------------------------------
    else:
        pid2 = None
        return HttpResponseRedirect("/common/compare/" + str(pid1) + "/?app=orchidaceae&pid=" + str(pid2) + "&failmsg=FAILGENUS&genus2=" + genus2 + "&species2=" + spc2)


def compare(request, pid):
    # TODO:  Use Species form instead
    role = getRole(request)
    app, family = get_application(request)

    # get Species, Genus, classes
    Species = apps.get_model(app, 'Species')
    Hybrid = apps.get_model(app, 'Hybrid')
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'Pid does not exist.'
        return HttpResponse(message)

    if app == 'orchidaceae' and species.type == 'hybrid':
        SpcImages = apps.get_model(app, 'HybImages')
    else:
        SpcImages = apps.get_model(app, 'SpcImages')

    # Images shown for species 1
    spcimg1_list = SpcImages.objects.filter(pid=pid).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]
    family = species.gen.family
    genus = species.genus
    spc2 = request.GET.get('species2', '').strip()
    gen2 = request.GET.get('genus2', '').strip()
    infraspe2 = request.GET.get('infraspe2', '').strip()
    infraspr2 = request.GET.get('infraspr2', '').strip()
    author2 = request.GET.get('author2', '').strip()
    year2 = request.GET.get('year2', '').strip()
    binomial2 = ' '.join((gen2, spc2, infraspr2, infraspe2 ))
    failmsg = request.GET.get('failmsg', None)
    message = ''
    if binomial2:
        species2 = Species.objects.filter(binomial__exact=binomial2)
        if len(species2) == 0:
            message = binomial2 + ' species does not exist. Cannot compare'
            pid2 = None
        elif len(species2) > 1:
            if year2:
                species2 = species2.filter(year=year2)
            if author2:
                species2 = species2.filter(author=author2)
            if len(species2) == 1:  # Found unique species
                species2 = species2[0]
                pid2 = species2.pid
            elif len(species2) > 1:  # MULTIPLE SPECIES RETURNED
                pid2 = None
                message = "Multiple" + ' '.join((species2[0].binomial, author2, year2)) + ' found. Try adding author or year'
            else:  # No match found
                pid2 = None
                message = "species, <b>" + str(gen2) + ' ' + spc2 + '</b> returned none'
        else:
            species2 = species2[0]
            pid2 = species2.pid
    else:
        # No binomial found,  This is the initial request
        message = None
        pid2 = None
    if not pid2:
        # Could be initial launch, or fail nothogenus
        context = {'species': species, 'genus': genus, 'pid': pid, 'family': family, 'species2': species2,
                   'spcimg1_list': spcimg1_list,
                   'genus2': gen2, 'species2': spc2, 'infraspr2': infraspr2, 'infraspe2': infraspe2,
                   'author2': author2, 'year2': year2,
                   'message2': message, 'failmsg': failmsg,
                   'tab': 'sbs', 'sbs': 'active', 'role': role, 'app': app}
        return render(request, 'common/compare.html', context)

    # Before allowing new hybrid, Check if pid and pid2 are the same or are synonym.
    from orchidaceae.models import Synonym
    # If one is a synonym of the other
    synonym = Synonym.objects.filter(Q(spid=pid, acc_id=pid2) | Q(spid=pid2, acc_id=pid))
    synonym_message = None
    if synonym:
         synonym_message = " are synopnymous"
    # In case both are synonymn to the same accepted species
    if species.status == 'synonym' and species2.status == 'synonym':
        if species.synonym.acc_id == species2.synonym.acc_id:
            accepted = Species.objects.get(pk=species2.synonym.acc_id)
            synonym_message = " are synonym of " + accepted.binomial

    if species2.type == 'hybrid':
        SpcImages = apps.get_model(app, 'HybImages')
    else:
        SpcImages = apps.get_model(app, 'SpcImages')

    # Determine cross
    cross = Hybrid.objects.filter(Q(seed_id=pid, pollen_id=pid2) | Q(seed_id=pid2, pollen_id=pid)).first()
    spcimg2_list = SpcImages.objects.filter(pid=pid2).filter(rank__lt=7).order_by('-rank', 'quality', '?')[0: 2]

    # msgnogenus = request.GET.get('msgnogenus', '')
    write_output(request, str(species.binomial) + " vs " + str(species2.binomial))
    context = {'pid': pid, 'genus': species.genus, 'species': species, 'species2': species2,
               'pid2': pid2,  # Valid pid of second species
               'genus2': species2.genus, 'spc2': species2.species, 'infraspr2': species2.infraspr, 'infraspe2': species2.infraspe,
               'author2': species2.author, 'year2': species2.year,
               'spcimg1_list': spcimg1_list,
               'spcimg2_list': spcimg2_list,
               'message3': message, 'synonym_message': synonym_message,
               'cross': cross, 'family': family, 'failmsg': failmsg,
               'tab': 'sbs', 'sbs': 'active', 'role': role, 'app': app, }
    return render(request, 'common/compare.html', context)
