from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.apps import apps
from itertools import chain
from fuzzywuzzy import fuzz, process
from utils import conf_orchidaceae
from utils import config
# from myproject import config
import logging
import random
import string
import re
from .forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, \
    SpeciesForm, RenameSpeciesForm

# import django.shortcuts
from utils.views import write_output
from utils.views import getRole
from utils.views import get_random_img, imgdir

from .models import Genus, GenusRelation, Intragen, Species, Hybrid, Accepted, Synonym, \
    Subgenus, Section, Subsection, Series, \
    Distribution, SpcImages, HybImages, UploadFile, AncestorDescendant

alpha_list = config.alpha_list
logger = logging.getLogger(__name__)

User = get_user_model()
Family = apps.get_model('core', 'Family')
Subfamily = apps.get_model('core', 'Subfamily')
Tribe = apps.get_model('core', 'Tribe')
Subtribe = apps.get_model('core', 'Subtribe')

Region = apps.get_model('core', 'Region')
Subregion = apps.get_model('core', 'Subregion')
Localregion = apps.get_model('core', 'Localregion')
imgdir, hybdir, spcdir = imgdir()


def information(request, pid):
    role = getRole(request)
    species = Species.objects.get(pk=pid)
    family = species.gen.family
    send_url = '/display/information/' + str(pid) + '/?family=' + str(family) + '&role=' + role
    # print(send_url)
    return HttpResponseRedirect(send_url)


def photos(request, pid):
    role = getRole(request)
    species = Species.objects.get(pk=pid)
    family = species.gen.family
    send_url = '/detail/photos/' + str(pid) + '?family=' + str(family)
    # print(send_url)
    return HttpResponseRedirect(send_url)


@login_required
def reidentify(request, orid, pid):
    role = getRole(request)
    species = Species.objects.get(pk=pid)
    family = species.gen.family
    send_url = '/detail/reidentify/' + str(orid) + "/" + str(pid) + '?family=' + str(family)
    # print(send_url)
    return HttpResponseRedirect(send_url)


@login_required
def uploadfile(request, pid):
    role = getRole(request)
    species = Species.objects.get(pk=pid)
    family = species.gen.family
    send_url = '/detail/uploadfile/' + str(pid) + '?family=' + str(family)
    # print(send_url)
    return HttpResponseRedirect(send_url)


@login_required
def uploadweb(request, pid, orid=None):
    role = getRole(request)
    species = Species.objects.get(pk=pid)
    family = species.gen.family
    if orid:
        send_url = '/detail/uploadweb/' + str(pid) + '/' + str(orid) + '?family=' + str(family)
    else:
        send_url = '/detail/uploadweb/' + str(pid) + '?family=' + str(family)
    # print(send_url)
    return HttpResponseRedirect(send_url)


@login_required
def curateinfohyb(request, pid=None):
    if pid:
        send_url = '/detail/curateinfohyb/' + str(pid) + '/?family=Orchidaceae'
    else:
        send_url = '/detail/curateinfohyb/?family=Orchidaceae'
    return HttpResponseRedirect(send_url)


@login_required
def curateinfospc(request, pid):
    send_url = '/detail/curateinfospc/' + str(pid) + '?family=Orchidaceae'
    return HttpResponseRedirect(send_url)


def compare(request, pid):
    send_url = '/detail/compare/' + str(pid) + '?family=Orchidaceae'
    return HttpResponseRedirect(send_url)


@login_required
def createhybrid(request, pid):
    send_url = '/detail/createhybrid/' + str(pid) + '?family=Orchidaceae'
    return HttpResponseRedirect(send_url)


