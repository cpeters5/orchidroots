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
from itertools import chain
import django.shortcuts
from django.apps import apps
from fuzzywuzzy import fuzz, process
from utils import config
from utils.views import write_output, getRole, paginator, get_author
from core.models import Family, Subfamily, Tribe, Subtribe
from accounts.models import User, Photographer
from .forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm

epoch = 1740
alpha_list = string.ascii_uppercase
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
app_list = ['Orchidaceae', 'Bromeliaceae', 'Cactaceae']
alpha_list = config.alpha_list
f, sf, t, st = '', '', '', ''
redirect_message = 'species does not exist'
# num_show = 5
# page_length = 500


def getModels(request):
    family, subfamily, tribe, subtribe = '', '', '', ''
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'family' in request.POST:
        family = request.POST['family']

    if family:
        try:
            family = Family.objects.get(pk=family)
        except Family.DoesNotExist:
            family = ''
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily']
        if subfamily:
            try:
                subfamily = Subfamily.objects.get(pk=subfamily)
            except Subfamily.DoesNotExist:
                subfamily = ''
            if subfamily.family:
                family = subfamily.family
    if 'tribe' in request.GET:
        tribe = request.GET['tribe']
        if tribe:
            try:
                tribe = Tribe.objects.get(pk=tribe)
            except Tribe.DoesNotExist:
                tribe = ''
            if tribe.subfamily:
                subfamily = tribe.subfamily
            if subfamily.family:
                family = tribe.subfamily.family
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe']
        if subtribe:
            try:
                subtribe = Subtribe.objects.get(pk=subtribe)
            except Subtribe.DoesNotExist:
                subtribe = ''
            if subtribe.tribe:
                tribe = subtribe.tribe
            if tribe.subfamily:
                subfamily = tribe.subfamily
            if subfamily.family:
                family = subfamily.family
    try:
        app = Family.objects.get(pk=family)
        app = app.application
    except Family.DoesNotExist:
        app = ''
        family = ''
        logger.error("Missing Family!")
    Genus = ''
    Species = ''
    Accepted = ''
    Hybrid = ''
    Synonym = ''
    Distribution = ''
    SpcImages = ''
    HybImages = ''
    UploadFile = ''
    Intragen = ''
    if app:
        if app == 'orchidaceae':
            from detail.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm
            # only exist for orchidaceae
            GenusRelation = apps.get_model(app.lower(), 'GenusRelation')
            HybImages = apps.get_model(app.lower(), 'HybImages')
            Intragen = apps.get_model(app.lower(), 'Intragen')
        Genus = apps.get_model(app.lower(), 'Genus')
        Hybrid = apps.get_model(app.lower(), 'Hybrid')
        Species = apps.get_model(app.lower(), 'Species')
        Accepted = apps.get_model(app.lower(), 'Accepted')
        Ancestordescendant = apps.get_model(app.lower(), 'AncestorDescendant')
        Synonym = apps.get_model(app.lower(), 'Synonym')
        Distribution = apps.get_model(app.lower(), 'Distribution')
        SpcImages = apps.get_model(app.lower(), 'SpcImages')
        UploadFile = apps.get_model(app.lower(), 'UploadFile')
    return Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen


def getForms(request):
    family, app = '', ''
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'family' in request.POST:
        family = request.POST['family']
    if family:
        family = Family.objects.get(pk=family)
    try:
        app = Family.objects.get(pk=family)
        app = app.application
    except Family.DoesNotExist:
        app = ''
        family = ''
    if app == 'orchidaceae':
        from orchidaceae.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm
    elif app == 'bromeliaceae':
        from bromeliaceae.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, \
            HybridInfoForm, SpeciesForm, RenameSpeciesForm
    elif app == 'cactaceae':
        from cactaceae.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, \
            HybridInfoForm, SpeciesForm, RenameSpeciesForm
    elif app == 'other':
        from other.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, \
            HybridInfoForm, SpeciesForm, RenameSpeciesForm
    if app:
        return UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm
    else:
        return None,None,None,None,None,None,None,

