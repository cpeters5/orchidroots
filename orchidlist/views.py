from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from itertools import chain
from utils.views import write_output
from myproject import conf_orchidaceae
import logging
import random
from myproject import config

# Create your views here.
from django.apps import apps
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

Genus = apps.get_model('orchiddb', 'Genus')
GenusRelation = apps.get_model('orchiddb', 'GenusRelation')
Intragen = apps.get_model('orchiddb', 'Intragen')
Species = apps.get_model('orchiddb', 'Species')
Hybrid = apps.get_model('orchiddb', 'Hybrid')
Accepted = apps.get_model('orchiddb', 'Accepted')
Synonym = apps.get_model('orchiddb', 'Synonym')

Subgenus = apps.get_model('orchiddb', 'Subgenus')
Section = apps.get_model('orchiddb', 'Section')
Subsection = apps.get_model('orchiddb', 'Subsection')
Series = apps.get_model('orchiddb', 'Series')

Distribution = apps.get_model('orchiddb', 'Distribution')
SpcImages = apps.get_model('orchiddb', 'SpcImages')
HybImages = apps.get_model('orchiddb', 'HybImages')
UploadFile = apps.get_model('orchiddb', 'UploadFile')
AncestorDescendant = apps.get_model('orchiddb', 'AncestorDescendant')

# High level lists
def family(request):
    # -- List Genuses
    family_list = Family.objects.order_by('family')
    context = {'family_list': family_list, 'alpha_list': alpha_list, 'title': 'families', }
    return render(request, 'orchidlist/family.html', context)


def subfamily(request):
    # -- List Genuses
    family = conf_orchidaceae.family
    subfamily_list = Subfamily.objects.filter(family=family).order_by('subfamily')
    context = {'subfamily_list': subfamily_list, 'alpha_list': alpha_list, 'title': 'subfamilies', }
    return render(request, 'orchidlist/subfamily.html', context)


def tribe(request):
    sf = ''
    family = conf_orchidaceae.family
    sf_list = Subfamily.objects.filter(family=family)
    tribe_list = Tribe.objects.order_by('tribe').filter(family=family)
    if 'sf' in request.GET:
        sf = request.GET['sf']
        if sf:
            sf_obj = Subfamily.objects.get(pk=sf)
            if sf_obj:
                tribe_list = tribe_list.filter(subfamily=sf)
    context = {'tribe_list': tribe_list, 'title': 'tribes', 'sf': sf, 'sf_list': sf_list, }
    return render(request, 'orchidlist/tribe.html', context)


def subtribe(request):
    family = conf_orchidaceae.family
    sf_list = Subfamily.objects.filter(family=family)
    t_list = Tribe.objects.order_by('tribe').filter(family=family)
    subtribe_list = Subtribe.objects.filter(family=family).order_by('subtribe')
    sf = ''
    t = ''
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

    context = {'subtribe_list': subtribe_list, 'title': 'subtribes', 't': t, 'sf': sf, 'sf_list': sf_list,
               't_list': t_list, }
    return render(request, 'orchidlist/subtribe.html', context)


@login_required
def advanced(request):
    sf = t = st = ''
    family = conf_orchidaceae.family
    specieslist = []
    hybridlist = []
    intragen_list = []
    logger.error("family = " + family)
    subfamily_list = Subfamily.objects.filter(family=family).filter(num_genus__gt=0)
    if 'sf' in request.GET:
        sf = request.GET['sf']
    if sf:
        tribe_list = Tribe.objects.filter(subfamily=sf)
    else:
        tribe_list = Tribe.objects.all()
    if 't' in request.GET:
        t = request.GET['t']
    if t:
        subtribe_list = Subtribe.objects.filter(tribe=t)
    else:
        subtribe_list = Subtribe.objects.all()
    if 'st' in request.GET:
        st = request.GET['st']

    genus_list = Genus.objects.filter(cit_status__isnull=True).exclude(cit_status__exact='').order_by('genus')

    if 'role' in request.GET:
        role = request.GET['role']
    else:
        role = 'pub'

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
        'genus': genus, 'genus_list': genus_list,
        'species_list': specieslist, 'hybrid_list': hybridlist, 'intragen_list': intragen_list,
        'family': family, 'subfamily': sf, 'tribe': t, 'subtribe': st,
        'subfamily_list': subfamily_list, 'tribe_list': tribe_list, 'subtribe_list': subtribe_list,
        'level': 'search', 'title': 'find_orchid', 'role': role,
    }
    return render(request, "orchidlist/advanced.html", context)