@login_required
def genera(request):
    family = 'Orchidaceae'
    min_lengenus_req = 2
    year = ''
    genustype = ''
    formula1 = ''
    formula2 = ''
    status = ''
    sort = ''
    prev_sort = ''
    sf_obj = ''
    t = ''
    t_obj = ''
    st_obj = ''
    role = getRole(request)
    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']

    if 'sf' in request.GET:
        sf = request.GET['sf']
        if sf:
            sf_obj = Subfamily.objects.get(pk=sf)
    if 't' in request.GET:
        t = request.GET['t']
        if t:
            try:
                t_obj = Tribe.objects.get(pk=t)
            except Tribe.DoesNotExist:
                pass
            if not sf_obj:
                try:
                    sf_obj = Subfamily.objects.get(pk=t_obj.subfamily)       # back fill subfamily
                except Subfamily.DoesNotExist:
                    pass
    if 'st' in request.GET:
        st = request.GET['st']
        if st:
            try:
                st_obj = Subtribe.objects.get(pk=st)
            except Subtribe.DoesNotExist:
                pass
            if st_obj:
                if not t:
                    try:
                        t_obj = Tribe.objects.get(pk=st_obj.tribe.tribe)
                    except Tribe.DoesNotExist:
                        pass
                if not sf_obj and st_obj.subfamily:
                    try:
                        sf_obj = Subfamily.objects.get(pk=st_obj.subfamily)
                    except Subtribe.DoesNotExist:
                        pass

    # Remove genus choide if subfamily, tribe or subtribe is chosen

    if 'genustype' in request.GET:
        genustype = request.GET['genustype']
    if not genustype:
        genustype = 'all'

    if 'formula1' in request.GET:
        formula1 = request.GET['formula1']
    if 'formula2' in request.GET:
        formula2 = request.GET['formula2']

    if 'status' in request.GET:
        status = request.GET['status']

    genus_list = Genus.objects.all()

    if status == 'synonym':
        genus_list = genus_list.filter(status='synonym')

    elif genustype == 'hybrid':
        genus_list = genus_list.filter(type='hybrid').exclude(status='synonym')
        if formula1 != '' or formula2 != '':
            genus_list = genus_list.filter(description__icontains=formula1).filter(description__icontains=formula2)
    elif genustype == 'species':
        # If an intrageneric is chosen, start from beginning.
        genus_list = genus_list.filter(type='species').exclude(status='synonym')
        if sf_obj or t_obj or st_obj:
            if sf_obj and t_obj and st_obj:
                genus_list = genus_list.filter(subfamily=sf_obj.subfamily).filter(
                    tribe=t_obj.tribe).filter(subtribe=st_obj.subtribe)
            elif sf_obj and t_obj and not st_obj:
                genus_list = genus_list.filter(subfamily=sf_obj.subfamily).filter(tribe=t_obj.tribe)
            elif sf_obj and st_obj and not t_obj:
                genus_list = genus_list.filter(subfamily=sf_obj.subfamily).filter(subtribe=st_obj.subtribe)
            elif sf_obj and not st_obj and not t_obj:
                genus_list = genus_list.filter(subfamily=sf_obj.subfamily)
            elif t_obj and st_obj and not sf_obj:
                genus_list = genus_list.filter(tribe=t_obj.tribe).filter(st=st_obj.subtribe)
            elif t_obj and not st_obj and not sf_obj:
                genus_list = genus_list.filter(tribe=t_obj.tribe)
            elif st_obj and not t_obj and not sf_obj:
                genus_list = genus_list.filter(subtribe=st_obj.subtribe)

    if alpha and len(alpha) == 1:
        genus_list = genus_list.filter(genus__istartswith=alpha)

    total = genus_list.count()

    # Get Alliances
    sf_list = Subfamily.objects.filter(family=family).filter(num_genus__gt=0)

    t_list = Tribe.objects.all()
    if sf_obj:
        t_list = t_list.filter(subfamily=sf_obj.subfamily)

    st_list = Subtribe.objects.all()
    if t_obj:
        st_list = st_list.filter(tribe=t_obj.tribe)
    elif sf_obj:
        st_list = st_list.filter(subfamily=sf_obj.subfamily)

    sf_list = sf_list.order_by('subfamily')
    t_list = t_list.order_by('tribe')
    st_list = st_list.order_by('subtribe')
    genus_lookup = Genus.objects.filter(pid__gt=0).filter(type='species')
    context = {'my_list': genus_list, 'total': total, 'genus_lookup': genus_lookup, 'family':family,
               'sf_obj': sf_obj, 'sf_list': sf_list, 't_obj': t_obj, 't_list': t_list,
               'st_obj': st_obj, 'st_list': st_list,
               'title': 'taxonomy', 'genustype': genustype, 'status': status,
               'formula1': formula1, 'formula2': formula2, 'alpha': alpha, 'alpha_list': alpha_list,
               'sort': sort, 'prev_sort': prev_sort, 'role': role,
               }
    write_output(request)
    return render(request, 'orchidaceae/genera.html', context)