def getAllGenera():
    # Call this when Family is not provided
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    BrGenus = apps.get_model('bromeliaceae', 'Genus')
    CaGenus = apps.get_model('cactaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    return OrGenus, BrGenus, CaGenus, OtGenus


def getAllSpecies():
    # Call this when Genus or Family is not provided
    OrSpecies = apps.get_model('orchidaceae', 'Species')
    BrSpecies = apps.get_model('bromeliaceae', 'Species')
    CaSpecies = apps.get_model('cactaceae', 'Species')
    OtSpecies = apps.get_model('other', 'Species')
    OrSpcImages = apps.get_model('orchidaceae', 'SpcImages')
    OrHybImages = apps.get_model('orchidaceae', 'HybImages')
    BrSpcImages = apps.get_model('bromeliaceae', 'SpcImages')
    CaSpcImages = apps.get_model('cactaceae', 'SpcImages')
    OtSpcImages = apps.get_model('other', 'SpcImages')

    return OrSpecies, BrSpecies, CaSpecies, OtSpecies, OrSpcImages, OrHybImages, BrSpcImages, CaSpcImages, OtSpcImages

def getFamilyImage(family):
    SpcImages = apps.get_model(family.application, 'SpcImages')
    return SpcImages.objects.filter(rank__lt=7).filter(status='approved').order_by('-rank','quality', '?')[0:1][0]

def orchid_home(request):
    family_list = []
    num_samples = 5
    orcfamily = Family.objects.get(pk='Orchidaceae')
    orcimage = getFamilyImage(orcfamily)

    brofamily = Family.objects.get(pk='Bromeliaceae')
    broimage = getFamilyImage(brofamily)
    cacfamily = Family.objects.get(pk='Cactaceae')
    cacimage = getFamilyImage(cacfamily)

    # Get random other families
    SpcImages = apps.get_model('other', 'SpcImages')
    Genus = apps.get_model('other', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    other_list = []
    for fam in sample_families:
        try:
            other_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            continue
        other_list.append(other_obj)
    del other_list[3:]
    # get random suculents
    sample_genus = Genus.objects.filter(is_succulent=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    try:
        succulent_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        succulent_obj = ''

    # get random carnivorous
    sample_genus = Genus.objects.filter(is_carnivorous=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    carnivorous_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]


    role = getRole(request)
    context = {'orcimage': orcimage, 'broimage': broimage, 'cacimage': cacimage,
               'other_list': other_list, 'succulent_obj': succulent_obj, 'carnivorous_obj': carnivorous_obj,
        'title': 'orchid_home', 'role': role }
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


# @login_required
def genera(request):
    path = resolve(request.path).url_name
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    num_show = 5

    page_length = 500
    alpha = ''
    sort = ''
    prev_sort = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']

    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae', 'Acanthaceae'))
    family_list = favorite.union(family_list)
    role = getRole(request)

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
        # No family (e.g. first landing on this page), show all genera except Orchidaceae, Bromeliaceae and Cactaceae
        OrGenus, BrGenus, CaGenus, OtGenus = getAllGenera()
        # brgenus_list = BrGenus.objects.all().order_by('genus')
        # cagenus_list = CaGenus.objects.all().order_by('genus')
        otgenus_list = OtGenus.objects.all().order_by('family','genus')
        # orgenus_list = OrGenus.objects.all().order_by('genus')
        # genus_list = list(chain(otgenus_list, brgenus_list, cagenus_list)) #, orgenus_list))
        # genus_list = sorted(allgenus_list, key=operator.attrgetter('genus'))
        genus_list = otgenus_list
    # Complete building genus list
    # Define sort
    if alpha and len(alpha) == 1:
        genus_list = genus_list.filter(genus__istartswith=alpha)
    if request.GET.get('sort'):
        sort = request.GET['sort']
        sort.lower()

    total = len(genus_list)
    write_output(request, str(family))
    context = {
        'genus_list': genus_list,  'app': app, 'sort': sort, 'prev_sort': prev_sort, 'total':total,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'family_list': family_list, 'title': 'taxonomy', 'alpha_list': alpha_list, 'alpha': alpha,
        'path': path
    }
    return render(request, "common/genera.html", context)


def xorchid_home(request):
    family_list = []
    num_samples = 5
    orcfamily = Family.objects.get(pk='Orchidaceae')
    orcimage = getFamilyImage(orcfamily)

    brofamily = Family.objects.get(pk='Bromeliaceae')
    broimage = getFamilyImage(brofamily)
    cacfamily = Family.objects.get(pk='Cactaceae')
    cacimage = getFamilyImage(cacfamily)

    # Get random other families
    SpcImages = apps.get_model('other', 'SpcImages')
    Genus = apps.get_model('other', 'Genus')
    sample_families = Genus.objects.filter(num_spcimage__gt=0).distinct().values_list('family', flat=True).order_by('?')[0:num_samples]
    other_list = []
    for fam in sample_families:
        try:
            other_obj = SpcImages.objects.filter(family=fam).order_by('?')[0:1][0]
        except:
            continue
        other_list.append(other_obj)
    del other_list[3:]
    # get random suculents
    sample_genus = Genus.objects.filter(is_succulent=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    try:
        succulent_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]
    except:
        succulent_obj = ''

    # get random carnivorous
    sample_genus = Genus.objects.filter(is_carnivorous=True).filter(num_spcimage__gt=0).order_by('?')[0:1][0]
    carnivorous_obj = SpcImages.objects.filter(genus=sample_genus).order_by('?')[0:1][0]


    role = getRole(request)
    context = {'orcimage': orcimage, 'broimage': broimage, 'cacimage': cacimage,
               'other_list': other_list, 'succulent_obj': succulent_obj, 'carnivorous_obj': carnivorous_obj,
        'title': 'orchid_home', 'role': role }
    return render(request, 'orchid_home.html', context)


def species(request):
    # path = resolve(request.path).url_name
    path = 'information'
    if str(request.user) == 'chariya':
        path = 'photos'
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    alpha = ''
    max_items = 5000

    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)
    genus = ''
    syn = ''
    role = getRole(request)
    if 'genus' in request.GET:
        genus = request.GET['genus']
        if genus:
            try:
                genus = Genus.objects.get(genus=genus)
            except Genus.DoesNotExist:
                genus = ''
    if 'syn' in request.GET:
        syn = request.GET['syn']


    if genus:
        species_list = Species.objects.filter(type='species').filter(
            cit_status__isnull=True).exclude(cit_status__exact='')
        # new genus has been selected. Now select new species/hybrid
        species_list = species_list.filter(genus=genus)
    elif family:
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
        app = 'other'
        Species = apps.get_model(app, 'Species')
        species_list = Species.objects.filter(type='species')
        # genus_list = Genus.objects.filter(family__application=app)
        # genus_list = genus_list.values_list('genus', flat=True)
        # species_list = species_list.filter(gen__family__application=app)


    if syn == 'N':
        species_list = species_list.exclude(status='synonym')
        syn = 'N'
    else:
        syn = 'Y'

    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL':
            alpha = ''
    if alpha != '':
        species_list = species_list.filter(species__istartswith=alpha)
    total = len(species_list)
    species_list = species_list.order_by('genus', 'species')
    message = ''

    if total > max_items:
        species_list = species_list[0:max_items]
        message = "List too long. Limit to 5000 items"
        total = max_items

    write_output(request, str(family))
    context = {
        'genus': genus, 'species_list': species_list, 'app': app, 'total':total, 'syn': syn,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'family_list': family_list, 'title': 'taxonomy', 'alpha_list': alpha_list, 'alpha': alpha,
        'message': message, 'path': path
    }
    return render(request, "common/species.html", context)


def hybrid(request):
    path = resolve(request.path).url_name
    path = 'genera'
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    hybrid_list = []
    genus = ''
    syn = ''
    primary = ''
    message = ''
    max_items = 5000
    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL':
            alpha = ''

    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)
    genus = ''
    if 'syn' in request.GET:
        syn = request.GET['syn']
    if 'primary' in request.GET:
        primary = request.GET['primary']
    role = getRole(request)
    if 'genus' in request.GET:
        genus = request.GET['genus']
        if genus:
            try:
                genus = Genus.objects.get(genus=genus)
            except Genus.DoesNotExist:
                genus = ''

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
        app = 'other'
        Species = apps.get_model(app, 'Species')
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

    if alpha != '':
        hybrid_list = hybrid_list.filter(species__istartswith=alpha)
    total = len(hybrid_list)
    # hybrid_list = hybrid_list.order_by('genus', 'species')
    if total > max_items:
        hybrid_list = hybrid_list[0:max_items]
        message = "List too long. Only show first 5000 items"
        total = max_items
    write_output(request, str(family))
    context = {
        'genus': genus, 'hybrid_list': hybrid_list, 'app': app, 'total':total, 'syn': syn,
        'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe, 'role': role,
        'family_list': family_list, 'title': 'taxonomy', 'alpha_list': alpha_list, 'alpha': alpha,
        'message': message, 'path': path, 'primary': primary,
    }
    return render(request, "common/hybrid.html", context)


def information(request, pid):
    ps_list = pp_list = ss_list = sp_list = seedimg_list = pollimg_list = ()
    role = getRole(request)
    offspring_list = []
    offspring_count = 0
    offspring_test = ''
    ancspc_list = []
    seedimg_list = []
    pollimg_list = []
    distribution_list = []
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    # If pid is a synonym, convert to accept
    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    genus = species.gen

    display_items = []
    synonym_list = Synonym.objects.filter(acc=pid)
    if species.gen.family == 'Orchidaceae':
        if species.type == 'species':
            accepted = species.accepted
            images_list = SpcImages.objects.filter(pid=species.pid).order_by('-rank', 'quality', '?')
            distribution_list = Distribution.objects.filter(pid=species.pid)
        else:
            accepted = species.hybrid
            images_list = HybImages.objects.filter(pid=species.pid).order_by('-rank', 'quality', '?')

    else:
        images_list = SpcImages.objects.filter(pid=species.pid).order_by('-rank', 'quality', '?')
        if species.type == 'species':
            accepted = species.accepted
        else:
            accepted = species.hybrid

    # Build display in main table
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
    # Build parents display for Orchidaceae hybrid  only
    from orchidaceae.models import AncestorDescendant
    seed_list = Hybrid.objects.filter(seed_id=species.pid).order_by('pollen_genus', 'pollen_species')
    pollen_list = Hybrid.objects.filter(pollen_id=species.pid)
    # Remove duplicates. i.e. if both parents are synonym.
    temp_list = pollen_list
    for x in temp_list:
        if x.seed_status() == 'syn' and x.pollen_status() == 'syn':
            pollen_list = pollen_list.exclude(pid=x.pid_id)
    pollen_list = pollen_list.order_by('seed_genus', 'seed_species')
    offspring_list = chain(list(seed_list), list(pollen_list))
    offspring_count = len(seed_list) + len(pollen_list)
    if offspring_count > 5000:
        offspring_list = offspring_list[0:5000]

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
        if ancspc_list:
            for x in ancspc_list:
                img = x.aid.get_best_img()
                if img:
                    x.img = img.image_file
    write_output(request, str(family))
    context = {'pid': species.pid, 'species': species, 'synonym_list': synonym_list, 'accepted': accepted,
               'title': 'information', 'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus,
               'display_items': display_items, 'distribution_list': distribution_list, 'family': family,
               'offspring_list': offspring_list, 'offspring_count': offspring_count,
               'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'app': app, 'role': role, 'ancspc_list': ancspc_list,
               }
    return render(request, "common/information.html", context)


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
    if app == 'orchidaceae' and species.type == 'hybrid':
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


def photos(request, pid=None):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = ''
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
        return HttpResponseRedirect('/')
        # return HttpResponse(redirect_message)
    role = getRole(request)

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    variety = ''
    tail = ''

    if family.family == 'Orchidaceae' and species.type == 'hybrid':
        all_list = HybImages.objects.filter(pid=species.pid)
    else:
        all_list = SpcImages.objects.filter(pid=species.pid)

    # Get private photos

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, species, Species, UploadFile, SpcImages, HybImages, role)
    # Happened when a curator request an author photos
    # if role == 'cur':
    #     if author:
    #         public_list = all_list.filter(rank__gt=0).filter(author=author)
    #         private_list = all_list.filter(rank=0).filter(author=author)
    # else:  # anonymous
    #     public_list = all_list.filter(rank__gt=0)

    # upload_list = UploadFile.objects.filter(pid=species.pid)
    # if role != 'cur':
    #     if author:
    #         upload_list = upload_list.filter(author=author)
    if app == 'orchidaceae' and species.type == 'hybrid':
        rank_update(request, HybImages)
        quality_update(request, HybImages)
    else:
        rank_update(request, SpcImages)
        quality_update(request, SpcImages)
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

    write_output(request, str(family))
    context = {'species': species, 'author': author, 'author_list': author_list, 'family': family,
               'variety': variety, 'pho': 'active', 'tab': 'pho', 'app':app,
               'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'title': 'photos', 'namespace': 'common',
               }
    return render(request, 'common/photos.html', context)

