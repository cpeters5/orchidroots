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

# import django.shortcuts
from utils.views import write_output
from utils.views import getRole
from utils.views import get_random_img, thumbdir

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
Localregion = apps.get_model('common', 'Localregion')
imgdir, hybdir, spcdir = thumbdir()

alpha_list = config.alpha_list

@login_required
def genera(request):
    write_output(request)
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
    if status == 'synonym':
        pid_list = Species.objects.filter(type__iexact=type).filter(status='synonym')
    else:
        pid_list = Species.objects.filter(type__iexact=type).exclude(status='synonym')

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
    myspecies = ''
    author = ''
    max_rec = 3000
    role = getRole(request)
    family = ''
    if 'family' in request.GET:
        family = request.GET['family']
    if family != 'Orchidaceae':
        send_url = '/common/species/?family=' + str(family) + '&role=' + role
        return HttpResponseRedirect(send_url)

    family = Family.objects.get(pk='Orchidaceae')
    spc = reqgenus = ''
    msg = ''
    type = 'species'
    alpha = ''
    tribe_list = []
    subtribe_list = []
    subfamily_obj = ''
    tribe_obj = ''
    genus = ''
    this_species_list = []
    # max_page_length = 1000

    # Initialize
    reqgenus = request.GET.get('genus', '')
    if reqgenus == '':
        # Sent from base.html in case no genus info, in which case randomize genus
        while 1:
            reqgenus = Genus.objects.filter(num_spc_with_image__gt=100, num_spc_with_image__lt=300).exclude(status='synonym').order_by('?')
            if reqgenus:
                reqgenus = reqgenus[0].genus
                break

    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL':
            alpha = ''
    syn = request.GET.get('syn', '')

    subfamily = request.GET.get('subfamily', '')
    tribe = request.GET.get('tribe', '')
    subtribe = request.GET.get('subtribe', '')

    myspecies = request.GET.get('myspecies', '')
    if myspecies:
        try:
            author = Photographer.objects.get(user_id=request.user)
        except Photographer.DoesNotExist:
            author = ''

    # Get list of affected  genus
    genus_list = Genus.objects.all()

    # Start building th elist
    if reqgenus or alpha or subfamily or tribe or subtribe:
        genus, this_species_list, intragen_list = getPartialPid(reqgenus, type, '')
        write_output(request, str(genus))
        # if not subfamily and not reqgenus:
        #     subfamily = 'Epidendroideae'
        if subfamily:
            genus_list = genus_list.filter(subfamily=subfamily)
        if tribe:
            genus_list = genus_list.filter(tribe=tribe)
        if subtribe:
            genus_list = genus_list.filter(subtribe=subtribe)
        genus_list = genus_list.values_list('pid',flat=True)

        if syn == 'N':
            this_species_list = this_species_list.exclude(status='synonym')
        else:
            syn = 'Y'
        if this_species_list:
            this_species_list = this_species_list.filter(gen__in=genus_list)
            if alpha:
                if len(alpha) == 1:
                    this_species_list = this_species_list.filter(species__istartswith=alpha)
            if myspecies and author:
                pid_list = SpcImages.objects.filter(author_id=author).values_list('pid', flat=True).distinct()
                this_species_list = this_species_list.filter(pid__in=pid_list)

    subfamily_list = Subfamily.objects.filter(family=family).filter(num_genus__gt=0).order_by('subfamily')
    if subfamily:
        tribe_list = Tribe.objects.filter(subfamily=subfamily).order_by('tribe')
    if tribe:
        subtribe_list = Subtribe.objects.filter(tribe=tribe).order_by ('subtribe')
    elif subfamily:
        subtribe_list = Subtribe.objects.filter(subfamily=subfamily).order_by ('subtribe')

    context = {'page_list': this_species_list, 'alpha_list': alpha_list, 'alpha': alpha, 'spc': spc,
               'role': role, 'family': family, 'genus': genus,
               'subfamily': subfamily, 'subfamily_list': subfamily_list,
               'tribe': tribe, 'tribe_list': tribe_list,
               'subtribe': subtribe, 'subtribe_list': subtribe_list,
               'msg': msg,
               'syn': syn, 'myspecies': myspecies,
               'title': 'taxonomy', 'type': 'species'
               }
    return render(request, 'orchidaceae/species.html', context)


