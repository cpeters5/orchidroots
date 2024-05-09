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


def search(request):
    # requested from scientific name search in navbar
    # Handles search genus. Then call search_species if there is another word(s) in the search straing
    role = getRole(request)
    # print("role = ", role)
    search_list = []
    match_spc_list = []
    selected_app = ''
    full_path = request.path
    path = 'information'
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'
    if 'selected_app' in request.POST:
        selected_app = request.POST['selected_app']

    # Get search string
    search_string = request.GET.get('search_string', '').strip()
    if 'search_string' in request.POST:
        search_string = request.POST['search_string'].strip()
    if not search_string or search_string == '':
        message = 'Empty search term'
        return HttpResponse(message)

    if ' ' not in search_string:
        genus_string = search_string
    else:
        genus_string, search_list = search_string.split(' ', 1)
        search_list = search_list.split()

    genus_list = []
    # collection all matching genus in each app
    if selected_app in applications:
        Genus = apps.get_model(selected_app, 'Genus')
        try:
            genus = Genus.objects.get(genus=genus_string)
        except Genus.DoesNotExist:
            genus = ''
        if genus and genus != '':
            genus_list.append(genus)

    else:
        for app in applications:
            Genus = apps.get_model(app, 'Genus')
            try:
                genus = Genus.objects.get(genus=genus_string)
            except Genus.DoesNotExist:
                genus = ''
            if genus and genus != '':
                genus_list.append(genus)
    if genus_list:
        match_spc_list = []
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

        context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                   'other_genus_spc': other_genus_spc, 'role': role,
                   'path': path, 'full_path': full_path
                   }
        return render(request, "search/search_species.html", context)

    else:

        other_genus_spc = []
        if selected_app in applications:
            Species = apps.get_model(selected_app, 'Species')
            this_spc_list = Species.objects.filter(
                Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
            other_genus_spc = list(this_spc_list)

        else:
            for app in applications:
                Species = apps.get_model(app, 'Species')
                this_spc_list = Species.objects.filter(
                        Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
                other_genus_spc = list(chain(other_genus_spc, this_spc_list))
        if other_genus_spc:
            context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'other_genus_spc': other_genus_spc, 'role': role, 'selected_app': selected_app,
                       'path': path, 'full_path': full_path
                       }
            return render(request, "search/search_species.html", context)

    # looks like only search string is given.
    url = "%s?search_string=%s" % (reverse('search:search_species'), search_string)
    return HttpResponseRedirect(url)

def search_binomial(request):
    import jellyfish
    from orchidaceae.models import Species

    query = request.GET.get('query', '')
    # print(query)
    results = Species.objects.search(query)
    jaro_winkler_similarities = {s: jellyfish.jaro_winkler_similarity(query, s.binomial) for s in results}
    str_with_scores_dicts = [{'match': s, 'score': jaro_winkler_similarities[s]} for s in results]
    str_with_scores_dicts.sort(key=lambda x: x['score'], reverse=True)

    result_list = []
    # print("results = ", len(str_with_scores_dicts))
    for i in range(10):
        if i == len(str_with_scores_dicts):
            break
        result_list.append(str_with_scores_dicts[i])

    # for x in result_list:
    #      print(f"{x['score']} : '{query}' and '{x['match'].author} {x['match'].binomial}'")
    # print("results = ", len(result_list))
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
    # print("search species")
    # Only family or genus is given (one or both)
    # print("Enter search species")
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
    # print("search_string", search_string)
    if ' ' not in search_string:
        genus_string = search_string
    elif search_string.split()[0]:
        genus_string, search_list = search_string.split(' ', 1)
        search_list = search_list.split()
        # print("search_string", search_string)
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


def xsearch_name(request):
    commonname = ''
    selected_app = ''
    role = getRole(request)
    if 'genre' in request.POST:
        genre = request.POST['genre']
    if 'selected_app' in request.POST:
        selected_app = request.POST['selected_app']
    elif 'selected_app' in request.GET:
        selected_app = request.GET['selected_app']

    if 'commonname' in request.GET:
        commonname = request.GET['commonname'].strip()
    elif 'commonname' in request.POST:
        commonname = request.POST['commonname'].strip()

    commonname = commonname.rstrip('s')
    if not commonname or commonname == '':
        context = {'role': role, }
        return render(request, "search/search_name.html", context)

    commonname_search = commonname.replace("-", "").replace(" ", "").replace("'", "")
    name_list = []

    if selected_app in applications:
        Accepted = apps.get_model(selected_app, 'Accepted')
        name_list = Accepted.objects.filter(common_name_search__icontains=commonname_search)
    else:
        for app in applications:
            Accepted = apps.get_model(app, 'Accepted')
            this_name_list = Accepted.objects.filter(common_name_search__icontains=commonname_search)
            if this_name_list:
                for x in this_name_list:
                    name_list.append(x)

    context = {'name_list': name_list, 'commonname': commonname, 'selected_app': selected_app, 'role': role,}
    write_output(request, str(commonname))
    return render(request, "search/search_name.html", context)


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
    if selected_app in applications:
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
        Accepted = apps.get_model(x.application, 'Accepted')
        acc_obj = Accepted.objects.get(pk=x.taxon_id)
        species_list = species_list + [acc_obj]

    context = {'family_list': family_list, 'genus_list': genus_list, 'species_list': species_list,
               'commonname': commonname, 'selected_app': selected_app, 'role': role,}
    write_output(request, str(commonname))
    return render(request, "search/search_name.html", context)


def search_orchid(request):
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
        search_string = request.GET['search_string'].strip()
        search_string = search_string.replace('.', '')
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
        match_spc_list = get_species_list(app, family).filter(binomial__icontains=search_string)
        if family:
            match_spc_list = match_spc_list.filter(gen__family=family.family)
        match_spc_list = match_spc_list.values('pid', 'species', 'infraspr', 'infraspe', 'family', 'genus', 'author', 'status', 'year', 'binomial')

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
    return render(request, "search/search_species.html", context)


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


def search_fuzzy(request):
    min_score = 60
    search_string = ''
    result_list = []
    result_score = []
    Family = apps.get_model('common', 'Family')
    Genus = apps.get_model('orchidaceae', 'Genus')
    Alliance = apps.get_model('orchidaceae', 'Alliance')
    Species = apps.get_model('orchidaceae', 'Species')

    family = 'Orchidaceae'
    if 'family' in request.GET:
        family = request.GET['family']

    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']

    if request.GET.get('search_string'):
        search_string = request.GET['search_string'].strip()
    send_url = '/search/search_orchid/?search_string=' + search_string + "&role=" + role

    if family != 'Orchidaceae':
        url = "%s?role=%s&family=%s&search_string=%s" % (
        reverse('search:search_species'), role, family, search_string)
        return HttpResponseRedirect(url)

    grexlist = Species.objects.exclude(status='pending')
    # Filter for partner specific list.

    perfect_list = grexlist
    keyword = search_string.lower()
    rest = keyword.split(' ', 1)

    if len(rest) > 1:
        # First get genus by name (could be abbrev.)
        genus = rest[0]
        abrev = genus
        if not genus.endswith('.'):
            abrev = genus + '.'
        # Then find genus in Genus class, start with accepted if exists.
        matched_gen = Genus.objects.filter(Q(genus=rest[0]) | Q(abrev=abrev)).order_by('status')

        if not matched_gen:
            return HttpResponseRedirect(send_url)

        # Genus found, get genus object
        genus_obj = matched_gen[0]
        keyword = rest[1]
        # If genus is a synonym, get accepted name
        if genus_obj.status == 'synonym':
            matched_gen = Genus.objects.filter(Q(genus=genus_obj.gensyn.acc_id) | Q(abrev=genus_obj.gensyn.acc.abrev))
            if matched_gen:
                genus_obj = matched_gen[0]
            else:
                # For synonym genus, use conventional search
                return HttpResponseRedirect(send_url)

        # Get alliance associated to the genus_obj
        alliance_obj = Alliance.objects.filter(gen=genus_obj.pid)
        if alliance_obj:
            # Then create genus_list of all genus associated to the alliance.
            genus_list = list(Alliance.objects.filter(alid=alliance_obj[0].alid.pid).values_list('gen'))

            # Then create the search space of species/hybrids in all genera associated to each alliances.
            grexlist = grexlist.filter(gen__in=genus_list)
        else:
            # If alliance does not exist, just search on the genus alone
            grexlist = grexlist.filter(gen=genus_obj.pid)
    else:
        return HttpResponseRedirect(send_url)

    # Compute fuzzy score for all species in grexlist
    for x in grexlist:
        # If the first word is genus hint, compare species and the tail
        score = fuzz.ratio(x.grex().lower(), keyword)
        if score >= min_score:
            result_list.append(x)
            result_score.append([x, score])

    # Add the perfect match and set score 100%.
    # At this point, the first word is related to a genus
    perfect_list = perfect_list.filter(species__iexact=rest[1])
    perfect_pid = perfect_list.values_list('pid', flat=True)

    for x in perfect_list:
        if x in result_list:
            result_list.remove(x)

    for i in range(len(result_score)):
        if genus_obj != '':
            if result_score[i][0].gen.pid == genus_obj.pid:
                if result_score[i][1] == 100:
                    result_score[i][1] = 200
    family = Family.objects.get(pk='Orchidaceae')

    result_score.sort(key=lambda k: (-k[1], k[0].name()))
    context = {'result_list': result_list,'result_score': result_score, 'len': len(result_list), 'search_string':  search_string, 'genus': genus,
               'alliance_obj': alliance_obj, 'genus_obj': genus_obj,
               'min_score': min_score, 'keyword': keyword,
               'family': family,
               'alpha_list': alpha_list, 'role': role, 'namespace': 'search',

               }
    return render(request, "search/search_orchid.html", context)


def compare_strings(str1, str2, ignore_chars):
    for char in ignore_chars:
        str1 = str1.replace(char, '')
        str2 = str2.replace(char, '')
    return str1.lower() == str2.lower()