@login_required
def advancedx(request):
    sf = t = st = ''
    specieslist = []
    hybridlist = []
    related_list = []
    subgenus_list = section_list = subsection_list = series_list = []

    subfamily_list = Subfamily.objects.all()
    if 'sf' in request.GET:
        sf = request.GET['sf']
    if sf:
        tribe_list = Tribe.objects.filter(subfamily=sf)
    else:
        tribe_list = Tribe.objects.all()
    if 't' in request.GET:
        t = request.GET['t']
    if t:
        subtribe_list = Subtribe.objects.filter(tribe=t)
    else:
        subtribe_list = Subtribe.objects.all()
    if 'st' in request.GET:
        st = request.GET['st']

    genus_list = Genus.objects.filter(cit_status__isnull=True).exclude(cit_status__exact='').order_by('genus')

    if 'role' in request.GET:
        role = request.GET['role']
    else:
        role = 'pub'

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

        subgenus_list = Intragen.objects.filter(gen=genus.pid).filter(subgenus__isnull=False).distinct().values_list('subgenus', flat=True)
        section_list = Intragen.objects.filter(gen=genus.pid).filter(section__isnull=False).distinct().values_list('section', flat=True)
        subsection_list = Intragen.objects.filter(gen=genus.pid).filter(subsection__isnull=False).distinct().values_list('subsection', flat=True)
        series_list = Intragen.objects.filter(gen=genus.pid).filter(series__isnull=False).distinct().values_list('series', flat=True)
        # Construct intragen list
        if genus.type == 'hybrid':
            parents = GenusRelation.objects.get(gen=genus.pid)
            if parents:
                parents = parents.parentlist.split('|')
                related_list = Genus.objects.filter(pid__in=parents)
        else:
            related_list = Genus.objects.filter(description__icontains=genus).filter(type='hybrid').filter(
                num_hybrid__gt=0)

    write_output(request, str(genus))
    context = {
        'genus': genus, 'genus_list': genus_list,
        'species_list': specieslist, 'hybrid_list': hybridlist, 'related_list': related_list,
        'subgenus_list': subgenus_list, 'section_list': section_list, 'subsection_list': subsection_list,
        'series_list': series_list,
        'subfamily': sf, 'tribe': t, 'subtribe': st,
        'subfamily_list': subfamily_list, 'tribe_list': tribe_list, 'subtribe_list': subtribe_list,
        'level': 'search', 'title': 'find_orchid', 'role': role,
    }
    return render(request, "orchidlist/advancedx.html", context)


@login_required
def genera(request):
    genus = ''
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
    role = 'pub'
    t_obj = ''
    st_obj = ''
    num_show = 5
    page_length = 1000
    # max_page_length = 1000
    if 'role' in request.GET:
        role = request.GET['role']
    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']

    if 'genus' in request.GET:
        genus = request.GET['genus']
        if len(genus) > min_lengenus_req:
            genus = str(genus).split()
            genus = genus[0]
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
    if sf_obj or t_obj or st_obj:
        genus = ''
    year_valid = 0
    if 'year' in request.GET:
        year = request.GET['year']
        if valid_year(year):
            year_valid = 1

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
    if year_valid:
        year = int(year)
        genus_list = genus_list.filter(year=year)

    if genus:
        if len(genus) >= 2:
            genus_list = genus_list.filter(genus__icontains=genus)
        elif len(genus) < 2:
            genus_list = genus_list.filter(genus__istartswith=genus)

    if status == 'synonym':
        genus_list = genus_list.filter(status='synonym')

    elif genustype:
        if genustype == 'ALL':
            if year:
                genus_list = genus_list.filter(year=year)
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

    else:
        if not genus:
            genus_list = Genus.objects.none()

    if alpha and len(alpha) == 1:
        genus_list = genus_list.filter(genus__istartswith=alpha)

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

    # Sort before paginator
    if sort:
        if sort == 'sf':
            genus_list = genus_list.order_by('subfamily__subfamily')
        elif sort == 't':
            genus_list = genus_list.order_by('tribe__tribe')
        elif sort == 'st':
            genus_list = genus_list.order_by('subtribe__subtribe')
        else:
            genus_list = genus_list.order_by(sort)

    total = genus_list.count()
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
        = mypaginator(request, genus_list, page_length, num_show)

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
    context = {'my_list': page_list, 'total': total, 'genus_lookup': genus_lookup,
               'sf_obj': sf_obj, 'sf_list': sf_list, 't_obj': t_obj, 't_list': t_list,
               'st_obj': st_obj, 'st_list': st_list,
               'title': 'genera', 'genus': genus, 'year': year, 'genustype': genustype, 'status': status,
               'formula1': formula1, 'formula2': formula2, 'alpha': alpha, 'alpha_list': alpha_list,
               'sort': sort, 'prev_sort': prev_sort, 'role': role,
               'page': page, 'page_range': page_range, 'last_page': last_page, 'next_page': next_page,
               'prev_page': prev_page, 'num_show': num_show, 'first': first_item, 'last': last_item, }
    write_output(request)
    return render(request, 'orchidlist/genera.html', context)