def xphotos(request, pid=None):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = ''
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

    if species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        species = Species.objects.get(pk=pid)

    variety = ''
    tail = ''

    if family.family == 'Orchidaceae' and species.type == 'hybrid':
        all_list = HybImages.objects.filter(pid=species.pid)
    else:
        all_list = SpcImages.objects.filter(pid=species.pid)

    # Get private photos

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, species, Species, UploadFile, SpcImages, HybImages, role)
    # Happened when a curator request an author photos
    # if role == 'cur':
    #     if author:
    #         public_list = all_list.filter(rank__gt=0).filter(author=author)
    #         private_list = all_list.filter(rank=0).filter(author=author)
    # else:  # anonymous
    #     public_list = all_list.filter(rank__gt=0)

    # upload_list = UploadFile.objects.filter(pid=species.pid)
    # if role != 'cur':
    #     if author:
    #         upload_list = upload_list.filter(author=author)
    if app == 'orchidaceae' and species.type == 'hybrid':
        rank_update(request, HybImages)
        quality_update(request, HybImages)
    else:
        rank_update(request, SpcImages)
        quality_update(request, SpcImages)
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

    write_output(request, str(family))
    context = {'species': species, 'author': author, 'author_list': author_list, 'family': family,
               'variety': variety, 'pho': 'active', 'tab': 'pho', 'app':app,
               'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'role': role, 'title': 'photos', 'namespace': 'common',
               }
    return render(request, 'common/photos.html', context)

def browse(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    reqsubgenus = reqsection = reqsubsection = reqseries = ''
    subgenus_obj = section_obj = subsection_obj = series_obj = ''
    subgenus_list = section_list = subsection_list = series_list = []
    page_range = page_list = last_page = next_page = prev_page = page = first_item = last_item = alpha = total = ''
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

    if type == 'species':
        if 'subgenus' in request.GET:
            reqsubgenus = request.GET['subgenus']
            if reqsubgenus:
                try:
                    subgenus_obj = Subgenus.objects.get(pk=reqsubgenus)
                except Subgenus.DoesNotExist:
                    subgenus_obj = ''
        if 'section' in request.GET:
            reqsection = request.GET['section']
            if reqsection:
                try:
                    section_obj = Section.objects.get(pk=reqsection)
                except Section.DoesNotExist:
                    section_obj = ''
        if 'subsection' in request.GET:
            reqsubsection = request.GET['subsection']
            if reqsubsection:
                try:
                    subsection_obj = Subsection.objects.get(pk=reqsubsection)
                except Subsection.DoesNotExist:
                    subsection_obj = ''
        if 'series' in request.GET:
            reqseries = request.GET['series']
            if reqseries:
                try:
                    series_obj = Series.objects.get(pk=reqseries)
                except Series.DoesNotExist:
                    series_obj = ''
    elif type == 'hybrid':
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

    genus, pid_list, intragen_list = getPartialPid(reqgenus, type, 'accepted', app)
    if pid_list and group:
        if group == 'succulent':
            pid_list = pid_list.filter(gen__is_succulent=True)
        elif group == 'carnivorous':
            pid_list = pid_list.filter(gen__is_carnivorous=True)
    total = len(pid_list)
    num_show = 5
    page_length = 20

    if pid_list:
        img_list = Species.objects.filter(type=type).exclude(status='synonym')
        if display == 'checked':
            img_list = img_list.filter(num_image__gt=0)
        if type == 'species':
            if intragen_list:
                # intragen_list = Intragen.objects.filter(genus__icontains=genus)
                subgenus_list = intragen_list.exclude(subgenus__isnull=True).exclude(subgenus__exact='').distinct().values(
                    'subgenus').order_by('subgenus')
                section_list = intragen_list.exclude(section__isnull=True).exclude(section__exact='').distinct().values(
                    'section').order_by('section')
                subsection_list = intragen_list.exclude(subsection__isnull=True).exclude(subsection__exact='').distinct().values(
                    'subsection').order_by('subsection')
                series_list = intragen_list.exclude(series__isnull=True).exclude(series__exact='').distinct().values(
                    'series').order_by('series')
            if reqsubgenus:
                section_list = section_list.filter(subgenus=reqsubgenus)
                subsection_list = subsection_list.filter(subgenus=reqsubgenus)
                series_list = series_list.filter(subgenus=reqsubgenus)
            if reqsection:
                subsection_list = subsection_list.filter(section=reqsection)
                series_list = series_list.filter(section=reqsection)

            pid_list = pid_list.filter(type='species')
            if reqsubgenus:
                pid_list = pid_list.filter(accepted__subgenus=reqsubgenus)
            if reqsection:
                pid_list = pid_list.filter(accepted__section=reqsection)
            if reqsubsection:
                pid_list = pid_list.filter(accepted__subsection=reqsubsection)
            if reqseries:
                pid_list = pid_list.filter(accepted__series=reqseries)
            pid_list = pid_list.distinct().values_list('pid',flat=True)

            img_list = img_list.filter(pid__in=pid_list)

        elif type == 'hybrid':
            pid_list = pid_list.filter(type='hybrid').distinct().values_list('pid',flat=True)
            img_list = img_list.filter(pid__in=pid_list)
            if seed_genus and pollen_genus:
                img_list = img_list.filter(Q(hybrid__seed_genus=seed_genus) & Q(hybrid__pollen_genus=pollen_genus) | Q(
                        hybrid__seed_genus=pollen_genus) & Q(hybrid__pollen_genus=seed_genus))
            elif seed_genus:
                img_list = img_list.filter(Q(hybrid__seed_genus=seed_genus) | Q(hybrid__pollen_genus=seed_genus))
            elif pollen_genus:
                img_list = img_list.filter(Q(hybrid__seed_genus=pollen_genus) | Q(hybrid__pollen_genus=pollen_genus))
            if seed:
                img_list = img_list.filter(Q(hybrid__seed_species=seed) | Q(hybrid__pollen_species=seed))
            if pollen:
                img_list = img_list.filter(Q(hybrid__seed_species=pollen) | Q(hybrid__pollen_species=pollen))
        my_full_list = []
        if 'alpha' in request.GET:
            alpha = request.GET['alpha']
            if alpha == 'ALL':
                alpha = ''
            elif len(alpha > 1):
                alpha = alpha[0].upper()
        if img_list:
            if display == "checked":
                img_list = img_list.filter(num_image__gt=0)
            if alpha:
                if reqgenus:
                    img_list = img_list.filter(species__istartswith=alpha)
                else:
                    img_list = img_list.filter(genus__istartswith=alpha)

            img_list = img_list.order_by('genus', 'species')
            for x in img_list:
                if x.get_best_img():
                    if family.family == 'Orchidaceae':
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
        total = len(my_full_list)
        page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
            = mypaginator(request, my_full_list, page_length, num_show)
    genus_list = Genus.objects.all()
    if display == 'checked':
        if type == 'species':
            genus_list = genus_list.filter(num_spcimage__gt=0)
        else:
            genus_list = genus_list.filter(num_hybimage__gt=0)
    write_output(request, str(family))
    context = {'family':family,
        'page_list': page_list, 'type': type, 'genus': reqgenus, 'display': display, 'genus_list': genus_list,
        'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
        'page': page, 'alpha': alpha, 'alpha_list': alpha_list, 'total': total,
        'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
        'title': 'browse', 'section': 'list', 'role': role,
    }
    if type == 'species':
        context.update({'subgenus_list': subgenus_list, 'subgenus_obj': subgenus_obj,
        'section_list': section_list, 'section_obj': section_obj,
        'subsection_list': subsection_list, 'subsection_obj': subsection_obj,
        'series_list': series_list, 'series_obj': series_obj,
                    })

    else:
        context.update({'seed_genus': seed_genus, 'pollen_genus': pollen_genus,'seed': seed, 'pollen': pollen,})

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
    elif family:
        species_list = species_list.filter(gen__family=family)
    return species_list
    # return species_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')


def search_species(request):
    path = resolve(request.path).url_name
    path = 'information'
    if str(request.user) == 'chariya':
        path = 'photos'

    # from itertools import chain
    min_score = 20
    spc_string = ''
    genus_string = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    app = ''
    species_list = []
    genus_list = []
    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)

    role = getRole(request)
    # if higher rank taxon requested
    if 'family' in request.GET:
        family = request.GET['family'].strip()
    if family:
        family = Family.objects.get(family=family)
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].subtribe()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
    if ' ' not in spc_string:
        genus_string = spc_string

    fuzzy = ''
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

    if 'app' in request.GET:
        app = request.GET['app']
    if not app:
        # Default to orchids
        app = 'orchidaceae'
    if app == 'orchidaceae':
        family = Family.objects.get(family='Orchidaceae')
    elif app == 'cactaceae':
        family = Family.objects.get(family='Cactaceae')
    elif app == 'bromeliaceae':
        family = Family.objects.get(family='Bromeliaceae')
    else:
        family = ''

    spc = spc_string
    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    fuzzy_list = []
    genus_list = []
    match_list = []

    # Perform conventional match
    if not fuzzy:
        if genus_string:  # Seach genus table
            if family and family.application == 'other':
                family = ''
            abrev = ''
            CaGenus = apps.get_model('cactaceae', 'Genus')
            OrGenus = apps.get_model('orchidaceae', 'Genus')
            OtGenus = apps.get_model('other', 'Genus')
            BrGenus = apps.get_model('bromeliaceae', 'Genus')
            genus_list = []
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description', 'num_species')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description', 'num_species')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description', 'num_species')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description', 'num_species')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                # If the first word is genus hint, compare species and the tail
                if x['genus']:
                    score = fuzz.ratio(x['genus'].lower(), genus_string)
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list

        spc_string = spc_string.replace('.', '')
        spc_string = spc_string.replace(' mem ', ' Memoria ')
        spc_string = spc_string.replace(' Mem ', ' Memoria ')
        words = spc_string.split()
        grex = spc_string.split(' ', 1)
        if len(grex) > 1:
            grex = grex[1]
        else:
            grex = ''
        subgrex = grex.rsplit(' ', 1)[0]

        match_list = species_list.filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex))
        if len(match_list) == 0:
            fuzzy = 1
            url = "%s?role=%s&app=%s&family=%s&spc_string=%s&fuzzy=1" % (reverse('common:search_species'), role, app, family, spc_string)
            return HttpResponseRedirect(url)

    # Perform Fuzzy search if requested (fuzzy = 1) or if no match found:
    else:
        first_try = species_list.filter(species=spc)
        min_score = 60
        for x in species_list:
            if x.binomial:
                score = fuzz.ratio(x.binomial, spc)
                if score >= min_score:
                    fuzzy_list.append([x, score])
        fuzzy_list.sort(key=lambda k: (-k[1], k[0].binomial))
        del fuzzy_list[20:]
    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list),
               'family_list': family_list, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)


