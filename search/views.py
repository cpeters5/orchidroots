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
    exact_match = []
    found_species = []
    matched_species = []
    matched_genus = []
    full_path = request.path
    path = 'summary'
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'

    # Get search string
    search_string = request.GET.get('search_string', '').strip()

    if not search_string:
        context = {'search_string': search_string,'app': app, 'role': role}
        return render(request, "search/search_results.html", context)

    search_string = clean_search_string(search_string)
    if ' ' not in search_string:
        # single word could be genus
        matched_genus = Genus.objects.filter(genus=search_string)
        #  Get exact matched species
        found_species = Species.objects.filter(species=search_string).order_by('binomial')
        # Get partial matched species (only if lenght > 2)
        if len(search_string) < 4:
            matched_species = Species.objects.filter(species__istartswith=search_string).exclude(species=search_string).order_by('binomial')
        elif len(search_string) > 3:
            matched_species = Species.objects.filter(species__icontains=search_string).exclude(species=search_string).order_by('binomial')
        context = {'search_string': search_string, 'matched_genus': matched_genus,
                   'matched_species': matched_species, 'found_species': found_species,
                   'role': role, 'path': path, 'full_path': full_path,
                   'app': app,}
        return render(request, "search/search_results.html", context)

    # Search string more than one word
    # Find genus matching first word
    words = search_string.split()
    search_genus = words[0]
    words_tail = words[1:]
    search_tail = ' '.join(words_tail)
    matched_genus = Genus.objects.filter(genus=search_genus)

    # Find binomial matching entire string
    exact_match = Species.objects.filter(binomial__istartswith=search_string).order_by('binomial')

    # Assume genus is not given in the string
    found_species1 = Species.objects.filter(species=search_string).order_by('binomial')

    # Assume the first word is genus
    #  Reject species string < 3
    if len(search_tail) > 1:
        found_species2 = Species.objects.filter(species=search_tail).exclude(binomial__istartswith=search_string).order_by('binomial')
        if len(search_tail) < 4:
            matched_species = Species.objects.filter(species__istartswith=search_tail).exclude(species=search_tail).exclude(binomial__istartswith=search_string).order_by('binomial')
        elif len(search_tail) > 3:
            matched_species = Species.objects.filter(species__icontains=search_tail).exclude(species=search_tail).exclude(binomial__istartswith=search_string).order_by('binomial')
    found_species = found_species1|found_species2
    
    write_output(request, search_string)
    context = {'search_string': search_string, 'matched_species': matched_species, 'found_species': found_species,
               'matched_genus':matched_genus, 'exact_match': exact_match,
               'app': app,
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


