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

def search(request):
    # requested from scientific name search in navbar
    # Handles search genus. Then call search_species if there is another word(s) in the search straing
    role = getRole(request)
    search_list = []
    genus_list = []
    match_spc_list = []
    selected_app = ''
    full_path = request.path
    path = 'information'
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'
    selected_app = request.GET.get('app', '')


    # Get search string
    search_string = request.GET.get('search_string', '').strip()
    if 'search_string' in request.POST:
        search_string = request.POST['search_string'].strip()

    # If no search string given, return
    if not search_string or search_string == '':
        message = 'Empty search term'
        return HttpResponse(message)

    # Handle orchids in its own search
    if selected_app == 'orchidaceae':
        url = "%s?search_string=%s" % (reverse('search:search_orchidaceae'), search_string)
        return HttpResponseRedirect(url)
    elif selected_app in applications:
        # If app is valid, collect all matching genera in each app
        Genus = apps.get_model(selected_app, 'Genus')
        genus, full_search_string = get_full_search_string(Genus, search_string)
        genus_list.append(genus)
        family = genus.family
        Species = apps.get_model(family.application, 'Species')
        this_match_spc_list = Species.objects.filter(genus=genus).filter(binomial__icontains=full_search_string)
        match_spc_list = list(chain(match_spc_list, this_match_spc_list))
    else:
    # unknown application. Check every app in Application (aves, animalia, fungi, orchidaceae and other)
        for app in applications:
            Genus = apps.get_model(app, 'Genus')
            genus, full_search_string = get_full_search_string(Genus, search_string)
            if genus and genus.family.family == 'Orchidaceae':
                genusname = genus.genus
                familyname = genus.family.family
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
        # If no matching genus, get matching species for any genus
        other_genus_spc = []
        if selected_app in applications:
            Species = apps.get_model(selected_app, 'Species')
            this_spc_list = Species.objects.filter(
                Q(binomial__icontains=full_search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
            other_genus_spc = list(this_spc_list)

        else:
            for app in applications:
                Species = apps.get_model(app, 'Species')
                this_spc_list = Species.objects.filter(
                        Q(binomial__icontains=full_search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
                other_genus_spc = list(chain(other_genus_spc, this_spc_list))
        if other_genus_spc:
            context = {'search_string': full_search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'other_genus_spc': other_genus_spc, 'role': role, 'selected_app': selected_app,
                       'path': path, 'full_path': full_path
                       }
            return render(request, "search/search_species.html", context)

    # Empty results
    url = "%s?search_string=%s" % (reverse('search:search_species'), full_search_string)
    return HttpResponseRedirect(url)


def search_binomial(request):
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


def getResultByGenus(family, search_string, genus):
    match_spc_list = []
    single_word = False

    if ' ' not in search_string:
        single_word = True
        genus_string = search_string
    elif search_string.split()[0]:
        genus_string = search_string.split()[0]

    if genus_string:  # Seach genus table
        min_score = 80
        # Try to match genus
        Genus = apps.get_model(family.application, 'Genus')
        genus_list = Genus.objects.all(). \
                        values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
        search_list = []
        for x in genus_list:
            if x['genus']:
                score = fuzz.ratio(x['genus'].lower(), genus_string.lower())
                if score >= min_score:
                    search_list.append([x, score])

        search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
        del search_list[5:]
        genus_list = search_list

    if not genus_list or not single_word:
        # search_string might be a species name, or second word in the <genus, species> pair
        match_spc_list = get_species_list(family.application, family).filter(binomial__icontains=search_string)
        if family:
            match_spc_list = match_spc_list.filter(gen__family=family.family)
        match_spc_list = match_spc_list.values_list('pid', 'species', 'infraspr', 'infraspe', 'family', 'genus', 'author', 'status', 'year', 'binomial')

    return genus_list, match_spc_list


def search_species(request):
    # Only family or genus is given (one or both)
    genus_list = []
    search_list = []
    match_spc_list = []
    full_path = request.path
    selected_app = ''
    # If no match found, perform fuzzy match

    search_string = request.GET.get('search_string', None)
    if 'search_string' in request.POST:
        search_string = request.POST['search_string']
    if not search_string:
        send_url = '/'
        return HttpResponseRedirect(send_url)
    search_string.strip()
    search_string = search_string.replace('.', '')
    search_string = search_string.replace(' mem ', ' Memoria ')
    search_string = search_string.replace(' Mem ', ' Memoria ')
    search_string = search_string.replace(' mem. ', ' Memoria ')
    search_string = search_string.replace(' Mem. ', ' Memoria ')
    if ' ' not in search_string:
        genus_string = search_string
    elif search_string.split()[0]:
        genus_string, search_list = search_string.split(' ', 1)
        search_list = search_list.split()
    role = getRole(request)

    if selected_app in request.POST:
        selected_app = request.POST['selected_app']
    match_spc_list = []
    if selected_app in applications:
        Species = apps.get_model(selected_app, 'Species')
        match_spc_list = Species.objects.filter(
            Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
    else:
        species_list = []
        i = 0
        for app in applications:
            Species = apps.get_model(app, 'Species')
            this_species_list = Species.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
            if i == 0:
                species_list = (this_species_list)
            else:
                species_list = (species_list).union(this_species_list)
            # match_spc_list = (otspecies_list).union(orspecies_list).union(fuspecies_list).union(avspecies_list).union( anspecies_list)

        match_spc_list = species_list
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
    app = 'orchidaceae'
    genus_string = ''
    single_word = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    match_spc_list = []
    full_path = request.path
    # If no match found, perform fuzzy match

    if 'search_string' in request.GET:
        search_string = request.GET.get('search_string','').strip()
    else:
        message = 'Empty search term'
        return HttpResponse(message)
    Genus = apps.get_model('orchidaceae', 'Genus')
    genus, search_string = get_full_search_string(Genus, search_string)


    # search_string = search_string.replace('.', '')
    search_string = search_string.replace(' mem ', ' Memoria ')
    search_string = search_string.replace(' Mem ', ' Memoria ')
    search_string = search_string.replace(' mem. ', ' Memoria ')
    search_string = search_string.replace(' Mem. ', ' Memoria ')
    if ' ' not in search_string:
        single_word = True
        genus_string = search_string
    elif search_string.split()[0]:
        genus_string = search_string.split()[0]
    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']
    try:
        family = Family.objects.get(pk=family)
    except Family.DoesNotExist:
        family = None

    # Perform conventional match
    if genus_string:  # Seach genus table
        min_score = 80
        # Try to match genus
        Genus = apps.get_model(app, 'Genus')
        genus_list = Genus.objects.all()
                      # .values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year'))
        search_list = []
        for x in genus_list:
            score = fuzz.ratio(x.genus.lower(), genus_string.lower())
            if score >= min_score:
                search_list.append([x, score])

        search_list.sort(key=lambda k: (-k[1], k[0].genus))
        del search_list[5:]
        genus_list = search_list
    if not genus_list or not single_word:
        match_spc_list = get_species_list(app, family).filter(binomial__icontains=search_string)
    if match_spc_list:
        match_spc_list = match_spc_list.order_by('binomial')
    path = 'information'
    if role == 'cur':
        path = 'photos'

    write_output(request, search_string)
    context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'genus_total': len(genus_list),
               'family': family,
               'alpha_list': alpha_list,
               'single_word': single_word,
               'role': role, 'path': path, 'full_path': full_path}
    return render(request, "search/search_orchidaceae.html", context)


def get_species_list(application, family=None, subfamily=None, tribe=None, subtribe=None):
    Species = apps.get_model(application, 'Species')
    species_list = Species.objects.all()
    if subtribe:
        species_list = species_list.filter(gen__subtribe=subtribe)
    elif tribe:
        species_list = species_list.filter(gen__tribe=tribe)
    elif subfamily:
        species_list = species_list.filter(gen__subfamily=subfamily)
    elif family:
        species_list = species_list.filter(gen__family=family)

    return species_list
    # return species_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')


def compare_strings(str1, str2, ignore_chars):
    for char in ignore_chars:
        str1 = str1.replace(char, '')
        str2 = str2.replace(char, '')
    return str1.lower() == str2.lower()