def subgenus(request):
    # -- List Genuses
    subgenus_list = Subgenus.objects.order_by('subgenus')
    context = {'subgenus_list': subgenus_list, 'title': 'subgenus', }
    return render(request, 'orchidlist/subgenus.html', context)


def section(request):
    # -- List Genuses
    section_list = Section.objects.order_by('section')
    context = {'section_list': section_list, 'title': 'section', }
    return render(request, 'orchidlist/section.html', context)


def subsection(request):
    # -- List Genuses
    subsection_list = Subsection.objects.order_by('subsection')
    context = {'subsection_list': subsection_list, 'title': 'subsection', }
    return render(request, 'orchidlist/subsection.html', context)


def series(request):
    # -- List Genuses
    series_list = Series.objects.order_by('series')
    context = {'series_list': series_list, 'title': 'series', }
    return render(request, 'orchidlist/series.html', context)


def getPartialPid(reqgenus, type, status):
    pid_list = []
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
        return reqgenus, pid_list, intragen_list
    else:
        return '', pid_list, intragen_list


@login_required
def species_list(request):
    spc = genus = gen = reqgenus = ''
    # genus = partial genus name
    mysubgenus = mysection = mysubsection = myseries = ''
    subgenus_obj = section_obj = subsection_obj = series_obj = ''
    subgenus_list = section_list = subsection_list = series_list = []
    region = subregion = ''
    region_list = subregion_list = []
    region_obj = subregion_obj = ''
    classtitle = ''
    year = ''
    year_valid = 0
    type = 'species'
    status = author = dist = ''
    sort = prev_sort = ''
    num_show = 5
    page_length = 500
    # max_page_length = 1000

    # Initialize
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
    else:
        alpha = ''

    if 'year' in request.GET:
        year = request.GET['year']
        if valid_year(year):
            year_valid = 1
    if 'spc' in request.GET:
        spc = request.GET['spc']
        if len(spc) == 1:
            alpha = ''
    if 'author' in request.GET:
        author = request.GET['author']
    if 'dist' in request.GET:
        dist = request.GET['dist']
    if alpha != 'ALL':
        alpha = alpha[0: 1]
    if 'subgenus' in request.GET:
        mysubgenus = request.GET['subgenus']
    if 'section' in request.GET:
        mysection = request.GET['section']
    if 'subsection' in request.GET:
        mysubsection = request.GET['subsection']
    if 'series' in request.GET:
        myseries = request.GET['series']
    if 'region' in request.GET:
        region = request.GET['region']
    if 'subregion' in request.GET:
        subregion = request.GET['subregion']

    if 'status' in request.GET:
        status = request.GET['status']
        if not status:
            status = 'accepted'

    if status == 'synonym':
        mysubgenus, mysection, mysubsection, myseries = '', '', '', ''

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

    if 'genus' in request.GET:
        reqgenus = request.GET['genus']

    genus, this_species_list, intragen_list = getPartialPid(reqgenus, type, status)
    total = len(this_species_list)
    temp_subgen_list = []
    if mysubgenus:
        try:
            subgenus_obj = Subgenus.objects.get(pk=mysubgenus)
        except Subgenus.DoesNotExist:
            pass
        if genus:
            temp_subgen_list = Accepted.objects.filter(subgenus=mysubgenus).filter(genus=genus).distinct(). \
                values_list('pid', flat=True)
        else:
            temp_subgen_list = Accepted.objects.filter(subgenus=mysubgenus).distinct().values_list('pid', flat=True)

    temp_sec_list = []
    if mysection:
        try:
            section_obj = Section.objects.get(pk=mysection)
        except Section.DoesNotExist:
            section_obj = ''
        if genus:
            temp_sec_list = Accepted.objects.filter(section=mysection).filter(genus=genus).distinct(). \
                values_list('pid', flat=True)
        else:
            temp_sec_list = Accepted.objects.filter(section=mysection).distinct().values_list('pid', flat=True)

    temp_subsec_list = []
    if mysubsection:
        try:
            subsection_obj = Subsection.objects.get(pk=mysubsection)
        except Subsection.DoesNotExist:
            pass
        if genus:
            temp_subsec_list = Accepted.objects.filter(subsection=mysubsection).filter(genus=genus).distinct(). \
                values_list('pid', flat=True)
        else:
            temp_subsec_list = Accepted.objects.filter(subsection=mysubsection).distinct(). \
                values_list('pid', flat=True)

    temp_ser_list = []
    if myseries:
        try:
            series_obj = Series.objects.get(pk=myseries)
        except Series.DoesNotExist:
            pass
        if genus:
            temp_ser_list = Accepted.objects.filter(series=myseries).filter(genus=genus).distinct(). \
                values_list('pid', flat=True)
        else:
            temp_ser_list = Accepted.objects.filter(series=myseries).distinct().values_list('pid', flat=True)

    if mysubgenus:
        this_species_list = this_species_list.filter(pid__in=temp_subgen_list)
    if mysection:
        this_species_list = this_species_list.filter(pid__in=temp_sec_list)
    if mysubsection:
        this_species_list = this_species_list.filter(pid__in=temp_subsec_list)
    if myseries:
        this_species_list = this_species_list.filter(pid__in=temp_ser_list)

    if region:
        try:
            region_obj = Region.objects.get(id=region)
        except Region.DoesNotExist:
            pass
    if subregion:
        try:
            subregion_obj = Subregion.objects.get(code=subregion)
        except Subregion.DoesNotExist:
            pass

    if spc:
        # if species[0] != '%' and species[-1] != '%':
        if len(spc) >= 2:
            this_species_list = this_species_list.filter(species__icontains=spc)
        else:
            this_species_list = this_species_list.filter(species__istartswith=spc)

    elif alpha:
        if len(alpha) == 1:
            this_species_list = this_species_list.filter(species__istartswith=alpha)

    if author:
        this_species_list = this_species_list.filter(author__icontains=author)

    if dist:
        this_species_list = this_species_list.filter(distribution__icontains=dist)

    if year_valid:
        year = int(year)
        this_species_list = this_species_list.filter(year=year)

    pid_list = []
    if region_obj:
        pid_list = Distribution.objects.filter(region_id=region_obj.id).values_list('pid', flat=True).distinct()
        this_species_list = this_species_list.filter(pid__in=pid_list)
    if subregion_obj:
        pid_list = Distribution.objects.filter(subregion_code=subregion_obj.code). \
            values_list('pid', flat=True).distinct()
        this_species_list = this_species_list.filter(pid__in=pid_list)
    if status == 'synonym':
        pid_list = Synonym.objects.filter(acc_id__in=pid_list).values_list('spid', flat=True).distinct()
        this_species_list = this_species_list.filter(pid__in=pid_list)


    if sort:
        if sort == 'classification':
            this_species_list = this_species_list.order_by('subgenus', 'section', 'subsection', 'series')
        elif sort == '-classification':
            this_species_list = this_species_list.order_by('-subgenus', '-section', '-subsection', '-series')
        else:
            this_species_list = this_species_list.order_by(sort)
    else:
        this_species_list = this_species_list.order_by('genus', 'species')
    subtotal = len(this_species_list)

    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = \
        mypaginator(request, this_species_list, page_length, num_show)

    region_list = Region.objects.exclude(id=0).order_by('name')
    if region_obj:
        subregion_list = Subregion.objects.filter(region=region_obj.id).order_by('name')
    else:
        subregion_list = Subregion.objects.all().order_by('name')


    if status == 'accepted':
        subgenus_list = intragen_list.filter(subgenus__isnull=False).values_list('subgenus', 'subgenus'). \
            distinct().order_by('subgenus')

        if genus:
            subgenus_list = subgenus_list.filter(genus=genus)
        elif reqgenus:
            subgenus_list = subgenus_list.filter(genus__istartswith=reqgenus)

        section_list = intragen_list.filter(section__isnull=False)
        if genus:
            section_list = section_list.filter(genus=genus)
        elif reqgenus:
            section_list = section_list.filter(genus__istartswith=reqgenus)

        subsection_list = intragen_list.filter(subsection__isnull=False)
        if genus:
            subsection_list = subsection_list.filter(genus=genus)
        elif reqgenus:
            subsection_list = subsection_list.filter(genus__istartswith=reqgenus)

        series_list = intragen_list.filter(series__isnull=False)
        if genus:
            series_list = series_list.filter(genus=genus)
        elif reqgenus:
            series_list = series_list.filter(genus__istartswith=reqgenus)

        if mysubgenus:
            section_list = section_list.filter(subgenus=mysubgenus)
            subsection_list = subsection_list.filter(subgenus=mysubgenus)
            series_list = series_list.filter(subgenus=mysubgenus)

        if mysection:
            subsection_list = subsection_list.filter(section=mysection)
            series_list = series_list.filter(section=mysection)

        section_list = section_list.values_list('section', 'section').distinct().order_by('section')
        subsection_list = subsection_list.values_list('subsection', 'subsection').distinct().order_by('subsection')
        series_list = series_list.values_list('series', 'series').distinct().order_by('series')

        # Sort by classification
        if not subgenus_list:
            subgenus_obj = ''
        else:
            classtitle = classtitle + 'Subgenus'
        if not section_list:
            section_obj = ''
        else:
            classtitle = classtitle + ' Section'
        if not subsection_list:
            subsection_obj = ''
        else:
            classtitle = classtitle + ' Subsection'
        if not series_list:
            series_obj = ''
        else:
            classtitle = classtitle + ' Series'

    if classtitle == '':
        classtitle = 'Classification'
    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']
    write_output(request, str(genus))
    logger.warning(">>> " + request.path + str(request.user))
    context = {'page_list': page_list, 'alpha_list': alpha_list, 'alpha': alpha, 'spc': spc,
               'role': role, 'total': total, 'subtotal': subtotal,
               'subgenus_list': subgenus_list, 'subgenus_obj': subgenus_obj,
               'section_list': section_list, 'section_obj': section_obj, 'genus': reqgenus,
               'subsection_list': subsection_list, 'subsection_obj': subsection_obj,
               'series_list': series_list, 'series_obj': series_obj,
               'classtitle': classtitle,
               'year': year, 'status': status,
               'author': author, 'dist': dist,
               'region_obj': region_obj, 'region_list': region_list, 'subregion_obj': subregion_obj,
               'subregion_list': subregion_list, 'sort': sort, 'prev_sort': prev_sort,
               'page': page, 'page_range': page_range, 'last_page': last_page, 'next_page': next_page,
               'prev_page': prev_page, 'num_show': num_show, 'first': first_item, 'last': last_item,
               'level': 'list', 'title': 'species_list', 'type': 'species'
               }
    return render(request, 'orchidlist/species.html', context)


