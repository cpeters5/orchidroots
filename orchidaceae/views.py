from django.shortcuts import render
from django.db import connection
from django.db.models import Q, Subquery
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.http import JsonResponse  # For datatable processing by page
from django.views.decorators.http import require_http_methods  # For datatable of large responses (hybrid and species view)
from django.urls import reverse, reverse_lazy
from django.apps import apps
# from django_mysql.models import SearchQuery   --- IMPORT ERROR!!

from urllib.parse import urlparse, urlencode
from itertools import chain
from fuzzywuzzy import fuzz, process
from utils import config
from utils.views import handle_bad_request, write_output, getRole, thumbdir, redirect_to_referrer
from collections import defaultdict
# from myproject import config
import logging
import random
import string
import re

from .models import Genus, GenusRelation, Intragen, Species, Hybrid, Accepted, Synonym, \
    Subgenus, Section, Subsection, Series, \
    Distribution, SpcImages, HybImages, UploadFile, AncestorDescendant

logger = logging.getLogger(__name__)
User = get_user_model()
Photographer = apps.get_model('accounts', 'Photographer')
Family = apps.get_model('common', 'Family')
Subfamily = apps.get_model('common', 'Subfamily')
Tribe = apps.get_model('common', 'Tribe')
Subtribe = apps.get_model('common', 'Subtribe')
Region = apps.get_model('common', 'Region')
Subregion = apps.get_model('common', 'Subregion')
Distribution = apps.get_model('orchidaceae', 'Distribution')

# Localregion = apps.get_model('common', 'Localregion')
imgdir, hybdir, spcdir = thumbdir()

alpha_list = config.alpha_list
app = 'orchidaceae'
family = 'Orchidaceae'

# orchidaceae application is specificly for Orchidaceae family only.

# List genera
@login_required
def genera(request):
    write_output(request)
    st_obj = ''
    role = getRole(request)
    alpha = request.GET.get('alpha', '')

    # Get subfamily, tribe, subtribe instance for genus_list filter
    # Get subfamily list
    sf = request.GET.get('sf', '')
    try:
        sf_obj = Subfamily.objects.get(pk=sf)
    except Subfamily.DoesNotExist:
        sf_obj = None

    # Get tribe instance
    t = request.GET.get('t', '')
    try:
        t_obj = Tribe.objects.get(pk=t)
        try:
            sf_obj = Subfamily.objects.get(pk=t_obj.subfamily)       # back fill subfamily
        except Subfamily.DoesNotExist:
            sf_obj = ''
    except Tribe.DoesNotExist:
        t_obj = ''

    # Get subtribe instance: A bit convoluted, because of incomplete data
    st = request.GET.get('st', '')
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
                    t_obj = ''
            if not sf_obj and st_obj.subfamily:
                try:
                    sf_obj = Subfamily.objects.get(pk=st_obj.subfamily)
                except Subtribe.DoesNotExist:
                    sf_obj = ''

    # subfamily, tribe or subtribe requests override genus request!
    genustype = request.GET.get('genustype', 'all')
    formula1 = request.GET.get('formula1', '')
    formula2 = request.GET.get('formula2', '')
    status = request.GET.get('status', '')

    # Build genus_list and apply filters
    genus_list = Genus.objects.all()
    if status == 'synonym':
        genus_list = genus_list.filter(status='synonym')
    elif genustype == 'hybrid':
        genus_list = genus_list.filter(type='hybrid').exclude(status='synonym')
        if formula1 != '' or formula2 != '':
            genus_list = genus_list.filter(Q(description__icontains=formula1) | Q(description__icontains=formula2))
    elif genustype == 'species':
        # If an intrageneric is chosen, start from beginning.
        genus_list = genus_list.filter(type='species').exclude(status='synonym')
        if sf_obj or t_obj or st_obj:
            if sf_obj and t_obj and st_obj:
                genus_list = genus_list.filter(subfamily=sf_obj.subfamily, tribe=t_obj.tribe, subtribe=st_obj.subtribe)
            elif sf_obj and t_obj and not st_obj:
                genus_list = genus_list.filter(subfamily=sf_obj.subfamily, tribe=t_obj.tribe)
            elif sf_obj and st_obj and not t_obj:
                genus_list = genus_list.filter(subfamily=sf_obj.subfamily, subtribe=st_obj.subtribe)
            elif sf_obj and not st_obj and not t_obj:
                genus_list = genus_list.filter(subfamily=sf_obj.subfamily)
            elif t_obj and st_obj and not sf_obj:
                genus_list = genus_list.filter(tribe=t_obj.tribe, stubtribe=st_obj.subtribe)
            elif t_obj and not st_obj and not sf_obj:
                genus_list = genus_list.filter(tribe=t_obj.tribe)
            elif st_obj and not t_obj and not sf_obj:
                genus_list = genus_list.filter(subtribe=st_obj.subtribe)

    if alpha and len(alpha) == 1:
        genus_list = genus_list.filter(genus__istartswith=alpha)

    # Get subfamily, tribe, subtribe list.  These will be shown in dropdown menu in the detail genus list page
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
    #   Genus lookuo list
    genus_lookup = Genus.objects.filter(pid__gt=0).filter(type='species')

    # Build canonical_url. Prefer crawlers to use the simpler version /common/genera"
    if alpha and alpha != 'All':
        canonical_url = request.build_absolute_uri(f'/common/genera/?app=orchidaceae&alpha={alpha}').replace('www.orchidroots.com', 'orchidroots.com')
    else:
        canonical_url = request.build_absolute_uri(f'/common/genera/?app=orchidaceae').replace('www.orchidroots.com', 'orchidroots.com')

    context = {'my_list': genus_list, 'genus_lookup': genus_lookup,
               'sf_obj': sf_obj, 'sf_list': sf_list, 't_obj': t_obj, 't_list': t_list,
               'st_obj': st_obj, 'st_list': st_list,
               'title': 'taxonomy', 'genustype': genustype, 'status': status,
               'formula1': formula1, 'formula2': formula2, 'alpha': alpha, 'alpha_list': alpha_list,
               'role': role, 'app': 'orchidaceae',
               'canonical_url': canonical_url,
               }
    return render(request, 'orchidaceae/genera.html', context)