def subgenus(request):
    # -- List Genuses
    subgenus_list = Subgenus.objects.order_by('subgenus')
    context = {'subgenus_list': subgenus_list, 'title': 'subgenus', }
    return render(request, 'orchidaceae/subgenus.html', context)


def section(request):
    # -- List Genuses
    section_list = Section.objects.order_by('section')
    context = {'section_list': section_list, 'title': 'section', }
    return render(request, 'orchidaceae/section.html', context)


def subsection(request):
    # -- List Genuses
    subsection_list = Subsection.objects.order_by('subsection')
    context = {'subsection_list': subsection_list, 'title': 'subsection', }
    return render(request, 'orchidaceae/subsection.html', context)


def series(request):
    # -- List Genuses
    series_list = Series.objects.order_by('series')
    context = {'series_list': series_list, 'title': 'series', }
    return render(request, 'orchidaceae/series.html', context)


def getPartialPid(reqgenus, type, status):
    pid_list = []
    # logger.error(">>00. reqgenus = " + str(reqgenus))
    intragen_list = Intragen.objects.all()
    if status == 'synonym' or type == 'hybrid':
        intragen_list = []
    pid_list = Species.objects.filter(type=type)
    if status == 'synonym':
        pid_list = pid_list.filter(status='synonym')
    elif status == 'accepted':
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
            else:
                pid_list = []
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
        # logger.error(">>01. reqgenus = " + str(reqgenus))
        return reqgenus, pid_list, intragen_list
    else:
        return '', pid_list, intragen_list


def getPrev(request,arg, prev):
    if arg in request.GET:
        arg = request.GET[arg]
    else:
        arg = ''
    if prev in request.GET:
        prev = request.GET[prev]
    else:
        prev = ''
    return arg, prev