@login_required
def hybrid(request):
    year = ''
    year_valid = 0
    status = ''
    author = originator = ''
    seed_genus = ''
    pollen_genus = ''
    seed = pollen = ''
    spc = ''
    msg = ''

    # Initialization
    reqgenus = request.GET.get('genus', None)
    prev_genus = request.GET.get('reqgenus', None)
    if reqgenus == None or reqgenus == '':
        # Sent from base.html in case no genus info, in which case randomize genus
        while 1:
            reqgenus = Genus.objects.filter(num_hyb_with_image__gt=100, num_hyb_with_image__lt=300).exclude(status='synonym').order_by('?')
            if reqgenus:
                reqgenus = reqgenus[0].genus
                break
        prev_genus = reqgenus
    if 'seed' in request.GET:
        seed = request.GET['seed']
    if 'pollen' in request.GET:
        pollen = request.GET['pollen']
    if 'status' in request.GET:
        status = request.GET['status']
    if 'spc' in request.GET:
        spc = request.GET['spc']
        if spc:
            crit = 1
        if len(spc) == 1:
            alpha = ''

    if 'author' in request.GET:
        author = request.GET['author']
        if author: crit = 1
    if 'originator' in request.GET:
        originator = request.GET['originator']
        if originator: crit = 1
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha: crit = 1
    else:
        alpha = ''
    if 'year' in request.GET:
        year = request.GET['year']
        if valid_year(year):
            year_valid = 1
            crit = 1
    if alpha != 'ALL':
        alpha = alpha[0:1]
    crit = 1
    if crit :
        reqgenus, this_species_list, intragen_list = getPartialPid(reqgenus, 'hybrid', status)
    else:
        return render(request, 'orchidaceae/hybrid.html', {})
    write_output(request, str(reqgenus))

    if (reqgenus and (reqgenus == prev_genus)):
        seed_genus, prev_seed_genus = getPrev(request,'seed_genus', 'prev_seed_genus')
        pollen_genus, prev_pollen_genus = getPrev(request,'pollen_genus', 'prev_pollen_genus')

    if seed and seed_genus:
        this_species_list = this_species_list.filter(
            Q(hybrid__seed_genus__istartswith=seed_genus, hybrid__seed_species__istartswith=seed)
            |
            Q(hybrid__pollen_genus__istartswith=seed_genus, hybrid__pollen_species__istartswith=seed)
        )
    elif seed:
        this_species_list = this_species_list.filter(
            Q(hybrid__seed_species__istartswith=seed)
            |
            Q(hybrid__pollen_species__istartswith=seed)
        )
    elif seed_genus:
        this_species_list = this_species_list.filter(
            Q(hybrid__seed_genus__istartswith=seed_genus)
            |
            Q(hybrid__pollen_genus__istartswith=seed_genus)
        )

    if pollen and pollen_genus:
        this_species_list = this_species_list.filter(
            Q(hybrid__seed_genus__istartswith=pollen_genus, hybrid__seed_species__istartswith=pollen)
            |
            Q(hybrid__pollen_genus__istartswith=pollen_genus, hybrid__pollen_species__istartswith=pollen)
        )
    elif pollen:
        this_species_list = this_species_list.filter(
            Q(hybrid__seed_species__istartswith=pollen)
            |
            Q(hybrid__pollen_species__istartswith=pollen)
        )
    elif pollen_genus:
        this_species_list = this_species_list.filter(
            Q(hybrid__seed_genus__istartswith=pollen_genus)
            |
            Q(hybrid__pollen_genus__istartswith=pollen_genus)
        )

    # Building pid ;list
    if crit and this_species_list:
        if spc:
            if len(spc) >= 2:
                this_species_list = this_species_list.filter(species__icontains=spc)
            else:
                this_species_list = this_species_list.filter(species__istartswith=spc)

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
               'author': author, 'originator': originator, 'seed': seed, 'pollen': pollen,
               'seed_genus': seed_genus, 'pollen_genus': pollen_genus,
               'role': role, 'level': 'list', 'title': 'hybrid_list',
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
    write_output(request, species.binomial)
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

    # if sort:
    #     if sort == 'pct':
    #         anc_list = anc_list.order_by('-pct')
    #     elif sort == '-pct':
    #         anc_list = anc_list.order_by('pct')
    #     elif sort == 'img':
    #         anc_list = anc_list.order_by('-aid__num_image')
    #     elif sort == '-img':
    #         anc_list = anc_list.order_by('aid__num_image')
    #     elif sort == 'name':
    #         anc_list = anc_list.order_by('aid__genus', 'aid__species')
    #     elif sort == '-name':
    #         anc_list = anc_list.order_by('-aid__genus', '-aid__species')

    for x in anc_list:
        x.anctype = "orchidaceae:" + str(x.anctype)

    context = {'species': species, 'anc_list': anc_list,
               'genus': genus,
               'anc': 'active', 'tab': 'anc',
               'sort': sort, 'prev_sort': prev_sort,
               'title': 'ancestor', 'role': role, 'state': state,
               }
    return render(request, 'orchidaceae/ancestor.html', context)


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
    write_output(request, species.binomial)
    if species.status == 'synonym':
        species = species.getAccepted()

    hybrid = species
    s = p = ss = sp = ps = pp = sss = ssp = sps = spp = pss = psp = pps = ppp = ssss = sssp = ssps = sspp = spss =\
        spsp = spps = sppp = psss = pssp = psps = pspp = ppss = ppsp = ppps = pppp = None
    spc = ''

    if species.type == 'hybrid':
        hybrid.img = hybdir + get_random_img(hybrid)

        if species.hybrid.seed_id and species.hybrid.seed_id.type == 'species':
            if species.hybrid.seed_id.status == 'synonym':
                s = Accepted.objects.get(pk=species.hybrid.seed_id.getAcc())
            else:
                s = Accepted.objects.get(pk=species.hybrid.seed_id)
            s.type = 'species'
            s.parent = 'seed'
            s.year = s.pid.year
            s.img = spcdir + get_random_img(s.pid)

            # tree_list = tree_list + (s,)
        elif species.hybrid.seed_id and species.hybrid.seed_id.type == 'hybrid':
            if species.hybrid.seed_id.status == 'synonym':
                s = Hybrid.objects.get(pk=species.hybrid.seed_id.getAcc())
            else:
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
    return render(request, 'orchidaceae/ancestrytree.html', context)


