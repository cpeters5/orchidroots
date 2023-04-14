from django.shortcuts import render
from django.db.models import Q
from django.apps import apps
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect

from itertools import chain
from fuzzywuzzy import fuzz, process
from core.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages
from accounts.models import User, Photographer
from utils.views import write_output, getRole
from utils import config
applications = config.applications
alpha_list = config.alpha_list

def search(request):
    role = getRole(request)
    print("role = ", role)
    search_list = []
    match_spc_list = []
    full_path = request.path
    path = 'information'
    if request.user.is_authenticated and request.user.tier.tier > 2:
        path = 'photos'

    # Get search string
    if 'search_string' in request.GET:
        search_string = request.GET['search_string'].strip()
        if search_string == '':
            message = 'The search term must contain genus name'
            return HttpResponse(message)
        if ' ' not in search_string:
            genus_string = search_string
        else:
            genus_string, search_list = search_string.split(' ', 1)
            search_list = search_list.split()
    else:
        message = 'The search term must contain genus name'
        return HttpResponse(message)

    genus_list = []
    # collection all matching genus in each app
    for app in applications:
        Genus = apps.get_model(app, 'Genus')
        try:
            genus = Genus.objects.get(genus=genus_string)
        except Genus.DoesNotExist:
            genus = ''
        if genus:
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
        for app in applications:
            Species = apps.get_model(app, 'Species')
            this_spc_list = Species.objects.filter(
                    Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))
            other_genus_spc = list(chain(other_genus_spc, this_spc_list))
        if other_genus_spc:
            context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
                       'other_genus_spc': other_genus_spc, 'role': role,
                       'path': path, 'full_path': full_path
                       }
            return render(request, "search/search_species.html", context)

    # looks like only search string is given.
    print("Nothing found, go through species = ")
    url = "%s?search_string=%s" % (reverse('search:search_species'), search_string)
    return HttpResponseRedirect(url)


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
    print("Enter search species")
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    search_list = []
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
        print("search_string", search_string)
        if ' ' not in search_string:
            genus_string = search_string
        elif search_string.split()[0]:
            genus_string, search_list = search_string.split(' ', 1)
            search_list = search_list.split()
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)
    print("search_string", search_string)
    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']

    # If orchids, use the old search engine for orchid

    if family:
        family = Family.objects.get(pk=family)

    spc = search_string
    OrSpecies = apps.get_model('orchidaceae', 'Species')
    OtSpecies = apps.get_model('other', 'Species')
    FuSpecies = apps.get_model('fungi', 'Species')
    AvSpecies = apps.get_model('aves', 'Species')
    AnSpecies = apps.get_model('animalia', 'Species')
    # First, try to match entire string using binomial

    # Try to match entire string
    #  Get orchid species matches
    orspecies_list = OrSpecies.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))

    # Get other species matches
    otspecies_list = OtSpecies.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))

    # Get fungi species matches
    fuspecies_list = FuSpecies.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))

    # Get aves species matches
    avspecies_list = AvSpecies.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))

    # Get animalia species matches
    anspecies_list = AnSpecies.objects.filter(Q(binomial__icontains=search_string) | Q(species__in=search_list) | Q(infraspe__in=search_list))

    if family:
        if family.application == 'orchidaceae':
            orspecies_list = orspecies_list.filter(family=family).values('pid', 'species', 'infraspr', 'infraspe', 'family', 'genus', 'author', 'status', 'year', 'binomial', 'gen')
            match_spc_list = orspecies_list
        elif family.application == 'other':
            otspecies_list = otspecies_list.filter(family=family).values('pid', 'species', 'infraspr', 'infraspe', 'family', 'genus', 'author', 'status', 'year', 'binomial', 'gen')
            match_spc_list = otspecies_list
        elif family.application == 'fungi':
            fuspecies_list = fuspecies_list.filter(family=family).values('pid', 'species', 'infraspr', 'infraspe', 'family', 'genus', 'author', 'status', 'year', 'binomial', 'gen')
            match_spc_list = fuspecies_list
        elif family.application == 'aves':
            avspecies_list = avspecies_list.filter(family=family).values('pid', 'species', 'infraspr', 'infraspe', 'family', 'genus', 'author', 'status', 'year', 'binomial', 'gen')
            match_spc_list = avspecies_list
        elif family.application == 'animalia':
            anspecies_list = anspecies_list.filter(family=family).values('pid', 'species', 'infraspr', 'infraspe', 'family', 'genus', 'author', 'status', 'year', 'binomial', 'gen')
            match_spc_list = anspecies_list

    else:
        match_spc_list = (otspecies_list).union(orspecies_list).union(fuspecies_list).union(avspecies_list).union(anspecies_list)
        match_spc_list = match_spc_list.order_by('family', 'binomial')

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    path = 'information'
    if request.user.tier.tier > 2:
        path = 'photos'

    write_output(request, search_string)
    context = {'search_string': search_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'genus_total': len(genus_list),
               'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'role': role, 'path': path, 'full_path': full_path}
    return render(request, "search/search_species.html", context)


def search_name(request):
    talpha = ''
    commonname = ''
    # app = 'other'
    # Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen = getModels(request)
    if 'commonname' in request.GET:
        commonname = request.GET['commonname'].strip()
        commonname = commonname.replace("-", " ")
    name_list = []
    for app in applications:
        Accepted = apps.get_model(app, 'Accepted')
        this_name_list = Accepted.objects.filter(common_name__icontains=commonname)
        if this_name_list:
            for x in this_name_list:
                name_list.append(x)
    if 'talpha' in request.GET:
        talpha = request.GET['talpha']
    if talpha != '':
        name_list = name_list.filter(species__istartswith=talpha)
    total = len(name_list)
    context = {'name_list': name_list, 'commonname': commonname,
               'talpha': talpha, 'alpha_list': alpha_list}
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
    Family = apps.get_model('core', 'Family')
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