# Works but not accessible
def subgenus(request):
    # -- List subgenus
    subgenus_list = Subgenus.objects.order_by('subgenus')
    context = {'subgenus_list': subgenus_list, 'title': 'subgenus',  'app': 'orchidaceae',}
    return render(request, 'orchidaceae/subgenus.html', context)


# Works but not accessible
def section(request):
    # -- List Genuses
    section_list = Section.objects.order_by('section')
    context = {'section_list': section_list, 'title': 'section', 'app': 'orchidaceae', }
    return render(request, 'orchidaceae/section.html', context)


# Works but not accessible
def subsection(request):
    # -- List Genuses
    subsection_list = Subsection.objects.order_by('subsection')
    context = {'subsection_list': subsection_list, 'title': 'subsection', 'app': 'orchidaceae', }
    return render(request, 'orchidaceae/subsection.html', context)


# Works but not accessible
def series(request):
    # -- List Genuses
    series_list = Series.objects.order_by('series')
    context = {'series_list': series_list, 'title': 'series', 'app': 'orchidaceae', }
    return render(request, 'orchidaceae/series.html', context)

# Get the list of matching genus along with related generaa
def getPartialPid(reqgenus, type, status):
    pid_list = []
    # logger.error(">>00. reqgenus = " + str(reqgenus))
    intragen_list = Intragen.objects.all()
    if status == 'synonym' or type == 'hybrid':
        intragen_list = []
    if status == 'synonym':
        pid_list = Species.objects.filter(type__iexact=type).filter(status='synonym')
    else:
        pid_list = Species.objects.filter(type__iexact=type)

    if reqgenus:
        if reqgenus[0] != '*' and reqgenus[-1] != '*':
            try:
                genus = Genus.objects.get(genus=reqgenus)
            except Genus.DoesNotExist:
                genus = ''
            if genus:
                pid_list = pid_list.filter(genus=reqgenus)
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

