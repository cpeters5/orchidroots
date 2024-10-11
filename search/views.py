from django.shortcuts import render, redirect
from django.db import connection
from django.db.models import Case, When, Value, Subquery, OuterRef, Q, CharField
from django.db.models.functions import Replace
from django.apps import apps
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from itertools import chain
from fuzzywuzzy import fuzz, process
from common.models import Family, Subfamily, Tribe, Subtribe, CommonName, Binomial, SpellChecker
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages, SpcImages
from accounts.models import User, Photographer
from utils.views import write_output, getRole, clean_search_string, expand_genus_name, Replace, MultiReplace, RemoveSpaces, clean_query, clean_name
from utils import config
import unicodedata

applications = config.applications
app_descriptions =config.app_descriptions
big_genera = config.big_genera
alpha_list = config.alpha_list


def get_binomial_search_string(search_string):
    if ' ' not in search_string:
        genus_string = search_string
    else:
        (genus_string, rest) = search_string.split(' ', 1)

    abrev = genus_string if genus_string.endswith('.') else genus_string + '.'

    # get genus obj
    genera = Binomial.objects.filter(Q(genus=genus_string) | Q(abrev=abrev))
    if len(genera) > 0:
        genus = genera[0]
    else:
        genus = ''
        # It could be an abreviation
        genus_obj = Genus.objects.filter(abrev=genus_string)
        if genus_obj:
            # genus = genus_obj[0]
        # if len(genus_obj) > 0:
            genus = genus_obj[0]
            abrev = genus_string if genus_string.endswith('.') else genus_string + '.'
    full_search_string = search_string
    if abrev != '':
        full_search_string = search_string.replace(abrev, genus.genus)
    return (genus, full_search_string)


def get_full_search_string(Genus, search_string):

    if ' ' not in search_string:
        genus_string = search_string
    else:
        (genus_string, rest) = search_string.split(' ', 1)
    try:
        genus = Genus.objects.get(genus=genus_string)
    except Genus.DoesNotExist:
        genus = ''
        # It could be an abreviation
        # TODO: This block will be replaced with spellchecker lookup (which include abrev)
        this_genus_string = genus_string
        if not this_genus_string.endswith('.'):
            this_genus_string += '.'
        abrevs = Genus.objects.filter(abrev=this_genus_string)

        if len(abrevs) > 0:
            genus = abrevs[0]
            replacement = genus.genus
            search_string = search_string.replace(genus_string, replacement)

    return (genus, search_string)

# Prepare query string for search in common.Binomial
# remove all occurrences of blanks, white spaces, single and double quotes, ., -, and expand genus abreviation if exists

# Fulltext common_name.common_name
def query_fulltext_with_score(search_string, search_string1, search_string2, score_limit, max_rec, ):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT taxon_id, application, level, MATCH(common_name) AGAINST (%s IN BOOLEAN MODE) AS score
            FROM common_commonname
            WHERE MATCH(common_name) AGAINST (%s IN BOOLEAN MODE)
              AND MATCH(common_name) AGAINST (%s IN BOOLEAN MODE) > %s

            ORDER BY score DESC
            LIMIT %s
        """, [search_string, search_string1, search_string2, score_limit, max_rec])
        results = [{'row': row, 'score': row[-1]} for row in cursor.fetchall()]
        # results = []
        # for row in cursor.fetchall():
        #     result_dict = {
        #         'pid': row[0],
        #         'application': row[1],
        #         'level': row[2],
        #         'score': row[3]
        #     }
        #
        #     results.append(result_dict)

    return results

# Fulltext common.binomial.species
def query_commonname_binomial(search_term, search_term1, search_term2, min_score, max_rec):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT taxon_id, application, level, MATCH(species) AGAINST (%s IN BOOLEAN MODE) AS score
            FROM common_binomial
            WHERE MATCH(species) AGAINST (%s IN BOOLEAN MODE)
              AND MATCH(species) AGAINST (%s IN BOOLEAN MODE) > %s
            ORDER BY score DESC
            LIMIT %s
        """, [search_term, search_term1, search_term2, min_score, max_rec])
        # result_list = cursor.fetchall()
        result_list = []
        for row in cursor.fetchall():
            result_dict = {
                'pid': row[0],
                'application': row[1],
                'level': row[2],
                'score': row[3]
            }
            result_list.append(result_dict)
    return result_list

