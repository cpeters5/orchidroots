from django.shortcuts import render
from django.db.models import Q
from django.apps import apps
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect

from itertools import chain
from fuzzywuzzy import fuzz, process
from core.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Genus, Subgenus, Section, Subsection, Series, Intragen, HybImages
from accounts.models import User, Photographer, Sponsor
from utils import config
from utils.views import write_output, getRole, get_family_list

# alpha_list = string.ascii_uppercase
alpha_list = config.alpha_list
# Create your views here.


def search_orchid(request):
    # from itertools import chain
    Family = apps.get_model('core', 'Family')
    Genus = apps.get_model('orchidaceae', 'Genus')
    Species = apps.get_model('orchidaceae', 'Species')

    family = 'Orchidaceae'
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']
    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
    else:
        spc_string = ''
    keyword = spc_string

    if family != 'Orchidaceae':
        url = "%s?role=%s&family=%s&spc_string=%s" % (
        reverse('search:search_species'), role, family, spc_string)
        return HttpResponseRedirect(url)
    genus = ''
    tail = ''
    spcount = ''
    y = ''
    search_list = ()
    partial_spc = ()
    partial_hyb = ()
    result_list = []
    spc_list = []
    hyb_list = []

    if request.user.is_authenticated:
        write_output(request, keyword)
    if keyword:
        rest = keyword.split(' ', 1)
        if len(rest) > 1:
            tail = rest[1]
        keys = keyword.split()
        if len(keys[0]) < 3 or keys[0].endswith('.'):
            keys = keys[1:]
            x = keys
        else:
            keyword = ' '.join(keys)
            x = keys[0]            # This could be genus or species (or hybrid)

        if len(x) > 7:
            x = x[: -2]  # Allow for some ending variation
        elif len(x) > 5:
            x = x[: -1]

        if len(keys) > 1:
            y = keys[1]            # This could be genus or species (or hybrid)

        if len(y) > 7:
            y = y[: -2]  # Allow for some ending variation
        elif len(y) > 5:
            y = y[: -1]

        if keys:
            genus = Genus.objects.filter(genus__iexact=keys[0])
            if len(genus) == 0:
                genus = ''
        else:
            genus = ''
        if genus and len(genus) > 0:
            genus = genus[0].genus
        else:
            genus = ''

        temp_list = Species.objects.exclude(status__iexact='pending')
        if spc_list:
            temp_list = temp_list.filter(pid__in=spc_list)
        if hyb_list:
            temp_list = temp_list.filter(pid__in=hyb_list)

        if len(keys) == 1:
            search_list = temp_list.filter(species__icontains=keys[0]).order_by('status', 'genus', 'species')
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(species__icontains=x).exclude(pid__in=mylist).order_by(
                'status', 'genus', 'species')

        elif len(keys) == 2:
            search_list = temp_list.filter(species__iexact=keys[1]).order_by('status', 'genus', 'species')
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=x) | Q(infraspe__icontains=y)
                                           | Q(species__icontains=y)).exclude(pid__in=mylist).order_by(
                'status', 'genus', 'species')

        elif len(keys) == 3:
            search_list = temp_list.filter((Q(species__iexact=keys[0]) & Q(infraspe__iexact=keys[2])) |
                                           (Q(genus__iexact=keys[0]) & Q(species__iexact=keys[1]) &
                                            Q(infraspe__iexact=keys[2]))).order_by('status', 'genus', 'species')
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=x) | Q(species__icontains=keys[1])).exclude(
                pid__in=mylist).order_by('status', 'genus', 'species')

        elif len(keys) >= 4:
            search_list = temp_list.filter((Q(species__iexact=keys[0]) & Q(infraspe__iexact=keys[2]))
                                           | (Q(genus__iexact=keys[0]) & Q(species__iexact=keys[1])
                                              & Q(infraspe__iexact=keys[2]))).order_by('status', 'genus', 'species')
            mylist = search_list.values('pid')
            partial_spc = temp_list.filter(Q(species__icontains=keys[1]) | Q(infraspe__icontains=keys[3])).exclude(
                pid__in=mylist).order_by('status', 'genus', 'species')
        spcount = len(search_list)

        all_list = list(chain(search_list, partial_hyb, partial_spc))
        for x in all_list:
            short_grex = x.short_grex().lower()
            score = fuzz.ratio(short_grex, keyword)     # compare against entire keyword
            if score < 60:
                score = fuzz.ratio(short_grex, keys[0])  # match against the first term after genus

            # if score < 100:
            grex = x.grex()
            score1 = fuzz.ratio(grex.lower(), keyword.lower())
            if score1 == 100:
                score1 = 200
            if score1 > score:
                score = score1
            if score >= 60:
                result_list.append([x, score])

    result_list.sort(key=lambda k: (-k[1], k[0].name()))
    family_list, alpha = get_family_list(request)
    family = Family.objects.get(pk='Orchidaceae')

    context = {'result_list': result_list, 'keyword': keyword, 'fuzzy': '1',
               'tail': tail, 'genus': genus, 'spcount': spcount, 'spc_string': spc_string,
               'family': family, 'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha,
               'role': role, }
    return render(request, "search/search_orchid.html", context)