@login_required
def species(request):
    author = ''
    role = getRole(request)
    spc = request.GET.get('spc', '')
    syn = request.GET.get('syn', 'N')
    msg = ''
    type = 'species'
    alpha = ''
    subgenus_list, section_list, subsection_list, series_list = [], [], [], []
    genus = ''
    this_species_list = []
    # max_page_length = 1000

    # Initialize
    reqgenus = request.GET.get('genus', '')
    if not reqgenus:
        reqgenus = 'Cattleya'
    alpha = request.GET.get('alpha', '')
    # For big genera, forces alpha to A.
    if reqgenus in config.big_genera and not alpha:
        alpha = 'A'
    # if alpha == 'ALL':
    #     alpha = ''

    if alpha == '' and reqgenus in config.big_genera:
        alpha = 'A'

    subgenus = request.GET.get('subgenus', '')
    section = request.GET.get('section', '')
    subsection = request.GET.get('subsection', '')
    series = request.GET.get('series', '')

    # Start building th elist
    if reqgenus or alpha or spc or subgenus or section or subsection:
        genus, this_species_list, intragen_list = getPartialPid(reqgenus, type, '')
        write_output(request, str(genus))
        if this_species_list:
            if subgenus:
                this_species_list = this_species_list.filter(accepted__subgenus=subgenus)
            elif section:
                this_species_list = this_species_list.filter(accepted__section=section)
            elif subsection:
                this_species_list = this_species_list.filter(accepted__subsection=subsection)
            elif series:
                this_species_list = this_species_list.filter(accepted__series=series)
            if this_species_list:
                if syn == 'N':
                    this_species_list = this_species_list.exclude(status='synonym')
                if spc:
                    this_species_list = this_species_list.filter(species__istartswith=spc)
                elif alpha:
                    if len(alpha) == 1:
                        this_species_list = this_species_list.filter(species__istartswith=alpha)

    subgenus_list = Subgenus.objects.filter(genus=genus).order_by('subgenus')
    section_list = Section.objects.filter(genus=genus).order_by('section')
    subsection_list = Subsection.objects.filter(genus=genus).order_by ('subsection')
    series_list = Series.objects.filter(genus=genus).order_by ('subsection')

    canonical_url = request.build_absolute_uri(f'/orchidaceae/species/?genus={genus}').replace('www.orchidroots.com', 'orchidroots.com')

    context = {'page_list': this_species_list, 'alpha_list': alpha_list, 'alpha': alpha, 'spc': spc,
               'role': role, 'genus': genus,
               'subgenus': subgenus, 'subgenus_list': subgenus_list,
               'section': section, 'section_list': section_list,
               'subsection': subsection, 'subsection_list': subsection_list,
               'series': series, 'series_list': series_list,
               'msg': msg,
               'syn': syn,
               'title': 'taxonomy', 'type': 'species', 'app': 'orchidaceae',
               'canonical_url': canonical_url,
               }
    return render(request, 'orchidaceae/species.html', context)