# Full text common.commonname.common_name
def query_commonname_commonname(search_string, search_string1, search_string2, min_score, max_rec, ):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT taxon_id, application, level, MATCH(common_name) AGAINST (%s IN BOOLEAN MODE) AS score
            FROM common_commonname
            WHERE MATCH(common_name) AGAINST (%s IN BOOLEAN MODE)
              AND MATCH(common_name) AGAINST (%s IN BOOLEAN MODE) > %s
              AND (level = 'Accepted' OR level = 'Hybrid')
            ORDER BY score DESC
            LIMIT %s
        """, [search_string, search_string1, search_string2, min_score, max_rec])
        # results = [{'row': row, 'score': row[-1]} for row in cursor.fetchall()]
        result_list = []
        for row in cursor.fetchall():
            result_dict = {
                'pid': row[0],
                'application': row[1],
                'level': row[2],
                'score': row[3]
            }
            result_list.append(result_dict)

    return result_list

# Common.commonname.common_name - other applications
# def query_commonname_binomial(search_string, search_string1, search_string2, score_limit, max_rec, ):
def query_binomial_non_orchid(search_string, search_string1, search_string2, min_score, max_rec, ):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT *, MATCH(common_name) AGAINST (%s IN BOOLEAN MODE) AS score
            FROM common_commonname
            WHERE MATCH(common_name) AGAINST (%s IN BOOLEAN MODE)
              AND MATCH(common_name) AGAINST (%s IN BOOLEAN MODE) > %s
              AND (level = 'Accepted' OR level = 'Hybrid')
              AND application <> 'orchidaceae'
            ORDER BY score DESC
            LIMIT %s
        """, [search_string, search_string1, search_string2, min_score, max_rec])
        result_list = [{'row': row, 'score': row[-1]} for row in cursor.fetchall()]
        # result_list = []
        # for row in cursor.fetchall():
        #     result_dict = {
        #         'pid': row[0],
        #         'application': row[1],
        #         'level': row[2],
        #         'score': row[3]
        #     }
        #
        #     result_list.append(result_dict)

    return result_list


# Fulltext orchidaceae_species.species
# Can also use common.binomial
def query_orchidaceae_species(search_term, search_term1, search_term2, min_score, max_rec):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT pid, lower(family), 'Accepted', MATCH(species) AGAINST (%s IN BOOLEAN MODE) AS score
            FROM orchidaceae_species
            WHERE MATCH(species) AGAINST (%s IN BOOLEAN MODE)
              AND MATCH(species) AGAINST (%s IN BOOLEAN MODE) > %s
            ORDER BY score DESC
            LIMIT %s
        """, [search_term, search_term1, search_term2, min_score, max_rec])
        # result_list = [{'row': row, 'score': row[-1]} for row in cursor.fetchall()]
        # result_list = cursor.fetchall()
        result_list = []
        for row in cursor.fetchall():
            result_dict = {
                'pid': row[0],
                'application': row[1],
                'level': row[2],
                'score': row[3]
            }

            result_list.append(result_dict)
    return result_list

# Fulltext orchidaceae_species.binomial
# Can also use common.binomial
def query_orchidaceae_binomial(search_term, search_term1, search_term2, min_score, max_rec):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT pid, lower(family), 'Accepted', MATCH(binomial) AGAINST (%s IN BOOLEAN MODE) AS score
            FROM orchidaceae_species
            WHERE MATCH(binomial) AGAINST (%s IN BOOLEAN MODE)
              AND MATCH(binomial) AGAINST (%s IN BOOLEAN MODE) > %s
            ORDER BY score DESC
            LIMIT %s
        """, [search_term, search_term1, search_term2, min_score, max_rec])
        # result_list = [{'row': row, 'score': row[-1]} for row in cursor.fetchall()]
        # result_list = cursor.fetchall()
        result_list = []
        for row in cursor.fetchall():
            result_dict = {
                'pid': row[0],
                'application': row[1],
                'level': row[2],
                'score': row[3]
            }

            result_list.append(result_dict)

    return result_list