def xxsearch_species(request):
    path = resolve(request.path).url_name

    # from itertools import chain
    min_score = 20
    spc_string = ''
    genus_string = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    species_list = []
    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)

    role = getRole(request)
    # if higher rank taxon requested
    if 'family' in request.GET:
        family = request.GET['family'].strip()
    if family:
        family = Family.objects.get(family=family)
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].subtribe()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)

    if 'genus_string' in request.GET:
        genus_string = request.GET['genus_string'].strip()

    if genus_string.endswith('.'):
        abrev = genus_string
        abrev.replace('.','')

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()


    # # CASE 1: request genus_string only
    if genus_string and not spc_string:  # Seach genus table
        if family and family.application == 'other':
            family = ''
        abrev = ''
        CaGenus = apps.get_model('cactaceae', 'Genus')
        OrGenus = apps.get_model('orchidaceae', 'Genus')
        OtGenus = apps.get_model('other', 'Genus')
        BrGenus = apps.get_model('bromeliaceae', 'Genus')
        genus_list = []
        cagenus_list = CaGenus.objects.all()
        # if subtribe:
        #     cagenus_list = cagenus_list.filter(gen__subtribe=subtribe)
        # elif tribe:
        #     cagenus_list = cagenus_list.filter(tribe=tribe)
        # elif subfamily:
        #     cagenus_list = cagenus_list.filter(subfamily=subfamily)
        # elif family:
        #     cagenus_list = cagenus_list.filter(family=family)
        cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description')
        #
        orgenus_list = OrGenus.objects.all()
        # if subtribe:
        #     orgenus_list = orgenus_list.filter(gen__subtribe=subtribe)
        # elif tribe:
        #     orgenus_list = orgenus_list.filter(tribe=tribe)
        # elif subfamily:
        #     orgenus_list = orgenus_list.filter(subfamily=subfamily)
        # elif family:
        #     orgenus_list = orgenus_list.filter(family=family)
        orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description')
        #
        brgenus_list = BrGenus.objects.all()
        # if subtribe:
        #     brgenus_list = brgenus_list.filter(gen__subtribe=subtribe)
        # elif tribe:
        #     brgenus_list = brgenus_list.filter(tribe=tribe)
        # elif subfamily:
        #     brgenus_list = brgenus_list.filter(subfamily=subfamily)
        # elif family:
        #     brgenus_list = brgenus_list.filter(family=family)
        brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description')
        #
        otgenus_list = OtGenus.objects.all()
        # if subtribe:
        #     otgenus_list = otgenus_list.filter(gen__subtribe=subtribe)
        # elif tribe:
        #     otgenus_list = otgenus_list.filter(tribe=tribe)
        # elif subfamily:
        #     otgenus_list = otgenus_list.filter(subfamily=subfamily)
        # elif family:
        #     otgenus_list = otgenus_list.filter(family=family)
        otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description')
        genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)

        search_list = []
        for x in genus_list:
            # If the first word is genus hint, compare species and the tail
            score = fuzz.ratio(x['genus'].lower(), genus_string)
            if score >= min_score:
                search_list.append([x, score])

        search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
        del search_list[20:]
        write_output(request, genus_string)
        context = {'genus_list': search_list, 'genus_string': genus_string, 'family_list': family_list,
                   'title': 'search', 'role': role, 'path': 'genera',
                   'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                   }
        return django.shortcuts.render(request, "common/search_species.html", context)

    # request spc_string and or genus_string. Search Species table
    # Application selected from the dropdown search filter
    if 'app' in request.GET:
        app = request.GET['app']
    if not app:
        # Default to orchids
        app = 'orchidaceae'
    if app == 'orchidaceae':
        family = Family.objects.get(family='Orchidaceae')
    elif app == 'cactaceae':
        family = Family.objects.get(family='Cactaceae')
    elif app == 'bromeliaceae':
        family = Family.objects.get(family='Bromeliaceae')
    else:
        family = ''

    spc = spc_string
    if genus_string:
        spc = genus_string + ' ' + spc_string

    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    # Regular match:
    search_list = []
    first_try = species_list.filter(species=spc)






    min_score = 60
    for x in species_list:
        score = fuzz.ratio(x.binomial, spc)
        if score >= min_score:
            search_list.append([x, score])
    search_list.sort(key=lambda k: (-k[1], k[0].binomial))
    del search_list[20:]
    # gencount = len(genus_list)
    # write_output(request, str(family))
    write_output(request, spc_string)
    context = {'species_list': search_list, 'genus_string': genus_string, 'spc_string': spc_string,
               'family_list': family_list, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)


def xsearch_species(request):
    path = resolve(request.path).url_name

    # from itertools import chain
    min_score = 20
    keyword = ''
    spc_string = ''
    genus_string = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    species_list = []
    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)

    role = getRole(request)
    # No space allowed in genera keyword
    if 'family' in request.GET:
        family = request.GET['family'].strip()
    if family:
        family = Family.objects.get(family=family)

    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)

    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)

    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].subtribe()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)

    if 'genus_string' in request.GET:
        genus_string = request.GET['genus_string'].strip()

    if genus_string:
        abrev = spc_string
        abrev.replace('.','')
    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()

    # # CASE 1: request genus_string only
    if genus_string and not spc_string:  # Seach genus table
        if family and family.application == 'other':
            family = ''
        abrev = ''
        CaGenus = apps.get_model('cactaceae', 'Genus')
        OrGenus = apps.get_model('orchidaceae', 'Genus')
        OtGenus = apps.get_model('other', 'Genus')
        BrGenus = apps.get_model('bromeliaceae', 'Genus')
        genus_list = []
        cagenus_list = CaGenus.objects.all()
        if subtribe:
            cagenus_list = cagenus_list.filter(gen__subtribe=subtribe)
        elif tribe:
            cagenus_list = cagenus_list.filter(tribe=tribe)
        elif subfamily:
            cagenus_list = cagenus_list.filter(subfamily=subfamily)
        elif family:
            cagenus_list = cagenus_list.filter(family=family)
        cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description')

        orgenus_list = OrGenus.objects.all()
        if subtribe:
            orgenus_list = orgenus_list.filter(gen__subtribe=subtribe)
        elif tribe:
            orgenus_list = orgenus_list.filter(tribe=tribe)
        elif subfamily:
            orgenus_list = orgenus_list.filter(subfamily=subfamily)
        elif family:
            orgenus_list = orgenus_list.filter(family=family)
        orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description')

        brgenus_list = BrGenus.objects.all()
        if subtribe:
            brgenus_list = brgenus_list.filter(gen__subtribe=subtribe)
        elif tribe:
            brgenus_list = brgenus_list.filter(tribe=tribe)
        elif subfamily:
            brgenus_list = brgenus_list.filter(subfamily=subfamily)
        elif family:
            brgenus_list = brgenus_list.filter(family=family)
        brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description')

        otgenus_list = OtGenus.objects.all()
        if subtribe:
            otgenus_list = otgenus_list.filter(gen__subtribe=subtribe)
        elif tribe:
            otgenus_list = otgenus_list.filter(tribe=tribe)
        elif subfamily:
            otgenus_list = otgenus_list.filter(subfamily=subfamily)
        elif family:
            otgenus_list = otgenus_list.filter(family=family)
        otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status', 'type', 'description')
        genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)

        if 'genus_string' in request.GET:
            genus_string = request.GET['genus_string'].strip()
        if genus_string.endswith('.'):
            abrev = genus_string

        search_list = []
        for x in genus_list:
            # If the first word is genus hint, compare species and the tail
            score = fuzz.ratio(x['genus'].lower(), genus_string)
            if score >= min_score:
                search_list.append([x, score])

        search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
        del search_list[20:]
        write_output(request, genus_string)
        context = {'genus_list': search_list, 'genus_string': genus_string, 'family_list': family_list,
                   'title': 'search', 'role': role, 'path': path
,
                   'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                   }
        return django.shortcuts.render(request, "common/search_species.html", context)

    # else: request spc_string and or genus_string. Search Species table
    spc = spc_string
    if genus_string:
        spc = genus_string + ' ' + spc_string

    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other', family, subfamily, tribe, subtribe)
    else:
        species_list = get_species_list('other', family, subfamily, tribe, subtribe)

    search_list = []
    min_score = 60
    for x in species_list:
        score = fuzz.ratio(x.binomial, spc)
        if score >= min_score:
            search_list.append([x, score])
    search_list.sort(key=lambda k: (-k[1], k[0].binomial))
    del search_list[20:]
    # gencount = len(genus_list)
    # write_output(request, str(family))
    write_output(request, spc_string)
    context = {'species_list': search_list, 'genus_string': genus_string, 'spc_string': spc_string,
               'family_list': family_list, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'title': 'search', 'role': role, 'path': path}
    return django.shortcuts.render(request, "common/search_species.html", context)


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


# @login_required
def deletephoto(request, orid, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    spcall = Species.objects.all()


    try:
        image = UploadFile.objects.get(pk=orid)
    except UploadFile.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)

    try:
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
    role = getRole(request)

    if area == 'allpending':
        # bulk delete by curators from all_pending tab
        url = "%s&page=%s&type=%s&days=%d&family=" % (reverse('detail:curate_pending'), page, ortype, days, family)
    elif area == 'curate_newupload':  # from curate_newupload (all rank 0)
        # Requested from all upload photos
        url = "%s?page=%s" % (reverse('detail:curate_newupload'), page)
    url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)

    # Finally remove file if exist
    if os.path.isfile(filename):
        os.remove(filename)

    write_output(request, str(family))
    return HttpResponseRedirect(url)