@login_required
def hybrid(request):
    # Initialization
    author = request.GET.get('author', '')
    year_valid = 0
    msg = ''
    crit = 0
    if author: crit = 1
    originator = request.GET.get('originator', '')
    if originator: crit = 1
    alpha = request.GET.get('alpha', '')
    if alpha: crit = 1
    year = request.GET.get('year', '')
    if valid_year(year):
        year_valid = 1
        crit = 1
    if alpha != 'ALL':
        alpha = alpha[0:1]
    status = request.GET.get('status', '')
    spc = request.GET.get('spc', '')
    if spc:
        crit = 1
    if len(spc) == 1:
        alpha = spc
        spc = ''
    reqgenus = request.GET.get('genus', None)
    if not reqgenus:
        reqgenus = 'Cattleya'
    if alpha == '' and reqgenus in config.big_genera:
        alpha = 'A'

    prev_genus = request.GET.get('reqgenus', None)

    if reqgenus == None or reqgenus == '':
        # Sent from base.html in case no genus info, in which case randomize genus
        while 1:
            # Just get a random one with some images to show
            reqgenus = Genus.objects.filter(num_hyb_with_image__gt=100, num_hyb_with_image__lt=300).exclude(status='synonym').order_by('?')
            if reqgenus:
                reqgenus = reqgenus[0].genus
                break
        prev_genus = reqgenus
    # If there is no params requested, and for large tables, set alpha = A
    if not crit and reqgenus in config.big_genera:
        alpha = 'A'

    # user requests seed or pollen parents
    # First get seed_id object, then filter the hybrid list matching seed / pollen parent
    seed_binomial = request.GET.get('seed_binomial', '').strip()
    pollen_binomial = request.GET.get('pollen_binomial', '').strip()

    # Start building the list
    # First matching genus, with wild card
    crit = 1 #???
    if crit :
        reqgenus, this_species_list, intragen_list = getPartialPid(reqgenus, 'hybrid', status)
    else:
        # If crit = 0 (no filter criteria), ignore request
        return render(request, 'orchidaceae/hybrid.html', {})
    write_output(request, str(reqgenus))

    if crit and this_species_list:
        if spc:
            this_species_list = this_species_list.extra(where=["MATCH(species) AGAINST (%s IN NATURAL LANGUAGE MODE)"], params=[spc])
            # if len(spc) >= 2:
            #     this_species_list = this_species_list.filter(species__icontains=spc)
            # else:
            #     this_species_list = this_species_list.filter(species__istartswith=spc)

        elif alpha:
            if len(alpha) == 1:
                this_species_list = this_species_list.filter(species__istartswith=alpha)
        if author or originator:
            this_species_list = this_species_list.filter(author__icontains=author, originator__icontains=originator)
        if author and originator:
            this_species_list = this_species_list.filter(Q(author__icontains=author) | Q(originator__icontains=originator))
        # if originator and not author:
        #     this_species_list = this_species_list.filter(originator__icontains=originator)
        if year_valid:
            year = int(year)
            this_species_list = this_species_list.filter(year=year)
    else:
        this_species_list = []
        msg = "Please select a search criteria"
    role = getRole(request)
    context = {'my_list': this_species_list,
               'alpha_list': alpha_list, 'alpha': alpha, 'spc': spc,
               'genus': reqgenus, 'year': year, 'status': status, 'msg': msg,
               'author': author, 'originator': originator, 'seed_binomial': seed_binomial, 'pollen_binomial': pollen_binomial,
               'role': role, 'level': 'list', 'title': 'hybrid_list',  'app': 'orchidaceae',
               }
    return render(request, 'orchidaceae/hybrid.html', context)