@login_required
def hybrid_list(request):
    spc = ''
    genus = ''
    type = 'hybrid'
    # min_lenspecies_req = 2
    year = ''
    year_valid = 0
    status = ''
    author = ''
    originator = ''
    seed_genus = ''
    pollen_genus = ''
    seed = ''
    pollen = ''
    reqgenus = ''
    alpha = ''
    sort = ''
    prev_sort = ''

    num_show = 5
    page_length = 200

    # Initialization
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
    if 'year' in request.GET:
        year = request.GET['year']
        if valid_year(year):
            year_valid = 1
    if 'seed_genus' in request.GET:
        seed_genus = request.GET['seed_genus']
        if seed_genus == 'clear':
            seed_genus = ''
    if 'seed' in request.GET:
        seed = request.GET['seed']

    if 'pollen_genus' in request.GET:
        pollen_genus = request.GET['pollen_genus']
        if pollen_genus == 'clear':
            pollen_genus = ''
    if 'pollen' in request.GET:
        pollen = request.GET['pollen']

    if 'status' in request.GET:
        status = request.GET['status']

    if not status:
        status = 'accepted'
    elif status == 'synonym':
        seed_genus = seed = pollen_genus = pollen = ''

    if 'spc' in request.GET:
        spc = request.GET['spc']
        if len(spc) == 1:
            alpha = ''
    if 'author' in request.GET:
        author = request.GET['author']
    if 'originator' in request.GET:
        originator = request.GET['originator']
    if alpha != 'ALL':
        alpha = alpha[0:1]
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
    if 'genus' in request.GET:
        reqgenus = request.GET['genus']

    # Building pid ;list
    genus, this_species_list, intragen_list = getPartialPid(reqgenus, type, status)
    total = len(this_species_list)

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

    if spc:
        if len(spc) >= 2:
            this_species_list = this_species_list.filter(species__icontains=spc)
        else:
            this_species_list = this_species_list.filter(species__istartswith=spc)

    elif alpha:
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

    # # Add the following to clear the list if no filter given
    # if not genus and not spc and not seed and not pollen and not year and not author and not originator and not dist \
    #         and not ancestor and not subgenus and not section and not subsection and not series:
    #     this_species_list = Species.objects.none()

    if sort:
        this_species_list = this_species_list.order_by(sort)
    else:
        this_species_list = this_species_list.order_by('genus', 'species')
    subtotal = this_species_list.count()

    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
        = mypaginator(request, this_species_list, page_length, num_show)

    genus_list = list(Genus.objects.exclude(status='synonym').values_list('genus', flat=True))
    genus_list.sort()
    write_output(request, str(reqgenus))
    logger.warning(">>> " + request.path + str(request.user) + ": " + str(reqgenus))
    context = {'my_list': page_list, 'genus_list': genus_list,
               'total': total, 'subtotal': subtotal, 'alpha_list': alpha_list, 'alpha': alpha, 'spc': spc,
               'genus': reqgenus, 'year': year, 'status': status,
               'author': author, 'originator': originator, 'seed': seed, 'pollen': pollen,
               'seed_genus': seed_genus, 'pollen_genus': pollen_genus,
               'sort': sort, 'prev_sort': prev_sort,
               'page': page, 'page_range': page_range, 'last_page': last_page, 'next_page': next_page,
               'prev_page': prev_page, 'num_show': num_show, 'first': first_item, 'last': last_item,
               'level': 'list', 'title': 'hybrid_list',
               }
    return render(request, 'orchidlist/hybrid.html', context)


