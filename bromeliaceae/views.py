from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
import string
from itertools import chain
from utils.views import write_output, paginator
import logging
import random

# Create your views here.
from django.apps import apps
Genus = apps.get_model('bromeliaceae', 'Genus')
Species = apps.get_model('bromeliaceae', 'Species')
Hybrid = apps.get_model('bromeliaceae', 'Hybrid')
Accepted = apps.get_model('bromeliaceae', 'Accepted')
Family = apps.get_model('orchiddb', 'Family')
SpcImages = apps.get_model('bromeliaceae', 'SpcImages')
HybImages = apps.get_model('bromeliaceae', 'HybImages')
UploadFile = apps.get_model('orchiddb', 'UploadFile')
User = get_user_model()
alpha_list = string.ascii_uppercase
logger = logging.getLogger(__name__)


def advanced(request):
    family = ''
    specieslist = []
    hybridlist = []
    intragen_list = []

    family_list = Family.objects.all()
    if 'f' in request.GET:
        family = request.GET['f']
    # if  f:
    #     tribe_list = Tribe.objects.filter(subfamily=sf)
    # else:
    #     tribe_list = Tribe.objects.all()
    # if 't' in request.GET:
    #     t = request.GET['t']
    # if t:
    #     subtribe_list = Subtribe.objects.filter(tribe=t)
    # else:
    #     subtribe_list = Subtribe.objects.all()
    # if 'st' in request.GET:
    #     st = request.GET['st']

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
        # 'intragen_list': intragen_list,
        'family': family, 'family_list': family_list,
        # 'subfamily': sf, 'tribe': t, 'subtribe': st,
        # 'subfamily_list': subfamily_list, 'tribe_list': tribe_list, 'subtribe_list': subtribe_list,
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

    year_valid = 0
    if 'year' in request.GET:
        year = request.GET['year']
        if valid_year(year):
            year_valid = 1

    # if 'formula1' in request.GET:
    #     formula1 = request.GET['formula1']
    # if 'formula2' in request.GET:
    #     formula2 = request.GET['formula2']

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
        genus_list = genus_list.order_by(sort)

    total = genus_list.count()
    page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item \
        = paginator(request, genus_list, page_length, num_show)

    genus_lookup = Genus.objects.filter(pid__gt=0).filter(type='species')
    context = {'my_list': page_list, 'total': total, 'genus_lookup': genus_lookup,
               'title': 'genera', 'genus': genus, 'year': year, 'genustype': genustype, 'status': status,
               'alpha': alpha, 'alpha_list': alpha_list,
               'sort': sort, 'prev_sort': prev_sort, 'role': role,
               'page': page, 'page_range': page_range, 'last_page': last_page, 'next_page': next_page,
               'prev_page': prev_page, 'num_show': num_show, 'first': first_item, 'last': last_item, }
    write_output(request)
    return render(request, 'bromeliaceae/genera.html', context)
