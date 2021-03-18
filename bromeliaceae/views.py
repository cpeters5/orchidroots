from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
import string
from itertools import chain
from utils.views import write_output, paginator, getRole
import logging
import random
from myproject import config
from myproject import conf_bromeliaceae

# Create your views here.
from django.apps import apps
Subfamily = apps.get_model('core', 'Subfamily')
Tribe = apps.get_model('core', 'Tribe')
Subtribe = apps.get_model('core', 'Subtribe')

Genus = apps.get_model('bromeliaceae', 'Genus')
Species = apps.get_model('bromeliaceae', 'Species')
Hybrid = apps.get_model('bromeliaceae', 'Hybrid')
Accepted = apps.get_model('bromeliaceae', 'Accepted')
SpcImages = apps.get_model('bromeliaceae', 'SpcImages')
# HybImages = apps.get_model('bromeliaceae', 'HybImages')
UploadFile = apps.get_model('orchidaceae', 'UploadFile')
User = get_user_model()
alpha_list = config.alpha_list
logger = logging.getLogger(__name__)


def advanced(request):
    specieslist = []
    hybridlist = []
    # intragen_list = []
    sf = t = st = ''
    family = conf_bromeliaceae.family
    logger.error("family = " + family)
    # family_list = Family.objects.all()
    # if 'f' in request.GET:
    #     family = request.GET['f']

    subfamily_list = Subfamily.objects.filter(family=family)
    # subfamily_list = Subfamily.objects.filter(family=family).filter(num_genus__gt=0)
    tribe_list = Tribe.objects.filter(subfamily=family)
    subtribe_list = Subtribe.objects.filter(family=family)
    if 't' in request.GET:
        t = request.GET['t']
        subtribe_list = subtribe_list.filter(tribe=t)
    if 'st' in request.GET:
        st = request.GET['st']
    logger.error("family list = " + str(len(subfamily_list)))

    genus_list = Genus.objects.filter(cit_status__isnull=True).exclude(cit_status__exact='').order_by('genus')

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
        # if genus.type == 'hybrid':
            # parents = GenusRelation.objects.get(gen=genus.pid)
            # if parents:
            #     parents = parents.parentlist.split('|')
            #     intragen_list = Genus.objects.filter(pid__in=parents)
        # else:
        #     intragen_list = Genus.objects.filter(description__icontains=genus).filter(type='hybrid').filter(
        #         num_hybrid__gt=0)

    write_output(request, str(genus))
    context = {
        'genus': genus, 'genus_list': genus_list,
        'species_list': specieslist, 'hybrid_list': hybridlist,
        'family': family,
        'subfamily': sf, 'tribe': t, 'subtribe': st,
        'subfamily_list': subfamily_list, 'tribe_list': tribe_list, 'subtribe_list': subtribe_list,
        'level': 'search', 'title': 'find_orchid', 'role': role,
    }
    return render(request, "bromeliaceae/advanced.html", context)


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
    t_obj = ''
    st_obj = ''
    num_show = 5
    page_length = 1000
    # max_page_length = 1000
    role = getRole(request)
    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']

    if 'genus' in request.GET:
        genus = request.GET['genus']
        if len(genus) > min_lengenus_req:
            genus = str(genus).split()
            genus = genus[0]

    year_valid = 0
    if 'year' in request.GET:
        year = request.GET['year']
        if valid_year(year):
            year_valid = 1

    if 'genustype' in request.GET:
        genustype = request.GET['genustype']
    if not genustype:
        genustype = 'ALL'

    if 'formula1' in request.GET:
        formula1 = request.GET['formula1']
    if 'formula2' in request.GET:
        formula2 = request.GET['formula2']

    # if 'formula1' in request.GET:
    #     formula1 = request.GET['formula1']
    # if 'formula2' in request.GET:
    #     formula2 = request.GET['formula2']

    if 'status' in request.GET:
        status = request.GET['status']

    genus_list = Genus.objects.all()
    print(len(genus_list))

    if year_valid:
        year = int(year)
        genus_list = genus_list.filter(year=year)

    if genus:
        if len(genus) >= 2:
            genus_list = genus_list.filter(genus__icontains=genus)
        elif len(genus) < 2:
            genus_list = genus_list.filter(genus__istartswith=genus)
    logger.error("genus = " + str(genus) + " genus lenght = " + str(len(genus_list)))

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
    else:
        genustype = 'ALL'
        #     genus_list = Genus.objects.none()
    logger.error("year = " + str(year) + " genus lenght = " + str(len(genus_list)))

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
        genus_list = genus_list.order_by(sort)

    total = genus_list.count()
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
        = paginator(request, genus_list, page_length, num_show)
    logger.error("genus = " + str(genus) + " page lenght = " + str(len(page_list)))

    genus_lookup = Genus.objects.filter(pid__gt=0).filter(type='species')
    context = {'my_list': page_list, 'total': total, 'genus_lookup': genus_lookup,
               'title': 'genera', 'genus': genus, 'year': year, 'genustype': genustype, 'status': status,
               'alpha': alpha, 'alpha_list': alpha_list,
               'sort': sort, 'prev_sort': prev_sort, 'role': role,
               'page': page, 'page_range': page_range, 'last_page': last_page, 'next_page': next_page,
               'prev_page': prev_page, 'num_show': num_show, 'first': first_item, 'last': last_item, }
    write_output(request)
    return render(request, 'bromeliaceae/genera.html', context)


