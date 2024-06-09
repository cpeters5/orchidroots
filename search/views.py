from django.shortcuts import render
from django.db.models import Q
from django.apps import apps
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect

from itertools import chain
from fuzzywuzzy import fuzz, process
from common.models import Family, Subfamily, Tribe, Subtribe, CommonName
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages
from accounts.models import User, Photographer
from utils.views import write_output, getRole
from utils import config
applications = config.applications
alpha_list = config.alpha_list


def get_full_search_string(Genus, search_string):
    if ' ' not in search_string:
        genus_string = search_string
    else:
        (genus_string, rest) = search_string.split(' ', 1)

    abrev = ''
    # get genus obj
    genera = Genus.objects.filter(genus=genus_string)
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
            abrev = genus_string
    full_search_string = search_string
    if abrev != '':
        full_search_string = search_string.replace(abrev, genus.genus)
    return (genus, full_search_string)

# Prepare query string for search in common.Binomial
# remove all occurrences of blanks, white spaces, single and double quotes, ., -, and expand genus abreviation if exists
def clean_query(search_string):
    if ' ' not in search_string:
        genus_string = search_string
    else:
        (genus_string, rest) = search_string.split(' ', 1)

    if genus_string:
        genus_list = Binomial.objects.filter(abrev=genus_string)

    # test if genus_string is an abreviation


    cleaned_species = rest.replace(" ", "").replace("-", "").replace(",", "").replace("'", "").replace("\"", "").replace(
        ".", "")
    clean_query = genus_string + cleaned_species
    return cleaned_query