def browsegen(request):
    gen = 0
    genus = ''
    display = ''
    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']

    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL':
            alpha = None
    if 'display' in request.GET:
        display = request.GET['display']
    if 'type' in request.GET:
        reqtype = request.GET['type']
    else:
        reqtype = 'species'

    my_full_list = []
    if reqtype == 'species':
        ordir = 'utils/images/species/'
        gen_list = Genus.objects.filter(num_species__gt=0).exclude(genus='na')
        if alpha:
            gen_list = gen_list.filter(genus__istartswith=alpha)
        if not gen_list:
            return HttpResponseRedirect("/orchidlist/browsegen/?role=" + role + "&type=hybrid")
        for x in gen_list:
            y = Species.objects.filter(gen=x).filter(type='species').exclude(status='synonym')
            if display == 'checked':
                y = y.filter(num_image__gt=0)
            y = y.order_by('-num_image', '?')[0: 1]
            if len(y):
                y = y[0]
                if y.get_best_img():
                    y.image_file = ordir + y.get_best_img().image_file
                elif display != 'checked':
                    y.image_file = ordir + 'noimage_light.jpg'
                my_full_list.append(y)
    else:
        ordir = 'utils/images/hybrid/'
        gen_list = Genus.objects.filter(num_hybrid__gt=0).exclude(genus='na')
        if alpha:
            gen_list = gen_list.filter(genus__istartswith=alpha)
        if not gen_list:
            return HttpResponseRedirect("/orchidlist/browsegen/?role=" + role + "&type=species")
        for x in gen_list:
            y = Species.objects.filter(gen=x).filter(type='hybrid').exclude(status='synonym')
            if display == 'checked':
                y = y.filter(num_image__gt=0)
            y = y.order_by('-num_image', '?')[0: 1]
            if len(y):
                y = y[0]
                if y.get_best_img():
                    y.image_file = ordir + y.get_best_img().image_file
                    my_full_list.append(y)
                elif display != 'checked':
                    y.image_file = ordir + 'noimage_light.jpg'
                    my_full_list.append(y)
    num_show = 5
    page_length = 20
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
        = mypaginator(request, my_full_list, page_length, num_show)
    context = {
        'page_list': page_list, 'type': reqtype, 'gen': gen, 'genus': genus,
        'page': page, 'page_range': page_range, 'last_page': last_page, 'num_show': num_show,
        'page_length': page_length, 'alpha': alpha, 'alpha_list': alpha_list, 'display': display,
        'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
        'level': 'detail', 'title': 'browsegen', 'section': 'My Collection', 'role': role,
               }
    write_output(request)
    return render(request, 'orchidlist/browse_gen.html', context)