@login_required
def species(request):
    role = getRole(request)
    family = ''
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
    elif 'family' in request.GET:
        family = request.GET['family']
    if family != 'Orchidaceae':
        send_url = '/common/species/?family=' + str(family) + '&role=' + role
        # print(send_url)
        return HttpResponseRedirect(send_url)

    family = Family.objects.get(pk='Orchidaceae')
    spc = reqgenus = ''
    msg = ''
    type = 'species'
    alpha = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    subfamily_list = []
    tribe_list = []
    subtribe_list = []
    subfamily_obj = ''
    tribe_obj = ''
    subtribe_obj = ''
    syn = ''
    genus = ''
    this_species_list = []
    total = 0
    # max_page_length = 1000

    # Initialize
    if 'genus' in request.GET:
        reqgenus = request.GET['genus']
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
    if 'syn' in request.GET:
        syn = request.GET['syn']

    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily']

    if subfamily:
        subfamily_obj = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe']
        if tribe:
            tribe_obj = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe']
        if subtribe:
            tribe_obj = Subtribe.objects.get(subtribe=subtribe)

    if alpha != 'ALL':
        alpha = alpha[0: 1]

    # initialize subfamily, tribe subtribe
    # Get list of affected  genus
    genus_list = Genus.objects.all()

    # Start building th elist
    if reqgenus or alpha or subfamily or tribe or subtribe:
        genus, this_species_list, intragen_list = getPartialPid(reqgenus, type, '')
        # if not subfamily and not reqgenus:
        #     subfamily = 'Epidendroideae'
        if subfamily:
            genus_list = genus_list.filter(subfamily=subfamily)
        if tribe:
            genus_list = genus_list.filter(tribe=tribe)
        if subtribe:
            genus_list = genus_list.filter(subtribe=subtribe)
        genus_list = genus_list.values_list('pid',flat=True)

        # logger.error(">>> 1 this species list = " + str(len(this_species_list)))
        if syn == 'N':
            this_species_list = this_species_list.exclude(status='synonym')
        else:
            syn = 'Y'
        # logger.error(">>> 1 this species list = " + str(len(this_species_list)))
        if this_species_list:
            this_species_list = this_species_list.filter(gen__in=genus_list)
            if alpha:
                if len(alpha) == 1:
                    this_species_list = this_species_list.filter(species__istartswith=alpha)

            total = len(this_species_list)

            if total > 5000:
                msg = 'Your search request generated over 5000 names. Please refine your search criteria.'
                this_species_list = this_species_list[0:5000]
                total = 5000

    subfamily_list = Subfamily.objects.filter(family=family).filter(num_genus__gt=0).order_by('subfamily')
    if subfamily_obj:
        tribe_list = Tribe.objects.filter(subfamily=subfamily_obj.subfamily).order_by('tribe')
    if tribe_obj:
        subtribe_list = Subtribe.objects.filter(tribe=tribe_obj.tribe).order_by ('subtribe')
    elif subfamily_obj:
        subtribe_list = Subtribe.objects.filter(subfamily=subfamily_obj.subfamily).order_by ('subtribe')

    write_output(request, str(genus))
    context = {'page_list': this_species_list, 'alpha_list': alpha_list, 'alpha': alpha, 'spc': spc,
               'role': role, 'total': total, 'family': family, 'genus': genus,
               'subfamily': subfamily, 'subfamily_list': subfamily_list,
               'tribe': tribe, 'tribe_list': tribe_list,
               'subtribe': subtribe, 'subtribe_list': subtribe_list,
               'msg': msg,
               'syn': syn,
               'title': 'taxonomy', 'type': 'species'
               }
    return render(request, 'orchidaceae/species.html', context)