@login_required
def ancestor(request, pid=None):
    if not pid:
        pid = request.GET.get('pid', '')
        if not pid or not str(pid).isnumeric():
            # Complete bonker! Send to home page
            return HttpResponseRedirect('/')
        else:
            canonical_url = request.build_absolute_uri(f'/orchidaceae/ancestor/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')
            # Redirect permanent to preferred url
            # Remove in a year or 2?
            return HttpResponsePermanentRedirect(canonical_url)

    role = getRole(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    write_output(request, species.binomial)
    genus = species.gen

    # List of ancestors in the left panel
    anc_list = AncestorDescendant.objects.filter(did=pid)
    canonical_url = request.build_absolute_uri(f'/orchidaceae/ancestor/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')

    context = {'species': species, 'anc_list': anc_list,
               'genus': genus,
               'lineage': 'active', 'tab': 'lineage', 'lineage': 'active',
               'title': 'ancestor', 'role': role, 'app': 'orchidaceae',
               'canonical_url': canonical_url,
               }
    return render(request, 'orchidaceae/ancestor.html', context)


def get_seed_parent(child):
    # child must be a Hybrid instance
    if not isinstance(child, Hybrid):
        return ''
    if child and child.seed_id and child.seed_id.type == 'species':
        # SS
        if child.seed_id.status == 'synonym':
            try:
                parent = Accepted.objects.get(pk=child.seed_id.getAcc())
            except Accepted.DoesNotExist:
                return ''
        else:
            try:
                parent = Accepted.objects.get(pk=child.seed_id)
            except Accepted.DoesNotExist:
                return ''
        parent.type = parent.pid.type
        parent.parent = 'seed'
        parent.year = parent.pid.year
        parent.img = parent.pid.speciesstat.best_image
    elif child.seed_id and child.seed_id.type == 'hybrid':
        if child.seed_id.status == 'synonym':
            try:
                parent = Hybrid.objects.get(pk=child.seed_id.getAcc())
            except Accepted.DoesNotExist:
                parent = ''
        else:
            try:
                parent = Hybrid.objects.get(pk=child.seed_id)
            except Hybrid.DoesNotExist:
                parent = ''
        parent = Hybrid.objects.get(pk=child.seed_id)
        parent.type = parent.pid.type
        parent.parent = 'seed'
        parent.year = parent.pid.year
        parent.img = parent.pid.speciesstat.best_image
    else:
        parent = ''
    return parent


def get_pollen_parent(child):
    # child must be a Hybrid instance
    if not isinstance(child, Hybrid):
        return ''
    if child and child.pollen_id and child.pollen_id.type == 'species':
        if child.pollen_id.status == 'synonym':
            try:
                parent = Accepted.objects.get(pk=child.pollen_id.getAcc())
            except Accepted.DoesNotExist:
                return ''
        else:
            try:
                parent = Accepted.objects.get(pk=child.pollen_id)
            except Accepted.DoesNotExist:
                return ''
        parent.type = parent.pid.type
        parent.parent = 'pollen'
        parent.year = parent.pid.year
        parent.img = parent.pid.speciesstat.best_image
    elif child.pollen_id and child.pollen_id.type == 'hybrid':
        if child.pollen_id.status == 'synonym':
            try:
                parent = Hybrid.objects.get(pk=child.pollen_id.getAcc())
            except Hybrid.DoesNotExist:
                return ''
        else:
            try:
                parent = Hybrid.objects.get(pk=child.pollen_id)
            except Hybrid.DoesNotExist:
                return ''
        parent.type = parent.pid.type
        parent.parent = 'pollen'
        parent.year = parent.pid.year
        parent.img = parent.pid.speciesstat.best_image
    else:
        parent = ''
    return parent

@login_required
def ancestrytree(request, pid=None):
    if not pid:
        pid = request.GET.get('pid', '')

    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    role = getRole(request)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    write_output(request, species.binomial)
    if species.status == 'synonym':
        species = species.getAccepted()

    s = p = ss = sp = ps = pp = sss = ssp = sps = spp = pss = psp = pps = ppp = None
    spc = ''
    if species.type == 'hybrid':
        hybrid = species.hybrid
        s = get_seed_parent(hybrid)
        p = get_pollen_parent(hybrid)
        ss = get_seed_parent(s)
        sp = get_pollen_parent(s)
        sss = get_seed_parent(ss)
        ssp = get_pollen_parent(ss)
        sps = get_seed_parent(sp)
        spp = get_pollen_parent(sp)
        ps = get_seed_parent(p)
        pp = get_pollen_parent(p)
        pss = get_seed_parent(ps)
        psp = get_pollen_parent(ps)
        pps = get_seed_parent(pp)
        ppp = get_pollen_parent(pp)
        species.img = species.speciesstat.best_image
    canonical_url = request.build_absolute_uri(f'/orchidaceae/ancestrytree/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')
    context = {'species': species,
               'spc': spc, 'tree': 'lineage', 'tab': 'lineage', 'lineage': 'active',
               's': s, 'ss': ss, 'sp': sp, 'sss': sss, 'ssp': ssp, 'sps': sps, 'spp': spp,
               'p': p, 'ps': ps, 'pp': pp, 'pss': pss, 'psp': psp, 'pps': pps, 'ppp': ppp,
               'title': 'ancestrytree', 'role': role, 'app': 'orchidaceae',
               'canonical_url': canonical_url,
               }
    return render(request, 'orchidaceae/ancestrytree.html', context)

from django.db import connection
from django.db.models import Subquery, OuterRef, Value, IntegerField, Q
from django.db.models.functions import Greatest


@login_required
def synonym(request, pid):
    role = getRole(request)

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

    canonical_url = request.build_absolute_uri(f'/orchidaceae/synonym/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')

    context = {'synonym_list': synonym_list, 'species': species,
               'tab': 'syn', 'syn': 'active', 'genus': genus,
               'role': role, 'app': 'orchidaceae',
               'canonical_url': canonical_url,
               }
    return render(request, 'orchidaceae/synonym.html', context)

@login_required
def progeny(request, pid):
    role = getRole(request)
    try:
        species = Species.objects.get(pk=pid)
        genus = species.genus
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    write_output(request, species.binomial)

    syn_list = Species.objects.filter(accid=pid).values_list('pid', flat=True)
    # Request immediate offsprings?
    prim = request.GET.get('prim', None)
    if prim:
        prim_list = Hybrid.objects.filter(
            Q(seed_id=pid) |
            Q(pollen_id=pid) |
            Q(seed_id__in=Subquery(syn_list)) |
            Q(pollen_id__in=Subquery(syn_list))
        )
        canonical_url = request.build_absolute_uri(f'/orchidaceae/progeny/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')
        context = {'prim_list': prim_list, 'species': species,
                   'tab': 'lineage', 'lineage': 'active', 'genus': genus,
                   'title': 'progeny', 'section': 'Public Area', 'role': role, 'app': 'orchidaceae',
                   'canonical_url': canonical_url,
                   }
        return render(request, 'orchidaceae/progeny_immediate.html', context)

    #Request all offsprings
    des_list =  list(AncestorDescendant.objects.filter(pct__gt=2, aid=pid))
    # Build canonical url
    canonical_url = request.build_absolute_uri(f'/orchidaceae/progeny/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')
    context = {'result_list': des_list, 'species': species,
                'tab': 'lineage', 'lineage': 'active', 'genus': genus,
               'title': 'progeny', 'section': 'Public Area', 'role': role, 'app': 'orchidaceae',
               'canonical_url': canonical_url,
               }

    return render(request, 'orchidaceae/progeny.html', context)

@login_required
def progenyimg(request, pid=None):
    num_show = 5
    page_length = 30
    min_pct = 30
    role = getRole(request)

    if not pid:
        pid = request.GET.get('pid', None)

    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    write_output(request, species.binomial)
    genus = species.genus
    des_list = AncestorDescendant.objects.filter(aid=pid).filter(pct__gt= min_pct)
    # des_list = des_list.order_by('-pct')

    img_list = []
    for x in des_list:
        if isinstance(x.did, Hybrid):
            try:
                offspring = Hybrid.objects.get(pk=x.did.pid_id)
            except Hybrid.DoesNotExist:
                offspring = ''
            y = x.did.pid.get_best_img()
            if y:
                y.name = offspring.pid.namecasual()
                y.pct = x.pct
                y.image_dir = y.image_dir()
                if offspring.pollen_id:
                    y.pollen = offspring.pollen_id.pid
                    y.pollen_name = offspring.pollen_id.namecasual()
                if offspring.seed_id:
                    y.seed = offspring.seed_id.pid
                    y.seed_name = offspring.seed_id.namecasual()
                img_list.append(y)

    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
            request, img_list, page_length, num_show)

    context = {'img_list': page_list, 'species': species, 'tab': 'lineage', 'lineage': 'active',
               'num_show': num_show, 'first': first_item, 'last': last_item, 'role': role,  'app': 'orchidaceae',
               'genus': genus, 'page': page,
               'page_range': page_range, 'last_page': last_page, 'next_page': next_page, 'prev_page': prev_page,
               'title': 'progenyimg', 'section': 'Public Area',
               }
    return render(request, 'orchidaceae/progenyimg.html', context)


@login_required
def distribution(request, pid):
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
               'title': 'distribution', 'app': 'orchidaceae',
               }
    write_output(request, species.binomial)
    return render(request, 'orchidaceae/distribution.html', context)


def valid_year(year):
    if year and year.isdigit() and 1700 <= int(year) <= 2020:
        return year


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


def infraspecific(request, pid):
    role = getRole(request)
    canonical_url = request.build_absolute_uri(f'/common/infraspecific/{app}/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')
    return HttpResponsePermanentRedirect(canonical_url)