def match_fulltext(search_string):
    # Firest match orchid species  (most popular)
    search_list1 = query_orchidaceae_species(search_string, search_string,  search_string, min_score=20, max_rec=5)

    # Then match orchid binomial
    search_list2 = query_orchidaceae_binomial(search_string, search_string, search_string, min_score=5, max_rec=5)
    # Then match common name

    # Then search non-orchids common_name
    search_list3 = query_commonname_binomial(search_string, search_string, search_string, min_score=5, max_rec=5)

    # Then search non-orchids binomial
    search_list4 = query_commonname_commonname(search_string, search_string, search_string, min_score=5, max_rec=5)

    # Get a combined list
    return search_list1, search_list2, search_list3, search_list4


def match_orchid(search_string):
    # First match genus
    perfect_querysets = []  # Use this to collect querysets
    Species = apps.get_model('orchidaceae', 'Species')
    if len(search_string.split()) >= 2:
        gen_str, spc_str = search_string.split(maxsplit=1)
        spc_list = Species.objects.filter(Q(binomial=search_string) |
                                          Q(species=search_string) |
                                          Q(species=spc_str)
                                          )
    else:
        spc_list = Species.objects.filter(Q(binomial=search_string) |
                                          Q(species=search_string)
                                          )


    if spc_list.exists():
        perfect_querysets.append(spc_list)

    # Now, merge all collected querysets
    if perfect_querysets:
        merged_queryset = perfect_querysets[0]
        for queryset in perfect_querysets[1:]:
            merged_queryset = merged_queryset | queryset
    else:
        merged_queryset = Species.objects.none()  # or any model to create an empty queryset

    # Second get partial matches, ignoring perfect matches found above.
    startswith_matches = []
    for app in applications:
        if app == 'orchidaceae':
            Species = apps.get_model(app, 'Species')
            # Using a queryset directly with the filter and exclude clauses
            spc_list = Species.objects.filter(
                Q(binomial__istartswith=search_string) | Q(species__istartswith=search_string)
            ).exclude(Q(binomial=search_string) | Q(species=search_string))
            if spc_list.exists():
                startswith_matches.append(spc_list)

    # Now, merge all collected querysets
    if startswith_matches:
        startswith_queryset = startswith_matches[0]
        for queryset in startswith_matches[1:]:
            startswith_queryset = startswith_queryset | queryset
    else:
        startswith_queryset = Species.objects.none()  # or any model to create an empty queryset


    # Extend combined_list with the queryset converted to a list if not empty
    combined_results = list(chain(merged_queryset, startswith_queryset))
    return combined_results


def match_collapsed(search_string):
    combined_list = []
    Binomial = apps.get_model('common', 'Binomial')
    for app in applications:
        spc_list = Binomial.objects.filter(Q(binomial_search__istartswith=search_string) | Q(species__istartswith=search_string))
        if spc_list:
            combined_list.extend(list(spc_list))
    return list(combined_list)


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
        app = request.GET.get('app', '')

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
    Accepted = apps.get_model(app, 'Accepted')
    if app == 'orchidaceae':
        # Treat grex name as a search_string
        pid_list = Species.objects.filter(species__icontains=search_string).values_list('pid', flat=True)
    else:
        pid_list = Accepted.objects.filter(Q(common_name__icontains=search_string) | Q(common_name_search__icontains=search_string_clean)).values_list('pid', flat=True)
    if pid_list:
        species_list = Species.objects.filter(pid__in=pid_list)

    context = {'species_list': species_list,
               'search_string': req_search_string, 'app': app, 'role': role,}
    write_output(request, str(search_string))
    return render(request, "search/search_name.html", context)