@login_required
def hybrid(request):
    role = getRole(request)
    family = ''
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
    elif 'family' in request.GET:
        family = request.GET['family']
    # logger.error(">>> 1 Family = " + str(family))
    if family != 'Orchidaceae':
        send_url = '/common/hybrid/?family=' + str(family) + '&role=' + role
        # print(send_url)
        return HttpResponseRedirect(send_url)

    type = 'hybrid'
    family = Family.objects.get(family='Orchidaceae')
    year = ''
    year_valid = 0
    author = originator = ''
    seed, pollen = '', ''
    # reqgenus = ''
    msg = ''
    syn = ''
    spc = ''
    total = 0
    this_species_list = []
    # Initialization
    if 'spc' in request.GET:
        spc = request.GET['spc']
    if 'seed' in request.GET:
        seed = request.GET['seed']
    if 'pollen' in request.GET:
        pollen = request.GET['pollen']
    seed_genus, prev_seed_genus = getPrev(request, 'seed_genus', 'prev_seed_genus')
    pollen_genus, prev_pollen_genus = getPrev(request, 'pollen_genus', 'prev_pollen_genus')
    if 'syn' in request.GET:
        syn = request.GET['syn']
    if 'author' in request.GET:
        author = request.GET['author']
    if 'originator' in request.GET:
        originator = request.GET['originator']
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
    else:
        alpha = ''
    if alpha != 'ALL':
        alpha = alpha[0:1]
    if 'year' in request.GET:
        year = request.GET['year']
        if valid_year(year):
            year_valid = 1

    # if alpha or seed_genus or pollen_genus or seed or pollen:
    reqgenus, prev_genus = getPrev(request,'genus', 'prev_genus')

    if reqgenus or spc or seed or pollen or seed_genus or pollen_genus or year or author or originator or alpha:
        genus, this_species_list, intragen_list = getPartialPid(reqgenus, 'hybrid', '')

        if syn == 'N':
            this_species_list = this_species_list.exclude(status='synonym')
        else:
            syn = 'Y'
        if spc:
            this_species_list = this_species_list.filter(species__icontains=spc)

        if (reqgenus == prev_genus):

            if seed_genus and pollen_genus:
                this_species_list = this_species_list.filter(
                    Q(hybrid__seed_genus=seed_genus) & Q(hybrid__pollen_genus=pollen_genus) | Q(
                        hybrid__seed_genus=pollen_genus) & Q(hybrid__pollen_genus=seed_genus))
            elif seed_genus:
                this_species_list = this_species_list.filter(
                    Q(hybrid__seed_genus=seed_genus) | Q(hybrid__pollen_genus=seed_genus))
            elif pollen_genus:
                this_species_list = this_species_list.filter(Q(hybrid__seed_genus=pollen_genus)
                                                             | Q(hybrid__pollen_genus=pollen_genus))
            if seed:
                this_species_list = this_species_list.filter(Q(hybrid__seed_species__icontains=seed)
                                                             | Q(hybrid__pollen_species__icontains=seed))
            if pollen:
                this_species_list = this_species_list.filter(Q(hybrid__seed_species__icontains=pollen)
                                                             | Q(hybrid__pollen_species__icontains=pollen))

        # Building pid ;list

        if this_species_list:
            if alpha:
                if len(alpha) == 1:
                    this_species_list = this_species_list.filter(species__istartswith=alpha)
            if author and not originator:
                this_species_list = this_species_list.filter(author__icontains=author)
            if author and originator:
                this_species_list = this_species_list.filter(Q(author__icontains=author) | Q(originator__icontains=originator))
            if originator and not author:
                this_species_list = this_species_list.filter(originator__icontains=originator)
            if year_valid:
                year = int(year)
                this_species_list = this_species_list.filter(year=year)

            if this_species_list:
                total = len(this_species_list)
            else:
                total = 0
            if total > 5000:
                msg = 'Your search request generated over 5000 names. Please refine your search criteria.'
                this_species_list = this_species_list[0:5000]
                total = 5000

    genus_list = list(Genus.objects.exclude(status='synonym').values_list('genus', flat=True))
    genus_list.sort()
    write_output(request, str(reqgenus))
    context = {'my_list': this_species_list, 'genus_list': genus_list, 'family': family,
               'total': total, 'alpha_list': alpha_list, 'alpha': alpha,
               'genus': reqgenus, 'year': year, 'syn': syn,
               'author': author, 'originator': originator, 'seed': seed, 'pollen': pollen,
               'seed_genus': seed_genus, 'pollen_genus': pollen_genus,
               'role': role, 'title': 'taxonomy', 'msg': msg,
               }
    return render(request, 'orchidaceae/hybrid.html', context)


def browsedist(request):
    dist_list = get_distlist()
    context = {'dist_list': dist_list, }
    return render(request, 'orchidaceae/browsedist.html', context)


@login_required
def ancestor(request, pid=None):
    if not pid:
        if 'pid' in request.GET:
            pid = request.GET['pid']
            pid = int(pid)
        else:
            pid = 0

    role = getRole(request)
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
               'anc': 'active', 'tab': 'anc',
               'sort': sort, 'prev_sort': prev_sort,
               'title': 'ancestor', 'role': role, 'state': state,
               }
    write_output(request, species.textname())
    return render(request, 'orchidaceae/ancestor.html', context)