# @login_required
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

        if family == 'Orchidaceae' and species.type == 'hybrid':
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
        url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)
    write_output(request, str(family))
    return HttpResponseRedirect(url)


# @login_required
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
        write_output(request, ">>> approvemediaphoto FAIL: " + species.textname() + "-" + str(orid))
        msg = "uploaded file #" + str(orid) + "does not exist"
        url = "%s?role=%s&msg=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, msg, family)
        return HttpResponseRedirect(url)

    old_name = os.path.join(settings.MEDIA_ROOT, str(upl.image_file_path))
    tmp_name = os.path.join("/webapps/static/tmp/", str(upl.image_file_path))

    filename, ext = os.path.splitext(str(upl.image_file_path))
    if family.family != 'Orchidaceae' or species.type == 'species':
        if family.family == 'Orchidaceae':
            spc = SpcImages(pid=species.accepted, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                        source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                        description=upl.description, location=upl.location, created_date=upl.created_date)
        else:
            spc = SpcImages(pid=species, author=upl.author, user_id=upl.user_id, name=upl.name, awards=upl.awards,
                        source_file_name=upl.source_file_name, variation=upl.variation, form=upl.forma, rank=0,
                        description=upl.description, location=upl.location, created_date=upl.created_date)
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
                        description=upl.description, location=upl.location, created_date=upl.created_date)
        spc.approved_by = request.user
        if family.family == 'Orchidaceae':
            newdir = os.path.join(settings.STATIC_ROOT, "utils/images/hybrid")
        else:
            newdir = os.path.join(settings.STATIC_ROOT, "utils/images/" + str(family))
        image_file = "hyb_"

    image_file = image_file + str(format(upl.pid_id, "09d")) + "_" + str(format(upl.id, "09d"))
    new_name = os.path.join(newdir, image_file)
    if not os.path.exists(new_name + ext):
        try:
            shutil.copy(old_name, tmp_name)
            shutil.move(old_name, new_name + ext)
        except shutil.Error:
            # upl.delete()
            url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)
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
                    url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)
                    return HttpResponseRedirect(url)
                spc.image_file = image_file
                break
            i += 1

    spc.save()
    # hist.save()
    upl.approved = True
    upl.delete(0)
    write_output(request, str(family))
    url = "%s?role=%s&family=%s" % (reverse('common:photos', args=(species.pid,)), role, family)
    return HttpResponseRedirect(url)


# @login_required
def myphoto(request, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    role = getRole(request)
    if not role or role == 'pub':
        url = "%s?role=%s" % (reverse('common:information', args=(pid,)), role)
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

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, app, species, Species, UploadFile, SpcImages, HybImages, role)
    author = Photographer.objects.get(user_id=request.user)
    if author:
        public_list = public_list.filter(author=author)
        private_list = private_list.filter(author=author)
    context = {'species': species, 'private_list': private_list, 'public_list': public_list, 'upload_list': upload_list,
               'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list, 'author_list': author_list,
               'pri': 'active', 'role': role, 'author': author,
               'title': 'myphoto',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto.html', context)


# @login_required
def myphoto_browse_spc(request):
    author, author_list = get_author(request)
    role = getRole(request)
    if role == 'pub':
        send_url = "%s?tab=%s" % (reverse('common:browse'), 'sum')
        return HttpResponseRedirect(send_url)
    if role == 'cur' and 'author' in request.GET:
        author = request.GET['author']
        author = Photographer.objects.get(pk=author)
    else:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, '', species, Species, UploadFile, SpcImages, HybImages, role)

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
               'role': role, 'brwspc': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,
               'title': 'myphoto_browse',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_spc.html', context)