@login_required
def species_list(request):
    spc = genus = gen = ''
    # genus = partial genus name
    mysubgenus = mysection = mysubsection = myseries = ''
    subgenus_obj = section_obj = subsection_obj = series_obj = ''
    region_obj = subregion_obj = ''
    year = ''
    year_valid = 0
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
    if 'status' in request.GET:
        status = request.GET['status']

    # Get regions
    if 'region' in request.GET:
        region = request.GET['region']
        if region:
            try:
                region_obj = Region.objects.get(id=region)
            except Region.DoesNotExist:
                pass
    if 'subregion' in request.GET:
        subregion = request.GET['subregion']
        if subregion:
            try:
                subregion_obj = Subregion.objects.get(code=subregion)
            except Subregion.DoesNotExist:
                pass
    region_list = Region.objects.exclude(id=0)
    if region_obj:
        subregion_list = Subregion.objects.filter(region=region_obj.id)
    else:
        subregion_list = Subregion.objects.all()

    # Get list for display
    if 'status' in request.GET:
        status = request.GET['status']
    this_species_list = Species.objects.exclude(status='pending').filter(type='species')
    if status == 'synonym':
        this_species_list = this_species_list.filter(status='synonym')
    elif status == 'accepted':
        this_species_list = this_species_list.exclude(status='synonym')

    if 'genus' in request.GET:
        genus = request.GET['genus']
        try:
            gen = Genus.objects.get(genus=genus).pid
        except Genus.DoesNotExist:
            gen = ''

    intragen_list = Intragen.objects.all()

    if genus:
        if genus[0] != '%' and genus[-1] != '%':
            this_species_list = this_species_list.filter(genus__icontains=genus)
            intragen_list = intragen_list.filter(genus__icontains=genus)

        elif genus[0] == '%' and genus[-1] != '%':
            mygenus = genus[1:]
            this_species_list = this_species_list.filter(genus__iendswith=mygenus)
            intragen_list = intragen_list.filter(genus__iendswith=genus)

        elif genus[0] != '%' and genus[-1] == '%':
            mygenus = genus[:-1]
            this_species_list = this_species_list.filter(genus__istartswith=mygenus)
            intragen_list = intragen_list.filter(genus__istartswith=genus)
        elif genus[0] == '%' and genus[-1] == '%':
            mygenus = genus[1:-1]
            this_species_list = this_species_list.filter(genus__icontains=mygenus)
            intragen_list = intragen_list.filter(genus__icontains=genus)

    temp_subgen_list = []
    if 'subgenus' in request.GET:
        mysubgenus = request.GET['subgenus']
        if mysubgenus:
            try:
                subgenus_obj = Subgenus.objects.get(pk=mysubgenus)
            except Subgenus.DoesNotExist:
                pass
            if gen:
                temp_subgen_list = Accepted.objects.filter(subgenus=mysubgenus).filter(gen=gen).distinct(). \
                    values_list('pid', flat=True)
            else:
                temp_subgen_list = Accepted.objects.filter(subgenus=mysubgenus).distinct().values_list('pid', flat=True)

    temp_sec_list = []
    if 'section' in request.GET:
        mysection = request.GET['section']
        if mysection:
            try:
                section_obj = Section.objects.get(pk=mysection)
            except Section.DoesNotExist:
                section_obj = ''
            if gen:
                temp_sec_list = Accepted.objects.filter(section=mysection).filter(gen=gen).distinct(). \
                    values_list('pid', flat=True)
            else:
                temp_sec_list = Accepted.objects.filter(section=mysection).distinct().values_list('pid', flat=True)

    temp_subsec_list = []
    if 'subsection' in request.GET:
        mysubsection = request.GET['subsection']
        if mysubsection:
            try:
                subsection_obj = Subsection.objects.get(pk=mysubsection)
            except Subsection.DoesNotExist:
                pass
            if gen:
                temp_subsec_list = Accepted.objects.filter(subsection=mysubsection).filter(gen=gen).distinct(). \
                    values_list('pid', flat=True)
            else:
                temp_subsec_list = Accepted.objects.filter(subsection=mysubsection).distinct(). \
                    values_list('pid', flat=True)

    temp_ser_list = []
    if 'series' in request.GET:
        myseries = request.GET['series']
        if myseries:
            try:
                series_obj = Series.objects.get(pk=myseries)
            except Series.DoesNotExist:
                pass
            if gen:
                temp_ser_list = Accepted.objects.filter(series=myseries).filter(gen=gen).distinct(). \
                    values_list('pid', flat=True)
            else:
                temp_ser_list = Accepted.objects.filter(series=myseries).distinct().values_list('pid', flat=True)

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
    if mysubgenus:
        this_species_list = this_species_list.filter(pid__in=temp_subgen_list)
    if mysection:
        this_species_list = this_species_list.filter(pid__in=temp_sec_list)
    if mysubsection:
        this_species_list = this_species_list.filter(pid__in=temp_subsec_list)
    if myseries:
        this_species_list = this_species_list.filter(pid__in=temp_ser_list)

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

    if region_obj:
        pid_list = Distribution.objects.filter(region_id=region_obj.id).values_list('pid', flat=True).distinct()
        this_species_list = this_species_list.filter(pid__in=pid_list)
    if subregion_obj:
        pid_list = Distribution.objects.filter(subregion_code=subregion_obj.code). \
            values_list('pid', flat=True).distinct()
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
    total = this_species_list.count()

    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item = \
        mypaginator(request, this_species_list, page_length, num_show)

    subgenus_list = intragen_list.filter(subgenus__isnull=False).values_list('subgenus', 'subgenus'). \
        distinct().order_by('subgenus')
    if gen:
        subgenus_list = subgenus_list.filter(gen=gen)
    elif genus:
        subgenus_list = subgenus_list.filter(genus__istartswith=genus)

    section_list = intragen_list.filter(section__isnull=False)
    if gen:
        section_list = section_list.filter(gen=gen)
    elif genus:
        section_list = section_list.filter(genus__istartswith=genus)

    subsection_list = intragen_list.filter(subsection__isnull=False)
    if gen:
        subsection_list = subsection_list.filter(gen=gen)
    elif genus:
        subsection_list = subsection_list.filter(genus__istartswith=genus)

    series_list = intragen_list.filter(series__isnull=False)
    if gen:
        series_list = series_list.filter(gen=gen)
    elif genus:
        series_list = series_list.filter(genus__istartswith=genus)

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
    classtitle = ''
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
    role = getRole(request)
    write_output(request, str(genus))
    context = {'page_list': page_list, 'total': total, 'alpha_list': alpha_list, 'alpha': alpha, 'spc': spc,
               'role': role,
               'subgenus_list': subgenus_list, 'subgenus_obj': subgenus_obj,
               'section_list': section_list, 'section_obj': section_obj, 'genus': genus,
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
    return render(request, 'bromeliaceae/species.html', context)


@login_required
def hybrid_list(request):
    spc = ''
    genus = ''
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

    alpha = ''
    sort = ''
    prev_sort = ''

    num_show = 5
    page_length = 200

    if 'alpha' in request.GET:
        alpha = request.GET['alpha']

    if 'year' in request.GET:
        year = request.GET['year']
        if valid_year(year):
            year_valid = 1

    if 'status' in request.GET:
        status = request.GET['status']

    this_species_list = Species.objects.exclude(status='pending').filter(type='hybrid')
    if status == 'synonym':
        this_species_list = this_species_list.filter(status='synonym')
    elif status == 'accepted':
        this_species_list = this_species_list.exclude(status='synonym')

    if 'genus' in request.GET:
        genus = request.GET['genus']
    if 'seed_genus' in request.GET:
        seed_genus = request.GET['seed_genus']
    if seed_genus == 'clear':
        seed_genus = ''

    if 'pollen_genus' in request.GET:
        pollen_genus = request.GET['pollen_genus']
    if pollen_genus == 'clear':
        pollen_genus = ''

    genus_list = list(Genus.objects.exclude(status='synonym').values_list('genus', flat=True))
    genus_list.sort()

    if genus:
        if not seed_genus and not pollen_genus:
            if genus[0] == '*' or genus[-1] == '*':
                genus = genus.replace('*','')
                this_species_list = this_species_list.filter(genus__icontains=genus)
            else:
                this_species_list = this_species_list.filter(genus=genus)
        else:
            # If user request one or both parent genus, then reset genus to ''
            genus = ''

    if 'spc' in request.GET:
        spc = request.GET['spc']
        if len(spc) == 1:
            alpha = ''

    if 'author' in request.GET:
        author = request.GET['author']
    if 'originator' in request.GET:
        originator = request.GET['originator']

    if 'seed' in request.GET:
        seed = request.GET['seed']

    if 'pollen' in request.GET:
        pollen = request.GET['pollen']


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

    if spc:
        # if species[0] != '%' and species[-1] != '%':
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

    if seed_genus:
        this_species_list = this_species_list.filter(Q(hybrid__seed_genus=seed_genus)
                                                     | Q(hybrid__pollen_genus=seed_genus))
    if pollen_genus:
        this_species_list = this_species_list.filter(Q(hybrid__seed_genus=pollen_genus)
                                                     | Q(hybrid__pollen_genus=pollen_genus))

    if seed:
        this_species_list = this_species_list.filter(Q(hybrid__seed_species__icontains=seed)
                                                     | Q(hybrid__pollen_species__icontains=seed))

    if pollen:
        this_species_list = this_species_list.filter(Q(hybrid__seed_species__icontains=pollen)
                                                     | Q(hybrid__pollen_species__icontains=pollen))

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
    total = this_species_list.count()

    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
        = mypaginator(request, this_species_list, page_length, num_show)
    write_output(request, str(genus))
    context = {'my_list': page_list, 'genus_list': genus_list,
               'total': total, 'alpha_list': alpha_list, 'alpha': alpha, 'spc': spc,
               'genus': genus, 'year': year, 'status': status,
               'author': author, 'originator': originator, 'seed': seed, 'pollen': pollen, 'seed_genus': seed_genus,
               'pollen_genus': pollen_genus,
               'sort': sort, 'prev_sort': prev_sort,
               'page': page, 'page_range': page_range, 'last_page': last_page, 'next_page': next_page,
               'prev_page': prev_page, 'num_show': num_show, 'first': first_item, 'last': last_item,
               'level': 'list', 'title': 'hybrid_list',
               }
    return render(request, 'bromeliaceae/hybrid.html', context)