def browse(request):
    import collections
    reqsubgenus = reqsection = reqsubsection = reqseries = ''
    subgenus_obj = section_obj = subsection_obj = series_obj = ''
    subgenus_list = section_list = subsection_list = series_list = []
    page_range = page_list = last_page = next_page = prev_page = page = first_item = last_item = alpha = total = ''
    display = ''
    role = 'pub'
    seed_genus = pollen_genus = seed = pollen = ''
    reqgenus = ''
    img_list = my_full_list = []

    if 'display' in request.GET:
        display = request.GET['display']
    if not display:
        display = ''
    if 'type' in request.GET:
        type = request.GET['type']
    else:
        type = 'species'
    if 'role' in request.GET:
        role = request.GET['role']
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

    # pid_list = ()
    if 'genus' in request.GET:
        reqgenus = request.GET['genus']

    genus, pid_list, intragen_list = getPartialPid(reqgenus, type, 'accepted')
    total = len(pid_list)

    num_show = 5
    page_length = 20
    if pid_list:
        img_list = Species.objects.filter(type=type).exclude(status='synonym')
        if display == 'checked':
            img_list = img_list.filter(num_image__gt=0)
        if type == 'species':
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
        if img_list:
            if type == 'species':
                ordir = 'utils/images/species/'
                # img_list = img_list.filter(type__iexact='species')
            else:
                ordir = 'utils/images/hybrid/'
                # img_list = img_list.filter(type__iexact='hybrid')
            if display == "checked":
                img_list = img_list.filter(num_image__gt=0)
            if alpha:
                img_list = img_list.filter(species__istartswith=alpha)

            img_list = img_list.order_by('genus', 'species')
            for x in img_list:
                if x.get_best_img():
                    x.image_file = ordir + x.get_best_img().image_file
                    my_full_list.append(x)
                else:
                    x.image_file = ordir + 'noimage_light.jpg'
                    my_full_list.append(x)
        total = len(my_full_list)
        page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
            = mypaginator(request, my_full_list, page_length, num_show)
    genus_list = Genus.objects.all()
    write_output(request, reqgenus)
    logger.warning(">>> " + request.path + str(request.user) + ": " + str(reqgenus))
    context = {
        'page_list': page_list, 'type': type, 'genus': reqgenus, 'display': display, 'genus_list': genus_list,
        'page_range': page_range, 'last_page': last_page, 'num_show': num_show, 'page_length': page_length,
        'page': page, 'alpha': alpha, 'alpha_list': alpha_list, 'total': total,
        'first': first_item, 'last': last_item, 'next_page': next_page, 'prev_page': prev_page,
        'level': 'browse', 'title': 'browse', 'section': 'list', 'role': role,
    }
    if type == 'species':
        context.update({'subgenus_list': subgenus_list, 'subgenus_obj': subgenus_obj,
        'section_list': section_list, 'section_obj': section_obj,
        'subsection_list': subsection_list, 'subsection_obj': subsection_obj,
        'series_list': series_list, 'series_obj': series_obj,
                    })

    else:
        context.update({'seed_genus': seed_genus, 'pollen_genus': pollen_genus,'seed': seed, 'pollen': pollen,})

    return render(request, 'orchidlist/browse.html', context)