# All access - at least role = pub
@login_required
def ancestrytree(request, pid=None):
    if not pid:
        if 'pid' in request.GET:
            pid = request.GET['pid']
            pid = int(pid)
        else:
            pid = 0
    role = getRole(request)

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
               'spc': spc, 'tree': 'active', 'tab': 'tree',
               's': s, 'ss': ss, 'sp': sp, 'sss': sss, 'ssp': ssp, 'sps': sps, 'spp': spp,
               'ssss': ssss, 'sssp': sssp, 'ssps': ssps, 'sspp': sspp, 'spss': spss, 'spsp': spsp, 'spps': spps,
               'sppp': sppp,
               'p': p, 'ps': ps, 'pp': pp, 'pss': pss, 'psp': psp, 'pps': pps, 'ppp': ppp,
               'psss': psss, 'pssp': pssp, 'psps': psps, 'pspp': pspp, 'ppss': ppss, 'ppsp': ppsp, 'ppps': ppps,
               'pppp': pppp,
               'title': 'ancestrytree', 'role': role,
               }
    write_output(request, species.textname())
    return render(request, 'orchidaceae/ancestrytree.html', context)


# All access - at least role = pub
@login_required
def progeny_old(request, pid):
    alpha = ''
    direct = ''
    role = getRole(request)
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)


    if 'direct' in request.GET:
        direct = request.GET['direct']

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    genus = species.genus
    des_list = AncestorDescendant.objects.filter(aid=pid)
    if len(des_list) > 5000:
        des_list = des_list.filter(pct__gt=20)
    if direct:
        des_list = des_list.filter(Q(did__seed_id=pid) | Q(did__pollen_id=pid))
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL' or alpha == 'all':
            alpha = ''
        des_list = des_list.filter(did__pid__species__istartswith=alpha)

    total = des_list.count()

    write_output(request, species.textname())
    context = {'des_list': des_list, 'species': species, 'total': total, 'alpha': alpha, 'alpha_list': alpha_list,
                'tab': 'pro', 'pro': 'active', 'genus': genus, 'direct': direct,
               'title': 'progeny', 'section': 'Public Area', 'role': role,
               }
    return render(request, 'orchidaceae/progeny_old.html', context)

def progeny(request, pid):
    direct = ''
    role = getRole(request)
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)
    else:
        family = Family.objects.get(pk='Orchidaceae')

    if 'direct' in request.GET:
        direct = request.GET['direct']

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    genus = species.genus

    #All descendants
    des_list = AncestorDescendant.objects.filter(aid=pid)

    # primary
    prim_list = Hybrid.objects.filter(Q(seed_id=pid) | Q(pollen_id=pid)).values_list('pid', flat=True)
    # Secondary
    sec_list = Hybrid.objects.filter(Q(seed_id__in=prim_list) | Q(pollen_id__in=prim_list)).values_list('pid', flat=True)
    prim_list = set(prim_list)
    sec_list = set(sec_list)


    if len(des_list) > 5000:
        des_list = des_list.filter(pct__gt=40)

    result_list = []
    for x in des_list:
        if x.did.pid.pid in prim_list:
            result_list.append([x,'primary'])
        elif x.did.pid.pid in sec_list:
            result_list.append([x,'secondary'])
        else:
            result_list.append([x,''])

    # total = des_list.count()

    write_output(request, species.textname())
    context = {'result_list': result_list, 'species': species, 'family': family,
                'tab': 'pro', 'pro': 'active', 'genus': genus, 'direct': direct,
               'title': 'progeny', 'section': 'Public Area', 'role': role,
               }
    return render(request, 'orchidaceae/progeny.html', context)