def search(request):
    # search.search requested from the navbar and home page.
    # If family = Orchidaceae, or unknown family, redirect to search.search_orchidaceae.

    # Identifies genus from the first word in search string.
    # If found, the family and application can be determined.
    # From list of genera, find matching species from the rest of search string.
    # if no results, call search.search_species.

    role = getRole(request)
    search_list = []
    genus_list = []
    match_spc_list = []
    full_path = request.path
    path = 'information'
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'

    # Get search string
    search_string = request.GET.get('search_string', '').strip()
    if 'search_string' in request.POST:
        search_string = request.POST['search_string'].strip()

    # If no search string given, return
    if not search_string or search_string == '':
        message = 'Empty search term'
        return HttpResponse(message)

    # Determine requested application and send 'orchidaceae' request to search_orchidaceae
    selected_app = request.GET.get('app', '')
    if selected_app == 'orchidaceae':
        url = "%s?search_string=%s" % (reverse('search:search_orchidaceae'), search_string)
        return HttpResponseRedirect(url)

    # Go through each application (!= orchidaceae) one by one.
    if selected_app in applications:
        # If app is valid, collect all matching genera in each app
        Genus = apps.get_model(selected_app, 'Genus')

        # Identify genus and expand genus abreviation if exists in search_string
        genus, full_search_string = get_full_search_string(Genus, search_string)
        genus_list.append(genus)
        family = genus.family
        Species = apps.get_model(family.application, 'Species')
        this_match_spc_list = Species.objects.filter(genus=genus).filter(binomial__icontains=full_search_string)
        match_spc_list = list(chain(match_spc_list, this_match_spc_list))
    else:
    # if requested application is empty or unknown, look for genus in each app in Applications
        for app in applications:
            Genus = apps.get_model(app, 'Genus')
            genus, full_search_string = get_full_search_string(Genus, search_string)
            if genus and genus.family.family == 'Orchidaceae':
                url = "%s?search_string=%s&genus=%s&family=%s" % (reverse('search:search_orchidaceae'), search_string, genus.genus, genus.family.family)
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
        other_genus_spc = []
        if genus_list and not match_spc_list and ' ' in search_string:
            other_genus_spc = Species.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))

        context = {'search_string': full_search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                   'other_genus_spc': other_genus_spc,
                   'role': role,
                   'path': path, 'full_path': full_path
                   }
        return render(request, "search/search_species.html", context)

    else:
        # Here, the requested genus from search string is unknown, probably misspelled, or search string didn't include genus.
        # Forget genus and match species instead


        other_genus_spc = []
        if selected_app in applications:
            Species = apps.get_model(selected_app, 'Species')
            # Look foir matching binomial with entire search string OR matchind species with elements in search_list
            this_spc_list = Species.objects.filter(
                Q(binomial__icontains=full_search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
            other_genus_spc = list(this_spc_list)
        else:
            for app in applications:
                Species = apps.get_model(app, 'Species')
                this_spc_list = Species.objects.filter(
                        Q(binomial__icontains=full_search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
                print("app = ", app, len(this_spc_list), full_search_string)
                other_genus_spc = list(chain(other_genus_spc, this_spc_list))

        if other_genus_spc:
            context = {'search_string': full_search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'other_genus_spc': other_genus_spc, 'role': role, 'selected_app': selected_app,
                       'path': path, 'full_path': full_path
                       }
            return render(request, "search/search_species.html", context)
    # Empty results
    url = "%s?search_string=%s" % (reverse('search:search_binomial'), full_search_string)
    return HttpResponseRedirect(url)


# Uses commin.Binomial
def search_binomial(request):
    from os.path import join
    import jellyfish
    from common.models import Binomial
    # Get teh search string
    search_string = request.GET.get('query', '')
    # Clean search string. Get genus if exists
    search_genus, search_string = clean_query(search_string)
    if query != '':
        # 1. Just match the requested string
        this_query = ''
        results = Binomial.objects.search(query)
        print("1. results = ", len(results))
        if ' ' in query:
            (req_genus, rest) = query.split(' ', 1)
            abrev_obj = Genus.objects.filter(abrev=req_genus)
            if len(abrev_obj) > 0:
                replacement = abrev_obj.first().genus
                query = query.split()
                abrev = query[0]
                query = " ".join(query)
                query = query.replace(abrev, replacement)
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
    context = {'result_list': result_list, 'query': query, 'role': role }
    return render(request, "search/search_binomial.html", context)


def xsearch_binomial(request):
    from os.path import join
    import jellyfish
    from orchidaceae.models import Species

    query = request.GET.get('query', '')
    if query != '':
        if ' ' in query:
            (req_genus, rest) = query.split(' ', 1)
            abrev_obj = Genus.objects.filter(abrev=req_genus)
            if len(abrev_obj) > 0:
                replacement = abrev_obj.first().genus
                query = query.split()
                abrev = query[0]
                query = " ".join(query)
                query = query.replace(abrev, replacement)
        results = Species.objects.search(query)
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
    context = {'result_list': result_list, 'query': query, 'role': role }
    return render(request, "search/search_binomial.html", context)

# Called from search when genus can't be identified
# We know that genus, application and family cannot be identified
def search_species(request):
    genus_list = []
    search_list = []
    species_list = []
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
    # Get search term
    role = getRole(request)
    selected_app = request.POST.get('selected_app', '')
    if not selected_app:
        selected_app = request.GET.get('selected_app', '')

    commonname = request.GET.get('commonname', '').strip()
    if not commonname:
        commonname = request.POST.get('commonname', '').strip()
    commonname = commonname.rstrip('s')

    if not commonname or commonname == '':
        context = {'role': role, }
        return render(request, "search/search_name.html", context)
    search_string = commonname.replace("-", "").replace(" ", "").replace("'", "")
    # Collect entities contaiing the search string
    commonname_list = CommonName.objects.filter(common_name_search__icontains=search_string)
    if selected_app != 'ALL' and selected_app in applications:
        commonname_list = commonname_list.filter(application=selected_app)

    if len(commonname_list) == 0:
        return render(request, "search/search_name.html", { 'role': role, 'commonname': commonname})

    # Start with highest level, Families
    name_list = commonname_list.filter(level='Family')
    family_list = []
    for x in name_list:
        fam_obj = Family.objects.get(pk=x.taxon_id)
        family_list = family_list + [fam_obj]

    # Search genus with matched common name
    name_list = commonname_list.filter(level='Genus')
    genus_list = []
    for x in name_list:
        Genus = apps.get_model(x.application, 'Genus')
        gen_obj = Genus.objects.get(pk=x.taxon_id)
        genus_list = genus_list + [gen_obj]

    # search species
    name_list = commonname_list.filter(level='Accepted')
    species_list = []
    for x in name_list:
        Species = apps.get_model(x.application, 'Species')
        acc_obj = Species.objects.get(pk=x.taxon_id)
        species_list = species_list + [acc_obj]

    context = {'family_list': family_list, 'genus_list': genus_list, 'species_list': species_list,
               'commonname': commonname, 'selected_app': selected_app, 'role': role,}
    write_output(request, str(commonname))
    return render(request, "search/search_name.html", context)


def search_orchidaceae(request):
    import re
    app = 'orchidaceae'
    family = Family.objects.get(pk='Orchidaceae')
    min_score = 70
    genus_list = []
    genus_id = []
    full_path = request.path
    matched_img = ''
    matched_genus = ''
    role = getRole(request)

    #Get search string. if none, send it back
    search_string = request.GET.get('search_string',None)
    if not search_string:
        message = 'Empty search term'
        return HttpResponse(message)

    # get orchidaceae models
    Genus = apps.get_model(app, 'Genus')
    Species = apps.get_model(app, 'Species')

    # Clean search_string
    search_string.strip()
    genus, search_string = get_full_search_string(Genus, search_string)
    # search_string = search_string.replace('.', '')
    search_string = search_string.replace(' mem ', ' Memoria ')
    search_string = search_string.replace(' Mem ', ' Memoria ')
    search_string = search_string.replace(' mem. ', ' Memoria ')
    search_string = search_string.replace(' Mem. ', ' Memoria ')
    search_string = re.sub(r'\s+', ' ', search_string)

    # Try to separate genus from species
    if ' ' not in search_string:
        #  This could possibly be genus
        genus_string = search_string
        spc_string = None  # If not genus, it could be species
    elif search_string.split()[0]:
        words = search_string.split()
        genus_string = words[0]
        spc_string = ' '.join(words[1:])  # If genus not found, then the entire string could be species
    else:
        genus_string = ''
        spc_string = ''

    # matching genus
    if genus_string:  # Seach genus table
        try:
            matched_genus = Genus.objects.get(genus=genus)
            genus_list = [[matched_genus, matched_genus.get_best_img()]]
            matched_img = matched_genus.get_best_img()
        except Genus.DoesNotExist:
            matched_genus = None
            # matched_img = ''
            if not spc_string:
                # Single word search string
                spc_string = genus_string

            # Get a list of similar genus with fuzzy score
            genus_list = Genus.objects.all()
            search_list = []
            for x in genus_list:
                score = fuzz.ratio(x.genus.lower(), genus_string.lower())
                if score >= min_score:
                    search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0].genus))
            del search_list[5:]
            # List of similarly spelled genera
            genus_list = [[item[0], item[0].get_best_img()] for item in search_list]
        genus_id = [item[0].genus for item in genus_list]

        # TODO
        # Get a list of genera in the same infrageneric or related genus uisng genus_relation class
        # genus_list = Genus.objects.filter(subfamily=?,tribe=?,,,)
        # or
        # genus_list = Genusrelation.objects.filter(parentlist__icontains=matched_genus.genus)
        # genus_id = [item[0].genus for item in genus_list]

    # matching species
    match_spc_list = []
    matched_genus_spc = []
    gen_list = []
    fuzzy = 0
    if spc_string:
        # Check if fuzzy search is requested
        fuzzy = request.GET.get('fuzzy', 0)
        if fuzzy:
            grexlist = Species.objects.filter(species__istartswith=spc_string[:2])
            # First get species in the matched genus
            if matched_genus:
                # Narrow the search to species begins with the firrst two characters of the search string
                print("1 matched genus = ", matched_genus)
                this_spc_list = grexlist.filter(genus=matched_genus)
                print("2 this_spc_list = ", len(this_spc_list))
                print("3 spc_string = ", spc_string)
                for x in this_spc_list:
                    score = fuzz.ratio(x.binomial.lower(), search_string)
                    if score >= min_score:
                        print(x.binomial)
                        match_spc_list.append([x, score])
                match_spc_list.sort(key=lambda k: (-k[1], k[0].genus))

                # If no match, search all species
                # if len(match_spc_list) == 0:
                #     match_spc_list = matched_genus_spc
                # match_spc_list = [(obj, 100) for obj in match_spc_list.iterator()]
                print("3 match_spc_list = ", len(match_spc_list))

            # If no matched, try similar genera
            if not match_spc_list and genus_list:
                this_list = grexlist.filter(genus__in=genus_id)
                if len(this_list) > 0:
                    matched_genus_spc = this_list
            else:
                matched_genus_spc = []

            print("4 genus_list = ", genus_list)
            # Compute fuzzy score
            print("5 grexlist = ", len(grexlist))
            if len(matched_genus_spc) == 0:
                for x in grexlist:
                    # compare species with spc_string
                    score = fuzz.ratio(x.species.lower(), spc_string)
                    if score >= min_score:
                        match_spc_list.append([x, score])

                if match_spc_list and match_spc_list[0][1] < min_score + 10:
                    for x in grexlist:
                        if x not in [key for key, _ in match_spc_list]:
                            # compare species with spc_string
                            score = fuzz.ratio(x.species.lower(), spc_string)
                            if score >= min_score:
                                match_spc_list.append([x, score])

            match_spc_list.sort(key=lambda k: (-k[1], k[0].genus))

            # if no matched_genus or matching species have low score, try other genera
            if not match_spc_list or match_spc_list[0][1] < min_score + 10:
                for x in grexlist:
                    if x not in [key for key, _ in match_spc_list]:
                        score = fuzz.ratio(x.species.lower(), spc_string)
                        if score >= min_score and x not in [key for key, _ in match_spc_list]:
                            match_spc_list.append([x, score])
            match_spc_list.sort(key=lambda k: (-k[1], k[0].genus))
            match_spc_list = [item[0] for item in match_spc_list]

        else:
            # straight partial matches
            if matched_genus:
                # First search species in matched genus
                all_spc_list = Species.objects.filter(binomial__icontains=search_string)
                match_spc_list = all_spc_list.filter(genus=matched_genus)
                # If no match, search all species
                if len(match_spc_list) == 0:
                    match_spc_list = all_spc_list
            else:
                # species is the entire search string, or part of it
                match_spc_list = Species.objects.filter(Q(species__istartswith=spc_string) | Q(species__istartswith=search_string))
            match_spc_list = match_spc_list.order_by('binomial')

    path = 'information'
    if role == 'cur':
        path = 'photos'

    write_output(request, search_string)
    context = {'search_string': search_string, 'matched_genus': matched_genus,
               'matched_img': matched_img,
               'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'genus_total': len(genus_list),
               'family': family, 'fuzzy': fuzzy,
               'alpha_list': alpha_list,
               'role': role, 'path': path, 'full_path': full_path}
    return render(request, "search/search_orchidaceae.html", context)