def browsedist(request):
    dist_list = get_distlist()
    context = {'dist_list': dist_list, }
    return render(request, 'orchidlist/browsedist.html', context)


# All access - at least role = pub
@login_required
def progeny(request, pid=None):
    alpha = ''
    sort = ''
    prev_sort = ''
    num_show = 5
    page_length = 30
    role = 'pub'

    if not pid:
        if 'pid' in request.GET:
            pid = request.GET['pid']
            pid = int(pid)
        else:
            pid = 0

    if 'role' in request.GET:
        role = request.GET['role']

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        message = 'This hybrid does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    genus = species.genus
    des_list = AncestorDescendant.objects.filter(aid=pid)

    if 'sort' in request.GET:
        sort = request.GET['sort']
        sort.lower()

    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
        if alpha == 'ALL' or alpha == 'all':
            alpha = ''
        des_list = des_list.filter(did__pid__species__istartswith=alpha)

    if sort:
        if request.GET.get('prev_sort'):
            prev_sort = request.GET['prev_sort']
        if prev_sort == sort:
            if sort.find('-', 0) >= 0:
                sort = sort.replace('-', '')
            else:
                sort = '-'+sort
        else:
            # sort = '-' + sort
            prev_sort = sort

    if sort:
        if sort == 'pct':
            des_list = des_list.order_by('-pct', 'did__pid__genus', 'did__pid__species')
        elif sort == '-pct':
            des_list = des_list.order_by('pct', 'did__pid__genus', 'did__pid__species')
        elif sort == 'img':
            des_list = des_list.order_by('-did__pid__num_image', 'did__pid__genus', 'did__pid__species')
        elif sort == '-img':
            des_list = des_list.order_by('did__pid__num_image', 'did__pid__genus', 'did__pid__species')
        elif sort == 'name':
            des_list = des_list.order_by('did__pid__genus', 'did__pid__species')
        elif sort == '-name':
            des_list = des_list.order_by('-did__pid__genus', '-did__pid__species')
        elif sort == 'seed':
            des_list = des_list.order_by('did__seed_id__genus', 'did__seed_id__species')
        elif sort == 'pollen':
            des_list = des_list.order_by('did__pollen_id__genus', 'did__pollen_id__species')

        elif sort == '-seed':
            des_list = des_list.order_by('-did__seed_id__genus', '-did__seed_id__species')
        elif sort == '-pollen':
            des_list = des_list.order_by('-did__pollen_id__genus', '-did__pollen_id__species')
    else:
        des_list = des_list.order_by('did__pid__genus', 'did__pid__species')
    total = des_list.count()

    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
            request, des_list, page_length, num_show)

    write_output(request, species.textname())
    context = {'des_list': page_list, 'species': species, 'total': total, 'alpha': alpha, 'alpha_list': alpha_list,
                'sort': sort, 'prev_sort': prev_sort, 'tab': 'pro', 'pro': 'active',
               'genus': genus, 'page': page,
               'page_range': page_range, 'last_page': last_page, 'next_page': next_page, 'prev_page': prev_page,
               'num_show': num_show, 'first': first_item, 'last': last_item,
               'level': 'orchidlist', 'title': 'progeny', 'section': 'Public Area', 'role': role,
               }
    return render(request, 'orchidlist/progeny.html', context)


# All access - at least role = pub
@login_required
def progenyimg(request, pid=None):
    num_show = 5
    page_length = 30

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
    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']

    des_list = AncestorDescendant.objects.filter(aid=pid).filter(pct__gt=20)
    des_list = des_list.order_by('-pct')

    img_list = []
    for x in des_list:
        offspring = Hybrid.objects.get(pk=x.did.pid_id)
        offimg = HybImages.objects.filter(pid=x.did.pid_id).filter(rank__gt=3).order_by('?')
        if offimg:
            x.img = offimg[:1][0]
            x.offspring = offspring
            x.pollen = offspring.pollen_id
            x.seed = offspring.seed_id
            img_list.append(x)

    total = len(img_list)
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = mypaginator(
            request, img_list, page_length, num_show)

    write_output(request, species.textname())
    context = {'des_list': page_list, 'species': species, 'tab': 'proimg', 'proimg': 'active',
               'genus': genus, 'total': total, 'page_range': page_range, 'last_page': last_page,
               'num_show': num_show, 'first': first_item, 'last': last_item, 'role': role,
               'level': 'orchidlist', 'title': 'progenyimg', 'section': 'Public Area',
               }
    return render(request, 'orchidlist/progenyimg.html', context)


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
