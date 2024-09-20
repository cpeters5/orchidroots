from django.shortcuts import render, redirect
from django.db import connection
from django.db.models import Case, When, Value, Subquery, OuterRef, Q, CharField
from django.db.models.functions import Replace
from django.apps import apps
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from itertools import chain
from fuzzywuzzy import fuzz, process
from common.models import Family, Subfamily, Tribe, Subtribe, CommonName, Binomial, SpellChecker
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages, SpcImages
from accounts.models import User, Photographer
from utils.views import write_output, getRole, clean_search_string, Replace, MultiReplace, RemoveSpaces, clean_query, clean_name
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


def search(request):
    # search.search requested from the navbar and home page.
    # If family = Orchidaceae, or unknown family, redirect to search.search_orchidaceae.

    # Get genus from the first word in search string.
    # If found, get family and application
    # From list of genera, find matching species from the rest of search string.
    # if no results, redirect to common name search
    role = getRole(request)
    search_list = []
    genus_list = []
    match_spc_list = []
    full_path = request.path
    path = 'information'
    full_search_string = ''
    other_genus_spc = ''
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'

    selected_app = request.GET.get('app', '')

    # Get search string
    search = request.GET.get('search', '')      #handle legacy case
    if search:
        search_string = search
    else:
        search_string = request.GET.get('search_string', '').strip()
    if 'search_string' in request.POST:
        search_string = request.POST['search_string'].strip()
    if not search_string:
        return redirect(request.META.get('HTTP_REFERER', '/'))



    search_string = clean_search_string(search_string)

    # If no search string given, return
    if not search_string or search_string == '':
        message = 'Empty search term'
        return HttpResponse(message)

    if not selected_app or selected_app == 'orchidaceae':
        Genus = apps.get_model('orchidaceae', 'Genus')
        if ' ' not in search_string:
            try:
                matched_genus = Genus.objects.get(genus=search_string)
            except Genus.DoesNotExist:
                matched_genus = ''
            if matched_genus:
                context = {'search_string': search_string, 'matched_genus': matched_genus,
                           # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                           'role': role, 'path': path, 'full_path': full_path}
                return render(request, "search/search_orchidaceae.html", context)
            else:
                genus_list = Genus.objects.filter(genus__istartswith=search_string).annotate(
                    img_file=Case(
                        When(Q(type='species'), then=Subquery(
                            SpcImages.objects.filter(gen=OuterRef('pk'), rank__lt=7)
                            .order_by('-rank', '-quality')
                            .values('image_file')[:1]
                        )),
                        When(Q(type='hybrid'), then=Subquery(
                            HybImages.objects.filter(gen=OuterRef('pk'), rank__lt=7)
                            .order_by('-rank', '-quality')
                            .values('image_file')[:1]
                        )),
                        default=None
                    ),
                ).annotate(
                    img_dir=Case(
                        When(type='species', then=Value('utils/thumbs/species/')),
                        When(type='hybrid', then=Value('utils/thumbs/hybrid/')),
                        default=Value(''),
                        output_field=CharField()
                    )
                )
                if genus_list:
                    context = {'search_string': search_string, 'genus_list': genus_list,
                               # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                               'role': role, 'path': path, 'full_path': full_path}
                    return render(request, "search/search_orchidaceae.html", context)

        #
        # Try the obvious first! Put basic query against Species.binomial and species.species here
        # First try straight forward matching (binoial and species)
        match_spc_list = match_orchid(search_string)
        if not match_spc_list:
            genus, full_search_string = get_full_search_string(Genus, search_string)
            match_spc_list = match_orchid(full_search_string)

        if match_spc_list:
            write_output(request, search_string)
            context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'genus_total': len(genus_list),
                       # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                       'role': role, 'path': path, 'full_path': full_path}
            return render(request, "search/search_orchidaceae.html", context)



    # Go through each application (!= orchidaceae) one by one.
    elif selected_app in applications:
        # If app is valid, collect all matching genera in each app
        Genus = apps.get_model(selected_app, 'Genus')
        # Identify genus and expand genus abreviation if exists in search_string
        genus, full_search_string = get_full_search_string(Genus, search_string)
        spc_string = clean_name(full_search_string)
        # If genus belongs to orchid famil, redirect to orchidaceae search
        if isinstance(genus, Genus):
            if genus.family.family == 'orchidaceae':
                url = "%s?search_string=%s&genus=%s" % (reverse('search:search_orchidaceae'), search_string, genus.genus)
                return HttpResponseRedirect(url)
            genus_list.append(genus)
            family = genus.family
            Species = apps.get_model(family.application, 'Species')
            this_match_spc_list = Species.objects.filter(genus=genus).filter(binomial__icontains=full_search_string)
            if not this_match_spc_list:
                # this_match_spc_list = Species.objects.filter(binomial_search=spc_string)
                # this_match_spc_list = query_fulltext_with_score(spc_string, spc_string, spc_string, score_limit, 20)
                this_match_spc_list = query_orchidaceae_binomial_old(spc_string, spc_string, spc_string, score_limit, 20)
            # if not this_match_spc_list:
            #     this_match_spc_list = Species.objects.filter(binomial_search=spc_string)

            match_spc_list = list(chain(match_spc_list, this_match_spc_list))
    else:
        # if requested application is empty or unknown, look for genus in each app in Applications
        for app in applications:
            Genus = apps.get_model(app, 'Genus')
            genus, full_search_string = get_full_search_string(Genus, search_string)

            if genus and genus.family.family == 'Orchidaceae':
                url = "%s?search_string=%s&genus=%s" % (reverse('search:search_orchidaceae'), search_string, genus.genus)
                return HttpResponseRedirect(url)
            if isinstance(genus, Genus) and genus != '':
                # List of genera found in each app (except orchidaceae).
                # We cannot assume genus is unique across all app
                genus_list.append(genus)
                family = genus.family
                Species = apps.get_model(family.application, 'Species')
                this_match_spc_list = Species.objects.filter(genus=genus).filter(binomial__icontains=full_search_string)
                match_spc_list = list(chain(match_spc_list, this_match_spc_list))
    # Now try to identify species from each word in the search string

    # Not found yet. Dig deeper
    if match_spc_list:
        context = {'search_string': full_search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                   'other_genus_spc': other_genus_spc,
                   'role': role,
                   'path': path, 'full_path': full_path
                   }
        return render(request, "search/search_results.html", context)
    else:
        if search_string.split()[0]:
            search_list = search_string.split()

        if genus_list:
            # Get species for each genus in the list
            for genus in genus_list:
                if ' ' not in search_string:
                    continue
                family = genus.family
                Species = apps.get_model(family.application, 'Species')
                this_match_spc_list = Species.objects.filter(genus=genus).filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
                match_spc_list = list(chain(match_spc_list, this_match_spc_list))
            # Incase no species found where search_string is more than one word, then look at other genus
            if genus_list and not match_spc_list and ' ' in search_string:
                for genus in genus_list:
                    if ' ' not in search_string:
                        continue
                    family = genus.family
                    Species = apps.get_model(family.application, 'Species')
                    this_match_spc_list = Species.objects.filter(genus=genus).filter(
                        Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
                    match_spc_list = list(chain(match_spc_list, this_match_spc_list))
                    other_genus_spc = Species.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))

            context = {'search_string': full_search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'other_genus_spc': other_genus_spc,
                       'role': role,
                       'path': path, 'full_path': full_path
                       }
            return render(request, "search/search_results.html", context)

    # unknown genus, probably misspelled, or search string didn't include genus.
    # Forget genus and match species instead

    if selected_app in applications:
        Species = apps.get_model(selected_app, 'Species')
        # Look foir matching binomial with entire search string OR matchind species with elements in search_list
        this_spc_list = Species.objects.filter(
            Q(binomial__icontains=full_search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
        other_genus_spc = list(this_spc_list)
        context = {'search_string': full_search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                   'other_genus_spc': other_genus_spc, 'role': role, 'selected_app': selected_app,
                   'path': path, 'full_path': full_path
                   }
        return render(request, "search/search_species.html", context)
    else:
        # When all else fails, send it to common nma e search?
        url = "%s?commonname=%s" % (
        reverse('search:search_name'), search_string)
        return HttpResponseRedirect(url)
        # for app in applications:
        #     Species = apps.get_model(app, 'Species')
        #     this_spc_list = Species.objects.filter(
        #             Q(binomial__icontains=full_search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
        #     other_genus_spc = list(chain(other_genus_spc, this_spc_list))


def xsearch(request):
    # search.search requested from the navbar and home page.
    # If family = Orchidaceae, or unknown family, redirect to search.search_orchidaceae.

    # Get genus from the first word in search string.
    # If found, get family and application
    # From list of genera, find matching species from the rest of search string.
    # if no results, redirect to common name search
    role = getRole(request)
    search_list = []
    genus_list = []
    match_spc_list = []
    full_path = request.path
    path = 'information'
    full_search_string = ''
    other_genus_spc = ''
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'

    selected_app = request.GET.get('app', '')
    if selected_app.lower() == 'all':
        selected_app = ''

    # Get search string
    search = request.GET.get('search', '')      #handle legacy case

    if search:
        search_string = search
    else:
        search_string = request.GET.get('search_string', '').strip()
    if 'search_string' in request.POST:
        search_string = request.POST['search_string'].strip()

    search_string = clean_search_string(search_string)

    search_string_collapsed = clean_search_string(search_string)

    # If no search string given, return
    if not search_string or search_string == '':
        message = 'Empty search term'
        return HttpResponse(message)


    if not selected_app:
        # Try the most popular first: orchids
        # First try straight forward matching (binoial and species)
        Genus = apps.get_model('orchidaceae', 'Genus')
        match_spc_list = match_orchid(search_string)
        if not match_spc_list:
            genus, full_search_string = get_full_search_string(Genus, search_string)
            match_spc_list = match_orchid(full_search_string)
        if not match_spc_list:
            words = full_search_string.split()
            if words:
                words[0] = ''
            species = ' '.join(words)
            match_spc_list = match_orchid(species)




        if match_spc_list:
            write_output(request, search_string)
            context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'genus_total': len(genus_list),
                       # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                       'role': role, 'path': path, 'full_path': full_path}
            return render(request, "search/search_orchidaceae.html", context)

        # Second try word matching common.binomial and common.common_name
        list1, list2, list3, list4 = match_fulltext(search_string)
        combined_list = []
        for app in applications:
            Species = apps.get_model(app, 'Species')
            if app == 'orchidaceae':
                this_list = [d for d in list1 + list2 if d['application'] == app]
            else:
                this_list = [d for d in list3 + list4 if d['application'] == app]
            pid_list = [t['pid'] for t in this_list]
            spc = Species.objects.filter(pid__in=pid_list)
            if spc:
                combined_list.extend(list(spc))
        match_spc_list = list(combined_list)
        if match_spc_list:
            write_output(request, search_string)
            context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'genus_total': len(genus_list),
                       # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                       'role': role, 'path': path, 'full_path': full_path}
            return render(request, "search/search_orchidaceae.html", context)

        #  Third, handle missing or unplaced space characters
        match_spc_list = match_collapsed(search_string)
        if match_spc_list:
            write_output(request, search_string)
            context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'genus_total': len(genus_list),
                       # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                       'role': role, 'path': path, 'full_path': full_path}
            return render(request, "search/search_orchidaceae.html", context)




    # Common search didn't find any result
    # If app is requested, will  only search in the requested app space.
    elif selected_app in applications:
        # If app is valid, collect all matching genera in each app
        Genus = apps.get_model(selected_app, 'Genus')
        # Identify genus and expand genus abreviation if exists in search_string
        genus, full_search_string = get_full_search_string(Genus, search_string)
        spc_string = clean_name(full_search_string)
        # If genus belongs to orchid famil, redirect to orchidaceae search
        if isinstance(genus, Genus):
            # For orchid, goto search_orchidaceae
            if genus.family.family == 'orchidaceae':
                url = "%s?search_string=%s&genus=%s" % (reverse('search:search_orchidaceae'), search_string, genus.genus)
                return HttpResponseRedirect(url)
            # For other app
            genus_list.append(genus)
            family = genus.family
            Species = apps.get_model(family.application, 'Species')
            # Do simple check first, against Species class.
            this_match_spc_list = Species.objects.filter(genus=genus).filter(binomial__icontains=full_search_string)
            # If no result, try Commonname class (both binomial and common_name)
            if not this_match_spc_list:
                # this_match_spc_list = Species.objects.filter(binomial_search=spc_string)
                # this_match_spc_list = query_fulltext_with_score(spc_string, spc_string, spc_string, score_limit, 20)
                spc_string = spc_string.replace(abrev, genus.genus)
                this_match_spc_list = query_commonname_binomial(spc_string, spc_string, spc_string, 20, 20)
# ERROR.  Elements in this list are of different app;.  Must loop through each app
                if this_match_spc_list:
                    pid_list = [t[0] for t in this_match_spc_list]
                    match_spc_list = Species.objects.filter(pid__in=pid_list)
            match_spc_list = list(chain(match_spc_list, this_match_spc_list))
    else:
        # if application is not requested, then search all other app spaces.
        # Identify genus from the first word in the search string
        for app in applications:
            Genus = apps.get_model(app, 'Genus')
            Species = apps.get_model(app, 'Species')
            genus, full_search_string = get_full_search_string(Genus, search_string)
            # If genus is identified as orchid, send it to search_orchid
            if genus and genus.family.family == 'Orchidaceae':
                url = "%s?search_string=%s&genus=%s" % (reverse('search:search_orchidaceae'), search_string, genus.genus)
                return HttpResponseRedirect(url)
            if isinstance(genus, Genus) and genus != '':
                # List of genera found in each app (except orchidaceae).
                # We cannot assume genus is unique across all app
                genus_list.append(genus)
                family = genus.family
                Species = apps.get_model(family.application, 'Species')
                this_match_spc_list = Species.objects.filter(genus=genus).filter(binomial__icontains=full_search_string)
                match_spc_list = list(chain(match_spc_list, this_match_spc_list))

    if len(match_spc_list) == 0:
        this_match_spc_list = query_binomial_non_orchid(search_string, search_string, search_string, 10, 20)
        for x in this_match_spc_list:
            # this_mathch_spc_list contain only Accepted and Hybrid level
            Species = apps.get_model(x['application'], 'Species')
            try:
                xobj = Species.objects.get(pk=x['pid'])
            except Model.DoesNotExist:
                break
            img = xobj.get_best_img()
            spc = {'pid': xobj.pid, 'binomial': xobj.binomial, 'type': xobj.type, 'score': x['score'],
                   'family': xobj.family, 'status': xobj.status, 'level': 'Accepted'}
            if xobj.status == 'synonym':
                spc['acc'] = xobj.getAccepted()
            elif xobj.type == 'species':
                spc['name'] = xobj.accepted.common_name
            if img:
                spc['img_pid'] = img.pid.pid
                spc['image_dir'] = img.thumb_dir
                spc['image_file'] = img.image_file
            match_spc_list.append(spc)

    # Check common name also (who knows? search term might be common name)



    if match_spc_list:
        write_output(request, search_string)
        context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                   'genus_total': len(genus_list),
                   # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
                   'role': role, 'path': path, 'full_path': full_path}
        return render(request, "search/search_species.html", context)


    # # Found one already!
    # if len(match_spc_list) > 0:
    #     context = {'search_string': full_search_string, 'genus_list': genus_list,
    #                'match_spc_list': match_spc_list,
    #                'other_genus_spc': other_genus_spc,
    #                'role': role,
    #                'path': path, 'full_path': full_path
    #                }
    #     return render(request, "search/search_name.html", context)

    if search_string.split()[0]:
        search_list = search_string.split()

    if genus_list:
        # Get species for each genus in the list
        for genus in genus_list:
            if ' ' not in search_string:
                continue
            family = genus.family
            Species = apps.get_model(family.application, 'Species')
            this_match_spc_list = Species.objects.filter(genus=genus).filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
            match_spc_list = list(chain(match_spc_list, this_match_spc_list))
        # Incase no species found where search_string is more than one word, then (misspelled genus?)
        # look for species in other genus, use the common_binomial class
        if genus_list and not match_spc_list and ' ' in search_string:
            this_match_spc_list = query_commonname_binomial(spc_string, spc_string, spc_string, score_limit, 20)
            for x in this_match_spc_list:
                if x['level'] == 'Family':
                    Model = apps.get_model('common', 'Family')
                elif x['level'] == 'Genus':
                    Model = apps.get_model(x['application'], 'Genus')
                elif x['level'] in ('Accepted', 'Hybrid'):
                    Model = apps.get_model(x['application'], 'Species')
                try:
                    xobj = Model.objects.get(pk=x['pid'])
                except Model.DoesNotExist:
                    break
                fam, gen, spc = {}, {}, {}
                img = xobj.get_best_img()
                if x['level'] == 'Family':
                    fam = {'family': xobj.family, 'name': xobj.common_name, 'score': x['score'],
                           'status': xobj.status}
                    if img:
                        fam['img_pid'] = img.pid.pid
                        fam['image_dir'] = img.thumb_dir
                        fam['image_file'] = img.image_file
                    family_list.append(fam)
                elif x['level'] == 'Genus':
                    gen = {'pid': xobj.pid, 'genus': xobj.genus, 'name': xobj.common_name, 'score': x['score'],
                           'status': xobj.status}
                    if img:
                        gen['img_pid'] = img.pid.pid
                        gen['image_dir'] = img.thumb_dir
                        gen['image_file'] = img.image_file
                    genus_list.append(gen)
                elif x['level'] in ('Accepted', 'Hybrid'):
                    spc = {'pid': xobj.pid, 'binomial': xobj.binomial, 'type': xobj.type, 'score': x['score'],
                           'family': xobj.family, 'status': xobj.status, 'level': 'Accepted'}
                    if xobj.status == 'synonym':
                        spc['acc'] = xobj.getAccepted()
                    elif xobj.type == 'species':
                        spc['name'] = xobj.accepted.common_name
                    if img:
                        spc['img_pid'] = img.pid.pid
                        spc['image_dir'] = img.thumb_dir
                        spc['image_file'] = img.image_file
                    species_list.append(spc)




            for genus in genus_list:
                if ' ' not in search_string:
                    continue
                family = genus.family
                Species = apps.get_model(family.application, 'Species')
                this_match_spc_list = Species.objects.filter(genus=genus).filter(
                    Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
                match_spc_list = list(chain(match_spc_list, this_match_spc_list))
                other_genus_spc = Species.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))

        context = {'search_string': full_search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                   'other_genus_spc': other_genus_spc,
                   'role': role,
                   'path': path, 'full_path': full_path
                   }
        return render(request, "search/search_results.html", context)

    # unknown genus, probably misspelled, or search string didn't include genus.
    # Forget genus and match species instead

    if selected_app in applications:
        Species = apps.get_model(selected_app, 'Species')
        # Look foir matching binomial with entire search string OR matchind species with elements in search_list
        this_spc_list = Species.objects.filter(
            Q(binomial__icontains=full_search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
        other_genus_spc = list(this_spc_list)
        context = {'search_string': full_search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                   'other_genus_spc': other_genus_spc, 'role': role, 'selected_app': selected_app,
                   'path': path, 'full_path': full_path
                   }
        return render(request, "search/search_species.html", context)
    else:
        # When all else fails, send it to common nma e search?
        url = "%s?commonname=%s" % (
        reverse('search:search_name'), search_string)
        return HttpResponseRedirect(url)
        # for app in applications:
        #     Species = apps.get_model(app, 'Species')
        #     this_spc_list = Species.objects.filter(
        #             Q(binomial__icontains=full_search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
        #     other_genus_spc = list(chain(other_genus_spc, this_spc_list))


# Uses commin.Binomial
def search_binomial(request):
    # Not in used
    query = []
    from os.path import join
    import jellyfish
    from common.models import Binomial
    # Get teh search string
    search_string = request.GET.get('query', '')
    # Clean search string. Get genus if exists
    search_genus, search_string = clean_query(search_string)
    if search_genus != '':
        # 1. Just match the requested string
        this_query = ''
        results = Binomial.objects.search(query)
        if ' ' in query:
            (req_genus, rest) = query.split(' ', 1)
            if not req_genus.endswith('.'):
                req_genus += '.'
                abrev_obj = Genus.objects.filter(abrev=req_genus)
            if len(abrev_obj) > 0:
                replacement = abrev_obj.first().genus
                query = query.split()
                abrev = query[0]
                query = " ".join(query)
                query = query.replace(abrev, replacement)
            else:
                req_genus.strip('.')

        results = Binomial.objects.search(query)
        jaro_winkler_similarities = {s: jellyfish.jaro_winkler_similarity(query, s.binomial) for s in results}
        str_with_scores_dicts = [{'match': s, 'score': jaro_winkler_similarities[s]} for s in results]
        str_with_scores_dicts.sort(key=lambda x: x['score'], reverse=True)
    else:
        str_with_scores_dicts = []
    result_list = []
    for i in range(10):
        if i == len(str_with_scores_dicts):
            break
        result_list.append(str_with_scores_dicts[i])

    role = getRole(request)
    context = {'result_list': result_list, 'search_string': search_string, 'role': role }

    return render(request, "search/search_binomial.html", context)


# Called from search when genus can't be identified
# We know that genus, application and family cannot be identified
def search_species(request):
    genus_list = []
    search_list = []
    species_list = []
    match_spc_list = []
    full_path = request.path
    role = getRole(request)

    search_string = request.GET.get('search_string', None)
    if search_string and search_string.split()[0]:
        search_list = search_string.split()
    species_list = []
    for app in applications:
        Species = apps.get_model(app, 'Species')
        this_species_list = Species.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
        if this_species_list:
            if not species_list:
                species_list = (this_species_list)
            else:
                species_list = (species_list).union(this_species_list)

        match_spc_list = species_list
    if match_spc_list:
        match_spc_list = match_spc_list.order_by('family', 'binomial')

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    path = 'information'
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'

    write_output(request, search_string)
    context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'genus_total': len(genus_list),
               # 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'role': role, 'path': path, 'full_path': full_path}
    return render(request, "search/search_species.html", context)


def search_name(request):
    # Assume the entire string is either species or hybrid grex name.
    # Absolutely no genus allowed in here.
    # Get search term
    global Model

    role = getRole(request)
    selected_app = request.POST.get('selected_app', '')
    if not selected_app:
        selected_app = request.GET.get('selected_app', '')

    commonname = request.GET.get('commonname', '').strip()
    if not commonname:
        commonname = request.POST.get('commonname', '').strip()
    commonname = commonname.rstrip('s')
    commonname = clean_search_string(commonname)
    commonname_clean = clean_name(commonname)

    if not commonname or commonname == '':
        context = {'role': role, }
        return render(request, "search/search_name.html", context)

    species_list, genus_list, family_list = [], [], []
    if selected_app:
        Species = apps.get_model(selected_app, 'Species')
        Accepted = apps.get_model(selected_app, 'Accepted')
        if selected_app == 'orchidaceae':
            # Treat grex name as a commonname
            pid_list = Species.objects.filter(species__icontains=commonname).values_list('pid', flat=True)
        else:
            pid_list = Accepted.objects.filter(Q(common_name__icontains=commonname) | Q(common_name_search__icontains=commonname_clean)).values_list('pid', flat=True)
        if pid_list:
            species_list = Species.objects.filter(pid__in=pid_list)
    else:
        combined_list = []
        for app in applications:
            Species = apps.get_model(app, 'Species')
            Accepted = apps.get_model(app, 'Accepted')
            if app == 'orchidaceae':
                # Treat grex name as a commonname
                pid_list = Species.objects.filter(species__icontains=commonname).values_list('pid', flat=True)
            else:
                pid_list = Accepted.objects.filter(Q(common_name__icontains=commonname) | Q(common_name_search__icontains=commonname_clean)).values_list('pid',flat=True)
            if pid_list:
                spc = Species.objects.filter(pid__in=pid_list)
                combined_list.extend(list(spc))
        species_list = list(combined_list)

    options = [{'value': app, 'text': app_descriptions.get(app, app)} for app in applications]
    options.append({'value': 'All', 'text': 'Entire site'})
    context = {'family_list': family_list, 'genus_list': genus_list, 'species_list': species_list,
               'options': options, 'commonname': commonname, 'selected_app': selected_app, 'role': role,}
    write_output(request, str(commonname))
    return render(request, "search/search_name.html", context)

# From redirect only. This view is all about orchids
def search_orchidaceae(request):
    Genus = apps.get_model('orchidaceae', 'Genus')
    Species = apps.get_model('orchidaceae', 'Species')
    family = Family.objects.get(pk='Orchidaceae')
    min_score = 80
    genus_list = []
    genus_id = []
    full_path = request.path
    path = 'information'
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'
    matched_genus = ''
    role = getRole(request)

    #Get search string. if none, send it back
    search_string = request.GET.get('search_string',None)
    if not search_string:
        # return HttpResponse(message)
        return redirect(request.META.get('HTTP_REFERER', '/'))


    req_genus = request.GET.get('genus','')
    write_output(request, search_string)

    # Clean search_string
    search_string.strip()
    genus, search_string = get_full_search_string(Genus, search_string)
    search_string = clean_search_string(search_string)
    # Try to separate genus from species
    if ' ' not in search_string:
        #  This could possibly be genus
        genus_string = search_string
        spc_string = ''  # If not genus, it could be species
    elif search_string.split()[0]:
        words = search_string.split()
        genus_string = words[0]
        spc_string = ' '.join(words[1:])  # If genus not found, then the entire string could be species
    else:
        genus_string = ''
        spc_string = ''
    # A hack. To avoid timed out
    # if genus_string in big_genera:
    #     genus_string = ''

    # matching genus
    if genus_string:  # Seach genus table
        try:
            matched_genus = Genus.objects.get(genus=genus)
            genus_list = [[matched_genus, matched_genus.get_best_img()]]

            if matched_genus:
                matched_genus.img = matched_genus.get_best_img()
        except Genus.DoesNotExist:
            matched_genus = None
            # if not spc_string:
            #     # Single word search string
            #     spc_string = genus_string
            # Get a list of similar genus with fuzzy score
            genus_list = Genus.objects.all()
            search_list = []
            for x in genus_list:
                score = fuzz.ratio(x.genus.lower(), genus_string.lower())
                if score >= min_score:
                    x.score = score
                    x.img = x.get_best_img()
                    search_list.append(x)

            search_list.sort(key=lambda k: k.score, reverse=True)
            del search_list[5:]
            # List of similarly spelled genera
            genus_list = search_list
            # genus_list = [[item, item.get_best_img()] for item in search_list]
            genus_id = [item.pid for item in genus_list]

    # TODO
    # Get a list of genera in the same infrageneric or related genus uisng genus_relation class
    # genus_list = Genus.objects.filter(subfamily=?,tribe=?,,,)
    # or
    # genus_list = Genusrelation.objects.filter(parentlist__icontains=matched_genus.genus)
    # genus_id = [item[0].genus for item in genus_list]
    # matching species
    match_spc_list = []
    matched_genus_spc = []
    matched_spc = ''

    # Begin species search:
    # Known genus, just get matching species.
#COMPARE UPTO HERE
    if matched_genus:
        if spc_string:
            # match_spc_list = Species.objects.filter(genus=matched_genus, species__istartswith=spc_string[:1])
            # match_spc_list = CommonName.objects.filter(common_name__istartswith=spc_string[:1])
            # pid_list = Binomial.objects.filter(genus=matched_genus, species__istartswith=spc_string).values_list('taxon_id', flat=True)
            this_match_spc_list = query_orchidaceae_species(spc_string, spc_string, spc_string, 5, 20)
            pid_list = []
            if this_match_spc_list:
                pid_list = [t['pid'] for t in this_match_spc_list]

            if not pid_list:
                spc_string = str(genus) + clean_name(spc_string)
                pid_list = Species.objects.annotate(clean_field=RemoveSpaces('binomial')).filter(clean_field=spc_string)
            if pid_list:
                match_spc_list = Species.objects.filter(pid__in=pid_list)
        context = {'search_string': search_string, 'matched_genus': matched_genus,
                   'genus_string': genus_string, 'spc_string': spc_string,
                   'genus_list': genus_list, 'match_spc_list': match_spc_list,
                   'alpha_list': alpha_list,
                   'role': role, 'path': path, 'full_path': full_path}
        return render(request, "search/search_orchidaceae.html", context)


    fuzzy = 0
    if spc_string:
        # Check if fuzzy search is requested
        # Assuming the species in search_string is correct up to the first two characters
        # Narrow the search to species begins with the first two characters of the search string
        grexlist = Species.objects.filter(species__istartswith=spc_string[:1])
        # if genus_list and not matched_genus:
            # matched_genus = genus_list[0]

        # First get species in the matched genus
        if matched_genus:
            # Prepare for sort priority
            priority_items = [matched_genus.genus]
            def sort_key(x):
                item = x[0].genus
                if item in {pv for pv in priority_items}:
                    return (0, item)
                else:
                    return (1, item)

            # Build species list
            this_spc_list = grexlist.filter(genus=matched_genus)
            for x in this_spc_list:
                score = fuzz.ratio(x.binomial.lower(), search_string)
                if score >= min_score:
                    x.score = score
                    match_spc_list.append(x)
                    # match_pid = match_pid.append(x.pid)
            # match_spc_list.sort(key=lambda k: (-k[1], k[0].genus))

            # If no matched, try similar genera
            if genus_list:
                this_list = grexlist.filter(genus__in=genus_id).exclude(genus=matched_genus)
                if len(this_list) > 0:
                    matched_genus_spc = this_list
            else:
                matched_genus_spc = []

            if len(matched_genus_spc) > 0:
                for x in matched_genus_spc:
                    if x not in [spc for spc in match_spc_list]:
                        score = fuzz.ratio(x.binomial.lower(), search_string)
                        if score >= min_score:
                            x.score = score
                            match_spc_list.append(x)
                            # match_pid = match_pid.append(x.pid)
            else:
                # If no good results, use all genera
                for x in grexlist:
                    # compare species with spc_string
                    if x not in [spc for spc in match_spc_list]:
                        score = fuzz.ratio(x.species.lower(), spc_string)
                        if score >= min_score:
                            x.score = score
                            match_spc_list.append(x)
                            # match_pid = match_pid.append(x.pid)

            priority_items = [genus_string]
            # def sort_species_key(x):
            #     item = x.score
            #     if item in {pv for pv in priority_items}:
            #         return (0, item)
            #     else:
            #         return (1, item)
            #
            # match_spc_list.sort(key=lambda x: x.score, reverse=True)
            # match_spc_list.sort(key=lambda k: (-k))
            # match_spc_list.sort(key=sort_species_key)
            sorted_spc_list = sorted(match_spc_list, key=lambda x: (-int(x.genus == genus_string), -x.score))
            match_spc_list = sorted_spc_list

            # if no matched_genus or matching species have low score, try other genera
            if not match_spc_list or match_spc_list[0].score < min_score + 10:
                for x in grexlist:
                    if x not in [key for key in match_spc_list]:
                        score = fuzz.ratio(x.species.lower(), spc_string)
                        if score >= min_score:
                            x.score = scorescore
                            match_spc_list.append(x)

            sorted_spc_list = sorted(match_spc_list, key=lambda x: (-x.score, -int(x.genus == genus_string)))
            match_spc_list = sorted_spc_list

        else:
            # No clue what genus is. Treat the entire string as species.
            flat_spc_string = search_string.replace(" ", "").replace("'", "").replace("-",'')
            # Couldn't find or estimate matched_genus. Then search binomial for all species within Orchidaceae family
            # species is the entire search string, or part of it (in case genus is badly misspelled)
            # match_spc_list = Species.objects.filter(Q(species__istartswith=spc_string) | Q(species__istartswith=search_string))
            match_spc_list = Species.objects.filter(species=search_string)
            if not match_spc_list:
                match_spc_list = Species.objects.filter(
                    Q(species__istartswith=search_string) |
                    Q(species__istartswith=flat_spc_string)
                )
            match_spc_list = match_spc_list.order_by('binomial')
        # If still no clue, send to common name search!
        if not match_spc_list:
            # In case the first word has been identified as a valid genus, remove it before redirection
            if matched_genus:
                search_string = spc_string
            url = "%s?commonname=%s" % (reverse('search:search_name'), search_string)
            return HttpResponseRedirect(url)



    write_output(request, search_string)
    context = {'search_string': search_string, 'matched_genus': matched_genus,
               'genus_string': genus_string, 'spc_string': spc_string,
               'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'family': family, 'fuzzy': fuzzy,
               'alpha_list': alpha_list,
               'role': role, 'path': path, 'full_path': full_path}
    return render(request, "search/search_orchidaceae.html", context)


def search_test(request):
    # Assume the entire string is either species or hybrid grex name.
    # Absolutely no genus allowed in here.
    # Get search term
    global Model

    role = getRole(request)
    selected_app = request.POST.get('selected_app', '')
    if not selected_app:
        selected_app = request.GET.get('selected_app', '')
    search_string = request.GET.get('search_string', '').strip()
    if not search_string:
        search_string = request.POST.get('search_string', '').strip()
    search_string = search_string.rstrip('s')
    search_string_clean = clean_name(search_string)

    if not search_string or search_string == '':
        context = {'role': role, }
        return render(request, "search/search_name.html", context)

    species_list, genus_list, family_list = [], [], []
    if selected_app:
        Species = apps.get_model(selected_app, 'Species')
        Accepted = apps.get_model(selected_app, 'Accepted')
        if selected_app == 'orchidaceae':
            # Treat grex name as a search_string
            pid_list = Species.objects.filter(species__icontains=search_string).values_list('pid', flat=True)
        else:
            pid_list = Accepted.objects.filter(Q(common_name__icontains=search_string) | Q(common_name_search__icontains=search_string_clean)).values_list('pid', flat=True)
        if pid_list:
            species_list = Species.objects.filter(pid__in=pid_list)
    else:
        combined_list = []
        for app in applications:
            Species = apps.get_model(app, 'Species')
            Accepted = apps.get_model(app, 'Accepted')
            if app == 'orchidaceae':
                # Treat grex name as a search_string
                pid_list = Species.objects.filter(species__icontains=search_string).values_list('pid', flat=True)
            else:
                pid_list = Accepted.objects.filter(Q(common_name__icontains=search_string) | Q(common_name_search__icontains=search_string_clean)).values_list('pid',flat=True)
            if pid_list:
                spc = Species.objects.filter(pid__in=pid_list)
                combined_list.extend(list(spc))
        species_list = list(combined_list)

    options = [{'value': app, 'text': app_descriptions.get(app, app)} for app in applications]
    options.append({'value': 'ALL', 'text': 'Entire site'})
    context = {'family_list': family_list, 'genus_list': genus_list, 'species_list': species_list,
               'options': options, 'search_string': search_string, 'selected_app': selected_app, 'role': role,}
    write_output(request, str(search_string))
    return render(request, "search/search_name.html", context)
