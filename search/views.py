from django.shortcuts import render, redirect
from django.db import connection
from django.db.models import Case, When, Value, Subquery, OuterRef, Q, CharField
from django.db.models.functions import Replace
from django.apps import apps
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from itertools import chain
from fuzzywuzzy import fuzz, process
from common.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages, SpcImages, Species
from accounts.models import User, Photographer
from utils.views import write_output, getRole, clean_search_string, expand_genus_name, Replace, MultiReplace, RemoveSpaces, clean_query, clean_name
from utils import config
import unicodedata

applications = config.applications
big_genera = config.big_genera
alpha_list = config.alpha_list

# NEW

def autocomplete_species(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query:
        matches = Species.objects.filter(
            binomial__istartswith=query
        ).values_list('binomial', flat=True)[:10]  # Limit suggestions to 10
        suggestions = list(matches)

    return JsonResponse({'suggestions': suggestions})



# Search scientific name
def search(request, app=None):
    if not app:
        # Legacy case, app may be given in query string
        app = request.GET.get('app', 'orchidaceae')  # handle legacy case
    Genus = apps.get_model(app, 'Genus')
    Species = apps.get_model(app, 'Species')

    # Search scientific name only
    # Get genus from the first word in search string.
    # If found, get family and application
    # From list of genera, find matching species from the rest of search string.
    # if no results, redirect to common name search
    role = getRole(request)
    search_list = []
    genus_list = []
    match_spc_list = []
    full_path = request.path
    path = 'summary'
    full_search_string = ''
    other_genus_spc = ''
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'

    # Get search string
    search_string = request.GET.get('search_string', '').strip()

    if not search_string:
        context = {'search_string': search_string,'app': app, 'role': role}
        return render(request, "search/search_results.html", context)

    # abrev. only applied to orchids
    if app == 'orchidaceae':
        genus_name, search_string = expand_genus_name(search_string)

    search_string = clean_search_string(search_string)
    if ' ' not in search_string:
        # single word could be genus
        matched_genus = Genus.objects.filter(Q(genus__istartswith=search_string) | Q(abrev__istartswith=search_string))
        if matched_genus:
            #  Done if found a matching genus.
            context = {'search_string': search_string, 'matched_genus': matched_genus,
                       # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                       'role': role, 'path': path, 'full_path': full_path,
                       'app': app,}
            return render(request, "search/search_results.html", context)

    # Search string more than one word
    match_spc_list = Species.objects.filter(binomial__icontains=search_string)
    # If no match found (probably wrong genus), drop the first word (genus) and match again
    if not match_spc_list:
        words = search_string.split()
        species_name = ' '.join(words[1:]) if len(words) > 1 else '' # Must already be > 1
        if species_name:
            match_spc_list = Species.objects.filter(binomial__icontains=species_name)


    write_output(request, search_string)
    context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'genus_total': len(genus_list), 'app': app,
               # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'role': role, 'path': path, 'full_path': full_path}
    return render(request, "search/search_results.html", context)


# Search common name
def search_name(request, app=None):
    # Assume the entire string is either species or hybrid grex name.
    # Absolutely no genus allowed in here.
    # Get search term
    global Model

    role = getRole(request)
    if not app:
        app = request.GET.get('app', 'orchidaceae')
    species_list = []
    req_search_string = request.GET.get('search_string', '').strip()
    if not req_search_string:
        req_search_string = request.POST.get('search_string', '').strip()
    if not req_search_string:
        context = {'search_string': req_search_string, 'app': app, 'role': role}
        return render(request, "search/search_name.html", context)


    search_string = req_search_string.rstrip('s')
    search_string = clean_search_string(search_string)
    search_string_clean = clean_name(search_string)

    # Switch from search scientific name
    if not search_string or search_string == '':
        search_string = request.GET.get('search_string', '').strip()

    Species = apps.get_model(app, 'Species')
    if app == 'orchidaceae':
        species_list = Species.objects.filter(species__icontains=search_string)
    else:
        species_list = Species.objects.filter(Q(accepted__common_name__icontains=search_string) | Q(accepted__common_name_search__icontains=search_string_clean))

    context = {'species_list': species_list,
               'search_string': req_search_string, 'app': app, 'role': role,}
    write_output(request, str(search_string))
    return render(request, "search/search_name.html", context)