# All access - at least role = pub
@login_required
def progenyimg(request, pid=None):
    num_show = 5
    page_length = 30
    role = getRole(request)
    if 'newfamily' in request.GET:
        family = request.GET['newfamily']
        url = "%s?role=%s&family=%s" % (reverse('common:genera'), role, family)
        return HttpResponseRedirect(url)

    if not pid:
        if 'pid' in request.GET:
            pid = request.GET['pid']
            pid = int(pid)
        else:
            pid = 0

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    genus = species.genus

    des_list = AncestorDescendant.objects.filter(aid=pid).filter(pct__gt=20)
    des_list = des_list.order_by('-pct')

    img_list = []
    for x in des_list:
        offspring = Hybrid.objects.get(pk=x.did.pid_id)
        y = x.did.pid.get_best_img()
        if y:
            y.name = offspring.pid.namecasual()
            y.pct = x.pct
            y.image_dir = y.image_dir()
            y.image_file = y.image_file
            y.author = y.author
            y.source_url = y.source_url
            y.pollen = offspring.pollen_id.pid
            y.seed = offspring.seed_id.pid
            y.seed_name = offspring.seed_id.namecasual()
            y.pollen_name = offspring.pollen_id.namecasual()
            img_list.append(y)

    total = len(img_list)
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
            request, img_list, page_length, num_show)

    write_output(request, species.textname())
    context = {'img_list': page_list, 'species': species, 'tab': 'proimg', 'proimg': 'active',
               'total': total,
               'num_show': num_show, 'first': first_item, 'last': last_item, 'role': role,
               'genus': genus, 'page': page,
               'page_range': page_range, 'last_page': last_page, 'next_page': next_page, 'prev_page': prev_page,
               'title': 'progenyimg', 'section': 'Public Area',
               }
    return render(request, 'orchidaceae/progenyimg.html', context)


def get_distlist():
    dist_list = Localregion.objects.exclude(id=0).order_by('continent_name', 'region_name', 'name')
    prevcon = ''
    prevreg = ''
    mydist_list = dist_list
    for x in mydist_list:
        x.concard = x.continent_name.replace(" ", "")
        x.regcard = x.region_name.replace(" ", "")
        x.prevcon = prevcon
        x.prevreg = prevreg
        # mydist_list.append([x, prevcon, prevreg,card] )
        prevcon = x.continent_name
        prevreg = x.region_name

    return mydist_list


def valid_year(year):
    if year and year.isdigit() and 1700 <= int(year) <= 2020:
        return year


# TOBE REMOVE
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


def xreidentify(request, orid, pid):
    source_file_name = ''
    role = getRole(request)
    old_species = Species.objects.get(pk=pid)
    old_family = old_species.gen.family
    if role != 'cur':
        url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(pid,)), role, old_family)
        return HttpResponseRedirect(url)

    if old_species.status == 'synonym':
        synonym = Synonym.objects.get(pk=pid)
        pid = synonym.acc_id
        old_species = Species.objects.get(pk=pid)

    form = SpeciesForm(request.POST or None)
    if old_species.type == 'species':
        old_img = SpcImages.objects.get(pk=orid)
    else:
        old_img = HybImages.objects.get(pk=orid)
    if request.method == 'POST':
        if form.is_valid():
            new_pid = form.cleaned_data.get('species')
            try:
                new_species = Species.objects.get(pk=new_pid)
            except Species.DoesNotExist:
                url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(pid,)), role, old_family)
                return HttpResponseRedirect(url)

            # If re-idenbtified to same genus. Just change pid
            if new_species.genus == old_species.genus:
                if old_species.type == 'species':
                    new_img = SpcImages.objects.get(pk=old_img.id)
                    new_img.pid = new_species.accepted
                else:
                    new_img = HybImages.objects.get(pk=old_img.id)
                    new_img.pid = new_species.hybris
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
                    url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(new_species.pid,)), role, new_family)
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

            # Delete old record
            # old_img.delete()

            # write_output(request, old_species.textname() + " ==> " + new_species.textname())
            url = "%s?role=%s&family=%s" % (reverse('display:photos', args=(new_species.pid,)), role, str(new_species.gen.family))
            return HttpResponseRedirect(url)
    context = {'form': form, 'species': old_species, 'img': old_img, 'role': 'cur', }
    return render(request, old_species.gen.family.application + '/reidentify.html', context)