# @login_required
def myphoto_browse_hyb(request):
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

    private_list, public_list, upload_list, myspecies_list, myhybrid_list = getmyphotos(author, '', species, Species, UploadFile, SpcImages, HybImages, role)

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
               'role': role, 'brwhyb': 'active', 'author': author,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'author_list': author_list,
               'title': 'myphoto_browse',
               }
    write_output(request, str(family))
    return render(request, 'common/myphoto_browse_hyb.html', context)


# @login_required
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

    write_output(request, str(family))
    context = {'file_list': page_list,
               'tab': 'upl', 'role': role, 'upl': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page, 'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app, 'title': 'curate_newupload', 'section': 'Curator Corner',
               }
    return render(request, "common/curate_newupload.html", context)


# @login_required
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

    role = getRole(request)
    write_output(request, str(family))
    title = 'curate_pending'
    context = {'file_list': page_list, 'type': ortype,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app, 'title': title,
               }
    return render(request, 'common/curate_pending.html', context)


# @login_required
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
    context = {'file_list': page_list, 'type': ortype,
               'tab': 'pen', 'role': role, 'pen': 'active', 'days': days,
               'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
               'page': page,
               'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
               'app': app, 'title': 'curate_newapproved',
               }
    return render(request, 'common/curate_newapproved.html', context)