def search_species(request):
    min_score = 70
    genus_string = ''
    single_word = ''
    family = ''
    subfamily = ''
    tribe = ''
    subtribe = ''
    genus_list = []
    match_spc_list = []
    match_list = []
    perfect_list = []
    fuzzy_list = []
    fuzzy = ''
    full_path = request.path
    if 'fuzzy' in request.GET:
        fuzzy = request.GET['fuzzy'].strip()
    # If no match found, perform fuzzy match

    if 'spc_string' in request.GET:
        spc_string = request.GET['spc_string'].strip()
        if ' ' not in spc_string:
            single_word = True
            genus_string = spc_string
        elif spc_string.split()[0]:
            genus_string = spc_string.split()[0]
    else:
        send_url = '/'
        return HttpResponseRedirect(send_url)

    role = getRole(request)
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    # If orchids, use the old search engine for orchid
    if family == 'Orchidaceae':
        url = "%s?role=%s&family=Orchidaceae&spc_string=%s" % (
        reverse('search:search_orchid'), role, spc_string)
        return HttpResponseRedirect(url)

    if family and family != 'other':
        family = Family.objects.get(pk=family)
        app = family.application
    else:
        family = ''
        app = 'other'
    # For other family search across all other families
    if app == 'other':
        family = ''

    # if suprageneric rank requested
    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily'].strip()
    if subfamily:
        subfamily = Subfamily.objects.get(subfamily=subfamily)
    if 'tribe' in request.GET:
        tribe = request.GET['tribe'].strip()
    if tribe:
        tribe = Tribe.objects.get(tribe=tribe)
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe'].strip()
    if subtribe:
        subtribe = Subtribe.objects.get(subtribe=subtribe)

    spc = spc_string
    if family:
        if family.family == 'Cactaceae':
            species_list = get_species_list('cactaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Orchidaceae':
            species_list = get_species_list('orchidaceae', family, subfamily, tribe, subtribe)
        elif family.family == 'Bromeliaceae':
            species_list = get_species_list('bromeliaceae', family, subfamily, tribe, subtribe)
        else:
            species_list = get_species_list('other')
            species_list = species_list.filter(gen__family=family.family)
    else:
        # In case of app = other, search will scan through every family in the app.
        species_list = get_species_list('other')

    # Perform conventional match
    if not fuzzy:
        # exact match genus, and species from beginning of word
        if genus_string:  # Seach genus table
            min_score = 80
            # Try to match genus
            CaGenus = apps.get_model('cactaceae', 'Genus')
            OrGenus = apps.get_model('orchidaceae', 'Genus')
            OtGenus = apps.get_model('other', 'Genus')
            BrGenus = apps.get_model('bromeliaceae', 'Genus')
            cagenus_list = CaGenus.objects.all()
            cagenus_list = cagenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            orgenus_list = OrGenus.objects.all()
            orgenus_list = orgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            brgenus_list = BrGenus.objects.all()
            brgenus_list = brgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            otgenus_list = OtGenus.objects.all()
            otgenus_list = otgenus_list.values('pid', 'genus', 'family', 'author', 'description', 'num_species', 'num_hybrid', 'status', 'year')
            genus_list = cagenus_list.union(orgenus_list).union(otgenus_list).union(brgenus_list)
            search_list = []
            for x in genus_list:
                if x['genus']:
                    score = fuzz.ratio(x['genus'].lower(), genus_string.lower())
                    if score >= min_score:
                        search_list.append([x, score])

            search_list.sort(key=lambda k: (-k[1], k[0]['genus']))
            del search_list[5:]
            genus_list = search_list
        if single_word:
            #Try to 0match species from all families
            CaSpecies = apps.get_model('cactaceae', 'Species')
            OrSpecies = apps.get_model('orchidaceae', 'Species')
            OtSpecies = apps.get_model('other', 'Species')
            BrSpecies = apps.get_model('bromeliaceae', 'Species')
            caspecies_list = CaSpecies.objects.filter(species__istartswith=spc_string)
            caspecies_list = caspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
            orspecies_list = OrSpecies.objects.filter(species__istartswith=spc_string)
            orspecies_list = orspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
            brspecies_list = BrSpecies.objects.filter(species__istartswith=spc_string)
            brspecies_list = brspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
            otspecies_list = OtSpecies.objects.filter(species__istartswith=spc_string)
            otspecies_list = otspecies_list.values('pid', 'species', 'family', 'genus', 'author', 'status', 'year')
            matched_species_list = caspecies_list.union(orspecies_list).union(otspecies_list).union(brspecies_list)
            for x in matched_species_list:
                if x['species']:
                    score = fuzz.ratio(x['species'].lower(), spc_string.lower())
                    if score >= min_score:
                        match_spc_list.append([x, score])
            match_spc_list.sort(key=lambda k: (-k[1], k[0]['species']))
            # del match_spc_list[5:]

        if not match_spc_list:
            # if no species found (single word) search binomial in other families
            spc_string = spc_string.replace('.', '')
            spc_string = spc_string.replace(' mem ', ' Memoria ')
            spc_string = spc_string.replace(' Mem ', ' Memoria ')
            spc_string = spc_string.replace(' mem. ', ' Memoria ')
            spc_string = spc_string.replace(' Mem. ', ' Memoria ')
            words = spc_string.split()
            grex = spc_string.split(' ', 1)
            if len(grex) > 1:
                grex = grex[1]
            else:
                grex = grex[0]
            # print("spc_string = " + spc_string)
            # print("grex = " + grex)
            if len(words) > 1:
                perfect_list = species_list.filter(binomial__istartswith=spc_string)
            # print("words = " + str(len(words)))
            # print("species_list = " + str(len(species_list)))
            # print("perfect_list = " + str(len(perfect_list)))
            if len(perfect_list) == 0:
                if len(words) == 1:
                    # Single word could be a genus or an epithet
                    match_list = species_list.filter(species__istartswith=grex)
                    # match_list = species_list.filter(species__icontains=grex)
                else:
                    match_list = species_list.filter(Q(binomial__icontains=grex) | Q(binomial__icontains=grex))
                    # match_list = species_list.exclude(binomial=spc_string).filter(Q(binomial__icontains=spc_string) | Q(species__icontains=spc_string) | Q(species__icontains=grex) | Q(infraspe__icontains=words[-1]) | Q(binomial__icontains=grex) | Q(species__icontains=subgrex)  | Q(binomial__icontains=subgrex))
                if len(match_list) == 0:
                    if not genus_list:
                        fuzzy = 1
                        url = "%s?role=%s&app=%s&family=%s&spc_string=%s&fuzzy=1" % (reverse('search:search_species'), role, app, family, spc_string)
                        return HttpResponseRedirect(url)

    # Perform Fuzzy search if requested (fuzzy = 1) or if no species match found:
    else:
        first_try = species_list.filter(species=spc)
        min_score = 60
        for x in species_list:
            if x.binomial:
                score = fuzz.ratio(x.binomial, spc)
                if score >= min_score:
                    fuzzy_list.append([x, score])
        fuzzy_list.sort(key=lambda k: (-k[1], k[0].binomial))
        del fuzzy_list[20:]
    path = 'information'
    if role == 'cur':
        path = 'photos'
    family_list, alpha = get_family_list(request)

    write_output(request, spc_string)
    context = {'spc_string': spc_string, 'genus_list': genus_list, 'match_spc_list': match_spc_list,
               'perfect_list': perfect_list, 'match_list': match_list, 'fuzzy_list': fuzzy_list,
               'genus_total': len(genus_list), 'match_total': len(match_list), 'fuzzy_total': len(fuzzy_list), 'perfect_total': len(perfect_list),
               'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha, 'family': family, 'subfamily': subfamily, 'tribe': tribe, 'subtribe': subtribe,
               'app': app, 'fuzzy': fuzzy, 'single_word': single_word,
               'role': role, 'path': path, 'full_path': full_path}
    return render(request, "search/search_species.html", context)


def getPartialPid(reqgenus, type, status, app):
    if app == 'orchidaceae':
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
        Intragen = apps.get_model(app.lower(), 'Intragen')
        intragen_list = Intragen.objects.all()
        if status == 'synonym' or type == 'hybrid':
            intragen_list = []
    else:
        Genus = apps.get_model(app.lower(), 'Genus')
        Species = apps.get_model(app.lower(), 'Species')
        intragen_list = []

    pid_list = []
    pid_list = Species.objects.filter(type=type)
    pid_list = pid_list.exclude(status='synonym')

    if reqgenus:
        if reqgenus[0] != '*' and reqgenus[-1] != '*':
            try:
                genus = Genus.objects.get(genus=reqgenus)
            except Genus.DoesNotExist:
                genus = ''
            if genus:
                pid_list = pid_list.filter(genus=genus)
                if intragen_list:
                    intragen_list = intragen_list.filter(genus=genus)
            return genus, pid_list, intragen_list

        elif reqgenus[0] == '*' and reqgenus[-1] != '*':
            mygenus = reqgenus[1:]
            pid_list = pid_list.filter(genus__iendswith=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__iendswith=mygenus)

        elif reqgenus[0] != '*' and reqgenus[-1] == '*':
            mygenus = reqgenus[:-1]
            pid_list = pid_list.filter(genus__istartswith=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__istartswith=mygenus)
        elif reqgenus[0] == '*' and reqgenus[-1] == '*':
            mygenus = reqgenus[1:-1]
            pid_list = pid_list.filter(genus__icontains=mygenus)
            if intragen_list:
                intragen_list = intragen_list.filter(genus__icontains=mygenus)
    else:
        reqgenus = ''
    return reqgenus, pid_list, intragen_list


def get_species_list(application, family=None, subfamily=None, tribe=None, subtribe=None):
    Species = apps.get_model(application, 'Species')
    species_list = Species.objects.all()
    if subtribe:
        species_list = species_list.filter(gen__subtribe=subtribe)
    elif tribe:
        species_list = species_list.filter(gen__tribe=tribe)
    elif subfamily:
        species_list = species_list.filter(gen__subfamily=subfamily)
    return species_list
    # return species_list.values('pid', 'binomial', 'author', 'source', 'status', 'type', 'family')


def search_fuzzy(request):
    min_score = 60
    spc_string = ''
    result_list = []
    result_score = []
    Family = apps.get_model('core', 'Family')
    Genus = apps.get_model('orchidaceae', 'Genus')
    Alliance = apps.get_model('orchidaceae', 'Alliance')
    Species = apps.get_model('orchidaceae', 'Species')

    family = 'Orchidaceae'
    if 'family' in request.GET:
        family = request.GET['family']
    elif 'newfamily' in request.GET:
        family = request.GET['newfamily']

    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']

    if request.GET.get('spc_string'):
        spc_string = request.GET['spc_string'].strip()
    send_url = '/search/search_orchid/?spc_string=' + spc_string + "&role=" + role

    if family != 'Orchidaceae':
        url = "%s?role=%s&family=%s&spc_string=%s" % (
        reverse('search:search_species'), role, family, spc_string)
        return HttpResponseRedirect(url)

    grexlist = Species.objects.exclude(status='pending')
    # Filter for partner specific list.

    perfect_list = grexlist
    keyword = spc_string.lower()
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
        score = fuzz.ratio(x.short_grex().lower(), keyword)
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
    family_list, alpha = get_family_list(request)
    family = Family.objects.get(pk='Orchidaceae')

    result_score.sort(key=lambda k: (-k[1], k[0].name()))
    context = {'result_list': result_list,'result_score': result_score, 'len': len(result_list), 'spc_string':  spc_string, 'genus': genus,
               'alliance_obj': alliance_obj, 'genus_obj': genus_obj,
               'min_score': min_score, 'keyword': keyword,
               'family': family, 'family_list': family_list, 'alpha_list': alpha_list, 'alpha': alpha,
               'role': role, 'namespace': 'search',

               }
    return render(request, "search/search_orchid.html", context)