@login_required
def progeny(request, pid):
    role = getRole(request)
    family = Family.objects.get(pk='Orchidaceae')
    direct = request.GET.get('direct', '')

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    write_output(request, species.binomial)
    genus = species.genus

    #All descendants
    des_list = AncestorDescendant.objects.filter(aid=pid)
    # primary
    prim_list = set(Hybrid.objects.filter(Q(seed_id=pid) | Q(pollen_id=pid)).values_list('pid', flat=True))
    # Secondary
    sec_list = set(Hybrid.objects.filter(Q(seed_id__in=prim_list) | Q(pollen_id__in=prim_list)).values_list('pid', flat=True))

    if len(des_list) > 5000:
        des_list = des_list.filter(pct__gt=30)

    result_list = []
    for x in des_list:
        if x.did.pid.pid in prim_list:
            result_list.append([x,'primary'])
        elif x.did.pid.pid in sec_list:
            result_list.append([x,'secondary'])
        else:
            result_list.append([x,'remote'])

    # total = des_list.count()

    context = {'result_list': result_list, 'species': species, 'family': family,
                'tab': 'pro', 'pro': 'active', 'genus': genus, 'direct': direct,
               'title': 'progeny', 'section': 'Public Area', 'role': role,
               }
    return render(request, 'orchidaceae/progeny.html', context)


@login_required
def progenyimg(request, pid=None):
    num_show = 5
    page_length = 30
    min_pct = 30
    role = getRole(request)
    if not pid:
        pid = request.GET.get('pid', 0)
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    write_output(request, species.binomial)
    genus = species.genus

    des_list = AncestorDescendant.objects.filter(aid=pid).filter(pct__gt= min_pct)
    des_list = des_list.order_by('-pct')

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

    context = {'img_list': page_list, 'species': species, 'tab': 'proimg', 'proimg': 'active',
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