# NOT USED
def home(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
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
    context = {'title': 'orchid_home', 'role': role, 'randimages': randimages, 'tab': 'sum', }
    return render(request, 'home.html', context)
def xxorchid_home(request):
    if 'family' in request.GET:
        family = request.GET['family']
    else:
        family = 'Orchidaceae'

    try:
        family = Family.objects.get(pk=family)
    except Family.DoesNotExist:  # Default to OR
        family = Family.objects.get(pk='Orchidaceae')

    app = family.application
    Species = apps.get_model(app, 'Species')
    SpcImages = apps.get_model(app, 'SpcImages')
    if app == 'orchidaceae':
        HybImages = apps.get_model(app, 'HybImages')
    else:
        HybImages = ''

    # OrSpecies, BrSpecies, CaSpecies, OtSpecies, OrSpcImages, OrHybImages, BrSpcImages, CaSpcImages, OtSpcImages = getAllSpecies()

    if family == 'Orchidaceae':
        num_img = 5
        randspecies = Species.objects.filter(num_image__gt=0).filter(type='species').exclude(
            status='synonym').values_list('pid', flat=True).order_by('?')[0:num_img]
        randhybrid = Species.objects.filter(num_image__gt=0).filter(type='hybrid').exclude(
            status='synonym').values_list('pid', flat=True).order_by('?')[0:num_img]
        randimages = []
        for e in randspecies:
            img = OrSpcImages.objects.filter(pid=e).filter(rank=5).order_by('quality', '?')[0:1]
            if img and len(img):
                randimages.append(img[0])
        for e in randhybrid:
            img = OrHybImages.objects.filter(pid=e).filter(rank=5).order_by('quality', '?')[0:1]
            if img and len(img):
                randimages.append(img[0])
    elif family == 'Bromeliaceae':
        randspecies = Species.objects.filter(num_image__gt=0).filter(type='species').exclude(status='synonym').values_list('pid', flat=True).order_by('?')[0:2]
        randimages = []
        for e in randspecies:
            img = SpcImages.objects.filter(pid=e).filter(rank=5).order_by('quality', '?')[0:1]
            if img and len(img):
                randimages.append(img[0])
    elif family == 'Cactaceae':
        randspecies = CaSpecies.objects.filter(num_image__gt=0).filter(type='species').exclude(status='synonym').values_list('pid', flat=True).order_by('?')[0:2]
        randimages = []
        for e in randspecies:
            img = SpcImages.objects.filter(pid=e).filter(rank=5).order_by('quality', '?')[0:1]
            if img and len(img):
                randimages.append(img[0])
    else:
        randspecies = Species.objects.filter(num_image__gt=0).filter(type='species').exclude(status='synonym').values_list('pid', flat=True).order_by('?')[0:6]
        randimages = []
        for e in randspecies:
            img = SpcImages.objects.filter(pid=e).filter(rank=5).order_by('quality', '?')[0:1]
            if img and len(img):
                randimages.append(img[0])

    # Number of visits to this view, as counted in the session variable.
    # num_visits = request.session.get('num_visits', 0)
    # request.session['num_visits'] = num_visits + 1
    random.shuffle(randimages)
    role = getRole(request)
    context = {'title': 'orchid_home', 'role': role, 'randimages': randimages, 'tab': 'sum', 'family': family }
    return render(request, 'orchid_home.html', context)

def xsearch_genus(request):
    # from itertools import chain
    genus_string = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    min_score = 60
    gensyn_list = []
    genus_list = []
    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)

    if 'family' in request.GET:
        family = request.GET['family'].strip()
    if family:
        family = Family.objects.get(family=family)

    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)

    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(subfamily=tribe)

    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].subtribe()
    if subtribe:
        subtribe = Subtribe.objects.get(subfamily=subtribe)

    CaGenus = apps.get_model('cactaceae', 'Genus')
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    BrGenus = apps.get_model('bromeliaceae', 'Genus')

    role = getRole(request)
    genus_list = []

    # First consolidate list from all families
    # No space allowed in genus_string
    cagenus_list = CaGenus.objects.all()
    if subtribe:
        cagenus_list = cagenus_list.filter(gen__subtribe=subtribe)
    elif tribe:
        cagenus_list = cagenus_list.filter(tribe=tribe)
    elif subfamily:
        cagenus_list = cagenus_list.filter(subfamily=subfamily)
    elif family:
        cagenus_list = cagenus_list.filter(family=family)
    cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status')

    orgenus_list = OrGenus.objects.all()
    if subtribe:
        orgenus_list = orgenus_list.filter(gen__subtribe=subtribe)
    elif tribe:
        orgenus_list = orgenus_list.filter(tribe=tribe)
    elif subfamily:
        orgenus_list = orgenus_list.filter(subfamily=subfamily)
    elif family:
        orgenus_list = orgenus_list.filter(family=family)
    orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status')

    brgenus_list = BrGenus.objects.all()
    if subtribe:
        brgenus_list = brgenus_list.filter(gen__subtribe=subtribe)
    elif tribe:
        brgenus_list = brgenus_list.filter(tribe=tribe)
    elif subfamily:
        brgenus_list = brgenus_list.filter(subfamily=subfamily)
    elif family:
        brgenus_list = brgenus_list.filter(family=family)
    brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status')

    otgenus_list = OtGenus.objects.all()
    if subtribe:
        otgenus_list = otgenus_list.filter(gen__subtribe=subtribe)
    elif tribe:
        otgenus_list = otgenus_list.filter(tribe=tribe)
    elif subfamily:
        otgenus_list = otgenus_list.filter(subfamily=subfamily)
    elif family:
        otgenus_list = otgenus_list.filter(family=family)
    otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status')
    genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)

    if 'genus_string' in request.GET:
        genus_string = request.GET['genus_string'].strip()
    if genus_string:
        abrev = genus_string
        abrev.replace('.', '')

    search_list = []
    for x in genus_list:
        # If the first word is genus hint, compare species and the tail
        score = fuzz.ratio(x['genus'].lower(), genus_string)
        if score >= min_score:
            search_list.append([x, score])
    search_list.sort(key=lambda k: (-k[1], k[0]['genus']))

        # gensyn_list = otgensyn_list.union(orgensyn_list).union(cagensyn_list).union(brgensyn_list)
    write_output(request, genus_string)
    context = {'genus_list': search_list, 'gensyn_list': gensyn_list, 'genus_string': genus_string, 'family_list': family_list,
               'title': 'search', 'role': role,
               'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               }
    return django.shortcuts.render(request, "common/search_genus.html", context)

def xxsearch_genus(request):
    # from itertools import chain
    keyword = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    gensyn_list = []
    genus_list = []
    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)

    if 'family' in request.GET:
        family = request.GET['family'].strip()
    if family:
        family = Family.objects.get(family=family)

    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)

    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(subfamily=tribe)

    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].subtribe()
    if subtribe:
        subtribe = Subtribe.objects.get(subfamily=subtribe)

    CaGenus = apps.get_model('cactaceae', 'Genus')
    OrGenus = apps.get_model('orchidaceae', 'Genus')
    OtGenus = apps.get_model('other', 'Genus')
    BrGenus = apps.get_model('bromeliaceae', 'Genus')

    CaGensyn = apps.get_model('cactaceae', 'Gensyn')
    OrGensyn = apps.get_model('orchidaceae', 'Gensyn')
    OtGensyn = apps.get_model('other', 'Gensyn')
    BrGensyn = apps.get_model('bromeliaceae', 'Gensyn')

    role = getRole(request)
    genus_list = []
    # No space allowed in genera keyword
    if 'keyword' in request.GET:
        keyword = request.GET['keyword'].strip()
    if keyword:
        abrev = keyword
        abrev.replace('.','')

        cagenus_list = CaGenus.objects.filter(Q(genus__icontains=keyword) | Q(abrev=abrev))
        if subtribe:
            cagenus_list = cagenus_list.filter(gen__subtribe=subtribe)
        elif tribe:
            cagenus_list = cagenus_list.filter(tribe=tribe)
        elif subfamily:
            cagenus_list = cagenus_list.filter(subfamily=subfamily)
        elif family:
            cagenus_list = cagenus_list.filter(family=family)
        cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status')

        orgenus_list = OrGenus.objects.filter(Q(genus__icontains=keyword) | Q(abrev=abrev))
        if subtribe:
            orgenus_list = orgenus_list.filter(gen__subtribe=subtribe)
        elif tribe:
            orgenus_list = orgenus_list.filter(tribe=tribe)
        elif subfamily:
            orgenus_list = orgenus_list.filter(subfamily=subfamily)
        elif family:
            orgenus_list = orgenus_list.filter(family=family)
        orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status')

        brgenus_list = BrGenus.objects.filter(Q(genus__icontains=keyword) | Q(abrev=abrev))
        if subtribe:
            brgenus_list = brgenus_list.filter(gen__subtribe=subtribe)
        elif tribe:
            brgenus_list = brgenus_list.filter(tribe=tribe)
        elif subfamily:
            brgenus_list = brgenus_list.filter(subfamily=subfamily)
        elif family:
            brgenus_list = brgenus_list.filter(family=family)
        brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status')

        otgenus_list = OtGenus.objects.filter(Q(genus__icontains=keyword) | Q(abrev=abrev))
        if subtribe:
            otgenus_list = otgenus_list.filter(gen__subtribe=subtribe)
        elif tribe:
            otgenus_list = otgenus_list.filter(tribe=tribe)
        elif subfamily:
            otgenus_list = otgenus_list.filter(subfamily=subfamily)
        elif family:
            otgenus_list = otgenus_list.filter(family=family)
        otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'source', 'status')

        genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)

        # Synonyms
        otgensyn_list = OtGensyn.objects.filter(Q(pid__genus__icontains=keyword) | Q(pid__abrev=abrev))
        if family: otgensyn_list = otgensyn_list.filter(pid__family=family)

        orgensyn_list = OrGensyn.objects.filter(pid__genus__icontains=keyword)
        if family: orgensyn_list = orgensyn_list.filter(pid__family=family)

        cagensyn_list = CaGensyn.objects.filter(Q(pid__genus__icontains=keyword) | Q(pid__abrev=abrev))
        if family: cagensyn_list = cagensyn_list.filter(pid__family=family)

        brgensyn_list = BrGensyn.objects.filter(Q(pid__genus__icontains=keyword) | Q(pid__abrev=abrev))
        if family: brgensyn_list = brgensyn_list.filter(pid__family=family)

        if orgensyn_list:
            gensyn_list = orgensyn_list
        if cagensyn_list:
            gensyn_list.union(cagensyn_list)
        if brgensyn_list:
            gensyn_list.union(brgensyn_list)
        if otgensyn_list:
            gensyn_list.union(otgensyn_list)

        # gensyn_list = otgensyn_list.union(orgensyn_list).union(cagensyn_list).union(brgensyn_list)
    write_output(request, keyword)
    context = {'genus_list': genus_list, 'gensyn_list': gensyn_list, 'keyword': keyword, 'family_list': family_list,
               'title': 'search', 'role': role,
               'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               }
    return django.shortcuts.render(request, "common/search_genus.html", context)

# @login_required
def xsearch_species(request):
    # from itertools import chain
    spckeyword = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    species_list = []
    family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)

    CaSpecies = apps.get_model('cactaceae', 'Species')
    OrSpecies = apps.get_model('orchidaceae', 'Species')
    OtSpecies = apps.get_model('other', 'Species')
    BrSpecies = apps.get_model('bromeliaceae', 'Species')

    role = getRole(request)
    genus_list = []
    # No space allowed in genera keyword
    if 'family' in request.GET:
        family = request.GET['family'].strip()
    if family:
        family = Family.objects.get(family=family)

    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)

    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(subfamily=tribe)

    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].subtribe()
    if subtribe:
        subtribe = Subtribe.objects.get(subfamily=subtribe)

    if 'spckeyword' in request.GET:
        spckeyword = request.GET['spckeyword'].strip()
    if spckeyword:
        abrev = spckeyword
        abrev.replace('.','')

        # # CASE 1: First word is genus

        caspecies_list = CaSpecies.objects.filter(binomial__icontains=spckeyword)
        if subtribe:
            caspecies_list = caspecies_list.filter(gen__subtribe=subtribe)
        elif tribe:
            caspecies_list = caspecies_list.filter(gen__tribe=tribe)
        elif subfamily:
            caspecies_list = caspecies_list.filter(gen__subfamily=subfamily)
        elif family:
            caspecies_list = caspecies_list.filter(gen__family=family)
        caspecies_list = caspecies_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')

        orspecies_list = OrSpecies.objects.filter(binomial__icontains=spckeyword)
        if subtribe:
            orspecies_list = orspecies_list.filter(gen__subtribe=subtribe)
        elif tribe:
            orspecies_list = orspecies_list.filter(gen__tribe=tribe)
        elif subfamily:
            orspecies_list = orspecies_list.filter(gen__subfamily=subfamily)
        elif family:
            orspecies_list = orspecies_list.filter(gen__family=family)
        orspecies_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')

        otspecies_list = OtSpecies.objects.filter(binomial__icontains=spckeyword)
        if subtribe:
            otspecies_list = otspecies_list.filter(gen__subtribe=subtribe)
        elif tribe:
            otspecies_list = otspecies_list.filter(gen__tribe=tribe)
        elif subfamily:
            otspecies_list = otspecies_list.filter(gen__subfamily=subfamily)
        elif family:
            otspecies_list = otspecies_list.filter(gen__family=family)
        otspecies_list = otspecies_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')

        brspecies_list = BrSpecies.objects.filter(binomial__icontains=spckeyword)
        if subtribe:
            brspecies_list = brspecies_list.filter(gen__subtribe=subtribe)
        elif tribe:
            brspecies_list = brspecies_list.filter(gen__tribe=tribe)
        elif subfamily:
            brspecies_list = brspecies_list.filter(gen__subfamily=subfamily)
        elif family:
            brspecies_list = brspecies_list.filter(gen__family=family)
        brspecies_list = brspecies_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')

        species_list = caspecies_list.union(orspecies_list).union(otspecies_list).union(brspecies_list)

    # gencount = len(genus_list)
    # write_output(request, str(family))
    write_output(request, spckeyword)
    context = {'species_list': species_list, 'spckeyword': spckeyword, 'family_list': family_list,
               'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'title': 'search', 'role': role, }
    return django.shortcuts.render(request, "common/search_species.html", context)

def xreidentify(request, orid, pid):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm = getForms(request)
    species = Species.objects.get(pk=pid)
    source_file_name = ''
    role = getRole(request)
    if role != 'cur':
        url = "%s?role=%s" % (reverse('detail:photos', args=(pid,)), role)
        return HttpResponseRedirect(url)

    old_species = Species.objects.get(pk=pid)
    if old_species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        old_species = Species.objects.get(pk=pid)

    form = SpeciesForm(request.POST or None)
    if old_species.type == 'hybrid' and family == 'Orchidaceae':
        old_img = HybImages.objects.get(pk=orid)
    else:
        old_img = SpcImages.objects.get(pk=orid)

    if request.method == 'POST':
        if form.is_valid():
            new_pid = form.cleaned_data.get('species')
            try:
                new_species = Species.objects.get(pk=new_pid)
            except Species.DoesNotExist:
                url = "%s?role=%s" % (reverse('detail:photos', args=(pid,)), role)
                return HttpResponseRedirect(url)

            # If re-idenbtified to same type
            if (family == 'Orchidaceae' and new_species.type == old_species.type) or new_species.genus == new_species.genus:
                if new_species.type == 'species' or family != 'Orchidaceae':
                    if new_species.status == 'synonym':
                        accid = new_species.getAcc()
                        new_species = Species.objects.get(pk=accid)
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
                # Must move image file
                if old_img.image_file:
                    if new_species.type == 'species' or family != 'Orchidaceae':
                        new_img = SpcImages(pid=new_species)
                        from_path = "/webapps/static/utils/images/hybrid/" + old_img.image_file
                        to_path = "/webapps/static/utils/images/species/" + old_img.image_file
                    else:
                        new_img = HybImages(pid=new_species.hybrid)
                        from_path = "/webapps/static/" + old_image_dir + old_img.image_file
                        to_path = "/webapps/static/utils/images/hybrid/" + old_img.image_file
                    if family == 'Orchidaceae':
                        hist = ReidentifyHistory(from_id=old_img.id, from_pid=old_species, to_pid=new_species,
                                             user_id=request.user, created_date=old_img.created_date)
                    os.rename(from_path, to_path)
                else:
                    url = "%s?role=%s" % (reverse('detail:photos', args=(new_species.pid,)), role)
                    return HttpResponseRedirect(url)
                if source_file_name:
                    new_img.source_file_name = source_file_name
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
    context = {'form': form, 'species': old_species, 'img': old_img, 'role': 'cur', }
    return render(request, 'common/reidentify.html', context)

def xtaxonomy(request):
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    sf = ''
    t = ''
    st = ''
    specieslist = []
    hybridlist = []
    intragen_list = []
    family_list = Family.objects.all()
    subfamily_list = Subfamily.objects.all()
    tribe_list = Tribe.objects.all()
    subtribe_list = Subtribe.objects.all()
    genus_list = Genus.objects.all()
    if f:
        subfamily_list = subfamily_list.filter(family=f)
        tribe_list = tribe_list.filter(family=f)
        subtribe_list = subtribe_list.filter(family=f)
        # if f in app_list':
        genus_list = genus_list.filter(family=f)
        # else:
        #     genus_list = genus_list.filter(family=f)

    if 'sf' in request.GET:
        sf = request.GET['sf']
    if sf:
        tribe_list = tribe_list.filter(subfamily=sf)
        subtribe_list = subtribe_list.filter(subfamily=sf)
        genus_list = genus_list.filter(subfamily=sf)

    if 't' in request.GET:
        t = request.GET['t']
    if t:
        subtribe_list = subtribe_list.filter(tribe=t)
        genus_list = genus_list.filter(tribe=t)

    if 'st' in request.GET:
        st = request.GET['st']
        genus_list = genus_list.filter(subtribe=st)
    subfamily_list = subfamily_list.order_by('family', 'subfamily')
    tribe_list = tribe_list.order_by('subfamily', 'tribe')
    subtribe_list = subtribe_list.order_by('tribe', 'subtribe')
    genus_list = genus_list.order_by('genus')

    # genus_list = Genus.objects.filter(cit_status__isnull=True).exclude(cit_status__exact='').order_by('genus')

    role = getRole(request)

    if 'genus' in request.GET:
        genus = request.GET['genus']
        if genus:
            try:
                genus = Genus.objects.get(genus=genus)
            except Genus.DoesNotExist:
                genus = ''
    else:
        genus = ''

    if genus:
        # new genus has been selected. Now select new species/hybrid
        specieslist = Species.objects.filter(gen=genus.pid).filter(type='species').filter(
                cit_status__isnull=True).exclude(cit_status__exact='').order_by('species', 'infraspe', 'infraspr')

        hybridlist = Species.objects.filter(gen=genus.pid).filter(type='hybrid').order_by('species')

        # Construct intragen list
        if genus.type == 'hybrid':
            parents = GenusRelation.objects.get(gen=genus.pid)
            if parents:
                parents = parents.parentlist.split('|')
                intragen_list = Genus.objects.filter(pid__in=parents)
        else:
            intragen_list = Genus.objects.filter(description__icontains=genus).filter(type='hybrid').filter(
                num_hybrid__gt=0)

    write_output(request, str(genus))
    context = {
        'genus': genus, 'genus_list': genus_list, 'species_list': specieslist, 'hybrid_list': hybridlist,
        'intragen_list': intragen_list, 'f': f, 'sf': sf, 't': t, 'st': st,
        'family_list': family_list, 'subfamily_list': subfamily_list, 'tribe_list': tribe_list,
        'subtribe_list': subtribe_list, 'title': 'find_orchid', 'role': role,
        'home_link': '/', 'title': 'OrchidRoots Home',
    }
    return render(request, "common/taxonomy.html", context)

def xadvanced(request):
    f, sf, t, st = '', '', '', ''
    if 'f' in request.GET:
        f = request.GET['f']
    else:
        f = 'Orchidaceae'
    family = f
    if f not in app_list:
        f = 'other'
    Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)

    specieslist = []
    hybridlist = []
    intragen_list = []
    family_list = Family.objects.all()
    subfamily_list = Subfamily.objects.all()
    tribe_list = Tribe.objects.all()
    subtribe_list = Subtribe.objects.all()
    genus_list = Genus.objects.all()
    if f:
        subfamily_list = subfamily_list.filter(family=f)
        tribe_list = tribe_list.filter(family=f)
        subtribe_list = subtribe_list.filter(family=f)
        # if f in app_list':
        genus_list = genus_list.filter(family=f)
        # else:
        #     genus_list = genus_list.filter(family=f)

    if 'sf' in request.GET:
        sf = request.GET['sf']
    if sf:
        tribe_list = tribe_list.filter(subfamily=sf)
        subtribe_list = subtribe_list.filter(subfamily=sf)
        genus_list = genus_list.filter(subfamily=sf)

    if 't' in request.GET:
        t = request.GET['t']
    if t:
        subtribe_list = subtribe_list.filter(tribe=t)
        genus_list = genus_list.filter(tribe=t)

    if 'st' in request.GET:
        st = request.GET['st']
        genus_list = genus_list.filter(subtribe=st)
    subfamily_list = subfamily_list.order_by('family', 'subfamily')
    tribe_list = tribe_list.order_by('subfamily', 'tribe')
    subtribe_list = subtribe_list.order_by('tribe', 'subtribe')
    genus_list = genus_list.order_by('genus')

    # genus_list = Genus.objects.filter(cit_status__isnull=True).exclude(cit_status__exact='').order_by('genus')

    role = getRole(request)

    if 'genus' in request.GET:
        genus = request.GET['genus']
        if genus:
            try:
                genus = Genus.objects.get(genus=genus)
            except Genus.DoesNotExist:
                genus = ''
    else:
        genus = ''

    if genus:
        # new genus has been selected. Now select new species/hybrid
        specieslist = Species.objects.filter(gen=genus.pid).filter(type='species').filter(
                cit_status__isnull=True).exclude(cit_status__exact='').order_by('species', 'infraspe', 'infraspr')

        hybridlist = Species.objects.filter(gen=genus.pid).filter(type='hybrid').order_by('species')

        # Construct intragen list
        if genus.type == 'hybrid':
            parents = GenusRelation.objects.get(gen=genus.pid)
            if parents:
                parents = parents.parentlist.split('|')
                intragen_list = Genus.objects.filter(pid__in=parents)
        else:
            intragen_list = Genus.objects.filter(description__icontains=genus).filter(type='hybrid').filter(
                num_hybrid__gt=0)

    write_output(request, str(genus))
    context = {
        'genus': genus, 'genus_list': genus_list, 'species_list': specieslist, 'hybrid_list': hybridlist,
        'intragen_list': intragen_list, 'f': f, 'sf': sf, 't': t, 'st': st,  'family': family,
        'family_list': family_list, 'subfamily_list': subfamily_list, 'tribe_list': tribe_list,
        'subtribe_list': subtribe_list, 'title': 'find_orchid', 'role': role,
    }
    return render(request, "common/advanced.html", context)

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

