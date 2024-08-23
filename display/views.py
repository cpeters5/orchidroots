import string
import re
import logging
import random
import json
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpRequest
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
import django.shortcuts
from itertools import chain
from django.apps import apps
from utils.views import write_output, getRole, get_reqauthor, pathinfo, get_random_sponsor, get_application, handle_bad_request
from common.views import rank_update, quality_update
from common.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Intragen, HybImages
from accounts.models import User, Photographer, Sponsor
from urllib.parse import urlencode
import utils.config

applications = utils.config.applications

epoch = 1740
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
f, sf, t, st = '', '', '', ''
redirect_message = 'species does not exist'

def is_crawler(request: HttpRequest) -> bool:
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    crawler_patterns = [
        'googlebot', 'bingbot', 'yandexbot', 'duckduckbot', 'baiduspider',
        'yahoo', 'slurp', 'msnbot', 'facebookexternalhit', 'twitterbot'
    ]
    return any(bot in user_agent for bot in crawler_patterns)


def summary(request, application, pid=None):
    print("In summary", request)
    # As of June 2022, synonym will have its own display page
    # NOTE: seed and pollen id must all be accepted.
    #  Handle a faulty url redirection (/display/information/application/1234)
    if application == 'application':
        application = 'orchidaceae'

    if pid is None:
        pid = request.GET.get('pid')

    if not pid or not str(pid).isnumeric() or application not in applications:
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    # Construct the canonical URL
    canonical_url = request.build_absolute_uri(f'/display/summary/{application}/{pid}/')

    Species = apps.get_model(application, 'Species')
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    Synonym = apps.get_model(application, 'Synonym')
    Hybrid = apps.get_model(application, 'hybrid')
    AncestorDescendant = apps.get_model(application, 'AncestorDescendant')

    SpcImages = apps.get_model(application, 'SpcImages')
    if application == 'orchidaceae':
        HybImages = apps.get_model(application, 'HybImages')
    else:
        HybImages = apps.get_model(application, 'SpcImages')

    ps_list = pp_list = ss_list = sp_list = ()
    ancspc_list = []
    seedimg_list = []
    pollimg_list = []

    # If pid is a synonym, convert to accept
    req_pid = pid
    req_species = species
    genus = species.gen
    display_items = []
    pid = species.pid
    syn_list = Synonym.objects.filter(acc_id=req_pid).values_list('spid')

    if species.gen.family.family == 'Orchidaceae' and species.type == 'hybrid':
        if req_pid != pid:  # req_pid is a synonym, just show the synonym
            images_list = HybImages.objects.filter(pid=pid).order_by('-rank', 'quality', '?')
        else:
            images_list = HybImages.objects.filter(Q(pid=pid) | Q(pid__in=syn_list)).order_by('-rank', 'quality', '?')
        if species.status != 'synonym':
            accepted = species.hybrid
        else:
            # accid = species.getAcc()
            # accepted = Species.objects.get(pk=accid).hybrid
            accepted = species.getAccepted().hybrid
    else:
        if req_pid != pid:  # req_pid is a synonym, just show the synonym
            images_list = SpcImages.objects.filter(pid=req_pid).order_by('-rank', 'quality', '?')
        else:               # req_pid is accepted species, show the accepted photos and all of its synonyms photos
            images_list = SpcImages.objects.filter(Q(pid=pid) | Q(pid__in=syn_list)).order_by('-rank', 'quality', '?')
        if species.status == 'synonym':
            accid = species.getAcc()
            try:
                myspecies = Species.objects.get(pk=accid)
            except Species.DoesNotExist:
                myspecies = ''
        else:
            myspecies = species
        if myspecies.type == 'species':
            accepted = myspecies.accepted
        else:
            accepted = myspecies.hybrid

    # Build display in main table
    if images_list:
        i_1, i_2, i_3, i_4, i_5, i_7, i_8 = 0, 0, 0, 0, 0, 0, 0
        for x in images_list:
            if x.rank == 1 and i_1 <= 0:
                i_1 += 1
                display_items.append(x)
            elif x.rank == 2 and i_2 <= 0:
                i_2 += 1
                display_items.append(x)
            elif x.rank == 3 and i_3 <= 1:
                i_3 += 1
                display_items.append(x)
            elif x.rank == 4 and i_4 <= 3:
                i_4 += 1
                display_items.append(x)
            elif x.rank == 5 and i_5 <= 3:
                i_5 += 1
                display_items.append(x)
            elif x.rank == 7 and i_7 <= 2:
                i_7 += 1
                display_items.append(x)
            elif x.rank == 8 and i_8 < 2:
                i_8 += 1
                display_items.append(x)

    if species.type == 'hybrid':
        if accepted.seed_id and accepted.seed_id.type == 'species':
            try:
                seed_obj = Species.objects.get(pk=accepted.seed_id.pid)
            except Species.DoesNotExist:
                seed_obj = ''
            seedimg_list = SpcImages.objects.filter(pid=seed_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
        elif accepted.seed_id and accepted.seed_id.type == 'hybrid':
            try:
                seed_obj = Hybrid.objects.get(pk=accepted.seed_id)
            except Hybrid.DoesNotExist:
                seed_obj = ''
            if seed_obj:
                seedimg_list = HybImages.objects.filter(pid=seed_obj.pid.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
                assert isinstance(seed_obj, object)
                if seed_obj.seed_id:
                    ss_type = seed_obj.seed_id.type
                    if ss_type == 'species':
                        ss_list = SpcImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                    elif ss_type == 'hybrid':
                        ss_list = HybImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                if seed_obj.pollen_id:
                    sp_type = seed_obj.pollen_id.type
                    if sp_type == 'species':
                        sp_list = SpcImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
                    elif sp_type == 'hybrid':
                        sp_list = HybImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
        # Pollen
        if accepted.pollen_id and accepted.pollen_id.type == 'species':
            try:
                pollen_obj = Species.objects.get(pk=accepted.pollen_id.pid)
            except Species.DoesNotExist:
                pollen_obj = ''
            pollimg_list = SpcImages.objects.filter(pid=pollen_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
        elif accepted.pollen_id and accepted.pollen_id.type == 'hybrid':
            try:
                pollen_obj = Hybrid.objects.get(pk=accepted.pollen_id)
            except Hybrid.DoesNotExist:
                pollen_obj = ''
            pollimg_list = HybImages.objects.filter(pid=pollen_obj.pid.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
            if pollen_obj.seed_id:
                ps_type = pollen_obj.seed_id.type
                if ps_type == 'species':
                    ps_list = SpcImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                elif ps_type == 'hybrid':
                    ps_list = HybImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
            if pollen_obj.pollen_id:
                pp_type = pollen_obj.pollen_id.type
                if pp_type == 'species':
                    pp_list = SpcImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                elif pp_type == 'hybrid':
                    pp_list = HybImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]

        if species.status == 'synonym':
            accid = species.getAcc()
            ancspc_list = AncestorDescendant.objects.filter(did=accid).filter(anctype='species').order_by('-pct')
        else:
            ancspc_list = AncestorDescendant.objects.filter(did=species.pid).filter(anctype='species').order_by('-pct')
    if req_species.status == 'synonym':
        # if request pid is a synopnym, return the synonym instance
        species = req_species
    role = request.GET.get('role', None)
    write_output(request, str(application) + " " + str(species))
    context = {'pid': species.pid, 'species': species,
               'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus,
               'display_items': display_items, 'family': species.family,
               'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list, 'role': role,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'app': application, 'ancspc_list': ancspc_list,
               'canonical_url': canonical_url,
               'tab': 'rel', 'view': 'information',
               }
    response = render(request, 'display/summary.html', context)

    # Add Link header
    # response['Link'] = f'<{canonical_url}>; rel="canonical"'

    return response

# Faulty url /information/pid
def xxxinformation_tmp1(request, pid):
    application = 'orchidaceae'
    # Use reverse to generate the correct URL
    corrected_url = f'/display/summary/{application}/{pid}/'

    # Redirect to the corrected URL
    return HttpResponsePermanentRedirect(corrected_url)

# Another faulty url /information/application/1234
def information_tmp(request, application, pid):
    print("In information_tmp", request)
    application = 'orchidaceae'
    # Use reverse to generate the correct URL
    corrected_url = f'/display/summary/{application}/{pid}/'

    # Redirect to the corrected URL
    return HttpResponsePermanentRedirect(corrected_url)

def information(request, pid=None):
    print("In information", request)
    # Will be eventually removed once all requests are permanently redirected to /summay/app/pid
    # As of June 2022, synonym will have its own display page
    # NOTE: seed and pollen id must all be accepted.
    if pid is None:
        pid = request.GET.get('pid')

    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    print("information", request)
    app, family = get_application(request)
    # print("family", family)

    # Try to identify app through family (if available)
    if family:
        try:
            family = Family.objects.get(pk=family)
        except FamilyDoesNotExist:
            # Fall back to defaul if no family found
            family = 'Orchidaceae'
            pass
    if isinstance(family, Family):
        # Get app
        app = family.application
        # print("ready to go on to", app)
        if app != 'orchidaceae':
            # This is from other applications, redirect permanently to where they belong
            corrected_url = f'/display/summary/{app}/{pid}/'
            # print("corrected_url", corrected_url)
            # Redirect to the corrected URL
            return HttpResponsePermanentRedirect(corrected_url)

    # Construct the canonical URL
    # canonical_url = request.build_absolute_uri(f'/display/information/{pid}/')


    # If accessed via query parameter, redirect to the canonical URL
    # TODO - Just orchid for now. Add canonical_url for other app / family later.
    # if family == 'Orchidaceae' and 'pid' in request.GET:
    #     return HttpResponsePermanentRedirect(canonical_url)


    Species = apps.get_model(app, 'Species')
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    Synonym = apps.get_model(app, 'Synonym')
    Hybrid = apps.get_model(app, 'hybrid')
    AncestorDescendant = apps.get_model(app, 'AncestorDescendant')

    SpcImages = apps.get_model(app, 'SpcImages')
    if app == 'orchidaceae':
        HybImages = apps.get_model(app, 'HybImages')
    else:
        HybImages = apps.get_model(app, 'SpcImages')

    ps_list = pp_list = ss_list = sp_list = ()
    ancspc_list = []
    seedimg_list = []
    pollimg_list = []

    # If pid is a synonym, convert to accept
    req_pid = pid
    req_species = species
    genus = species.gen
    display_items = []
    pid = species.pid
    syn_list = Synonym.objects.filter(acc_id=req_pid).values_list('spid')

    if species.gen.family.family == 'Orchidaceae' and species.type == 'hybrid':
        if req_pid != pid:  # req_pid is a synonym, just show the synonym
            images_list = HybImages.objects.filter(pid=pid).order_by('-rank', 'quality', '?')
        else:
            images_list = HybImages.objects.filter(Q(pid=pid) | Q(pid__in=syn_list)).order_by('-rank', 'quality', '?')
        if species.status != 'synonym':
            accepted = species.hybrid
        else:
            # accid = species.getAcc()
            # accepted = Species.objects.get(pk=accid).hybrid
            accepted = species.getAccepted().hybrid
    else:
        if req_pid != pid:  # req_pid is a synonym, just show the synonym
            images_list = SpcImages.objects.filter(pid=req_pid).order_by('-rank', 'quality', '?')
        else:               # req_pid is accepted species, show the accepted photos and all of its synonyms photos
            images_list = SpcImages.objects.filter(Q(pid=pid) | Q(pid__in=syn_list)).order_by('-rank', 'quality', '?')
        if species.status == 'synonym':
            accid = species.getAcc()
            print("accid", accid)
            try:
                myspecies = Species.objects.get(pk=accid)
            except Species.DoesNotExist:
                myspecies = ''
        else:
            myspecies = species
        if myspecies.type == 'species':
            accepted = myspecies.accepted
        else:
            accepted = myspecies.hybrid

    # Build display in main table
    if images_list:
        i_1, i_2, i_3, i_4, i_5, i_7, i_8 = 0, 0, 0, 0, 0, 0, 0
        for x in images_list:
            if x.rank == 1 and i_1 <= 0:
                i_1 += 1
                display_items.append(x)
            elif x.rank == 2 and i_2 <= 0:
                i_2 += 1
                display_items.append(x)
            elif x.rank == 3 and i_3 <= 1:
                i_3 += 1
                display_items.append(x)
            elif x.rank == 4 and i_4 <= 3:
                i_4 += 1
                display_items.append(x)
            elif x.rank == 5 and i_5 <= 3:
                i_5 += 1
                display_items.append(x)
            elif x.rank == 7 and i_7 <= 2:
                i_7 += 1
                display_items.append(x)
            elif x.rank == 8 and i_8 < 2:
                i_8 += 1
                display_items.append(x)
    # Build parents display for Orchidaceae hybrid  only
    seed_list = Hybrid.objects.filter(seed_id=species.pid).order_by('pollen_genus', 'pollen_species')
    pollen_list = Hybrid.objects.filter(pollen_id=species.pid)
    # Remove duplicates. i.e. if both parents are synonym.
    temp_list = pollen_list
    pollen_list = pollen_list.order_by('seed_genus', 'seed_species')

    if species.type == 'hybrid':
        if accepted.seed_id and accepted.seed_id.type == 'species':
            try:
                seed_obj = Species.objects.get(pk=accepted.seed_id.pid)
            except Species.DoesNotExist:
                seed_obj = ''
            seedimg_list = SpcImages.objects.filter(pid=seed_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
        elif accepted.seed_id and accepted.seed_id.type == 'hybrid':
            try:
                seed_obj = Hybrid.objects.get(pk=accepted.seed_id)
            except Hybrid.DoesNotExist:
                seed_obj = ''
            if seed_obj:
                seedimg_list = HybImages.objects.filter(pid=seed_obj.pid.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
                assert isinstance(seed_obj, object)
                if seed_obj.seed_id:
                    ss_type = seed_obj.seed_id.type
                    if ss_type == 'species':
                        ss_list = SpcImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                    elif ss_type == 'hybrid':
                        ss_list = HybImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                if seed_obj.pollen_id:
                    sp_type = seed_obj.pollen_id.type
                    if sp_type == 'species':
                        sp_list = SpcImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
                    elif sp_type == 'hybrid':
                        sp_list = HybImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
        # Pollen
        if accepted.pollen_id and accepted.pollen_id.type == 'species':
            try:
                pollen_obj = Species.objects.get(pk=accepted.pollen_id.pid)
            except Species.DoesNotExist:
                pollen_obj = ''
            pollimg_list = SpcImages.objects.filter(pid=pollen_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
        elif accepted.pollen_id and accepted.pollen_id.type == 'hybrid':
            try:
                pollen_obj = Hybrid.objects.get(pk=accepted.pollen_id)
            except Hybrid.DoesNotExist:
                pollen_obj = ''
            pollimg_list = HybImages.objects.filter(pid=pollen_obj.pid.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
            if pollen_obj.seed_id:
                ps_type = pollen_obj.seed_id.type
                if ps_type == 'species':
                    ps_list = SpcImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                elif ps_type == 'hybrid':
                    ps_list = HybImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
            if pollen_obj.pollen_id:
                pp_type = pollen_obj.pollen_id.type
                if pp_type == 'species':
                    pp_list = SpcImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                elif pp_type == 'hybrid':
                    pp_list = HybImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]

        if species.status == 'synonym':
            accid = species.getAcc()
            ancspc_list = AncestorDescendant.objects.filter(did=accid).filter(anctype='species').order_by('-pct')
        else:
            ancspc_list = AncestorDescendant.objects.filter(did=species.pid).filter(anctype='species').order_by('-pct')
    if req_species.status == 'synonym':
        # if request pid is a synopnym, return the synonym instance
        species = req_species
    role = request.GET.get('role', None)
    write_output(request, str(family))
    context = {'pid': species.pid, 'species': species,
               'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus,
               'display_items': display_items, 'family': species.family,
               'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list, 'role': role,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'app': app, 'ancspc_list': ancspc_list,
               # 'canonical_url': canonical_url,
               'tab': 'rel', 'view': 'information',
               }
    response = render(request, 'display/information.html', context)

    # Add Link header
    # response['Link'] = f'<{canonical_url}>; rel="canonical"'

    return response


def xinformation(request, pid=None):
    # As of June 2022, synonym will have its own display page
    # NOTE: seed and pollen id must all be accepted.
    author = ''
    if pid is None:
        pid = request.GET.get('pid')
    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    # Construct the canonical URL
    # canonical_url = request.build_absolute_uri(f'/display/information/{pid}/')
    canonical_url = reverse('display:information', kwargs={'pid': pid})
    full_canonical_url = request.build_absolute_uri(canonical_url)

    if request.build_absolute_uri() != full_canonical_url:
        return HttpResponsePermanentRedirect(full_canonical_url)

    # If accessed via query parameter, redirect to the canonical URL
    if 'pid' in request.GET:
        return HttpResponsePermanentRedirect(canonical_url)

    app, family = get_application(request)

    Species = apps.get_model(app, 'Species')
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    Synonym = apps.get_model(app, 'Synonym')
    Hybrid = apps.get_model(app, 'hybrid')
    AncestorDescendant = apps.get_model(app, 'AncestorDescendant')

    SpcImages = apps.get_model(app, 'SpcImages')
    if app == 'orchidaceae':
        HybImages = apps.get_model(app, 'HybImages')
    else:
        HybImages = apps.get_model(app, 'SpcImages')

    ps_list = pp_list = ss_list = sp_list = ()
    ancspc_list = []
    seedimg_list = []
    pollimg_list = []
    images_list = []

    # If pid is a synonym, convert to accept
    req_pid = pid
    req_species = species
    genus = species.gen
    display_items = []
    pid = species.pid

    syn_list = Synonym.objects.filter(acc_id=req_pid).values_list('spid')

    if is_crawler(request):
        if species.gen.family.family == 'Orchidaceae' and species.type == 'hybrid':
            if req_pid != pid:  # req_pid is a synonym, just show the synonym
                images_list = HybImages.objects.filter(pid=pid).order_by('-rank', 'quality', '?')
            else:
                images_list = HybImages.objects.filter(Q(pid=pid) | Q(pid__in=syn_list)).order_by('-rank', 'quality', '?')

            if species.status != 'synonym':
                accepted = species.hybrid
            else:
                # accid = species.getAcc()
                # accepted = Species.objects.get(pk=accid).hybrid
                accepted = species.getAccepted().hybrid
        else:
            if req_pid != pid:  # req_pid is a synonym, just show the synonym
                images_list = SpcImages.objects.filter(pid=req_pid).order_by('-rank', 'quality', '?')
            else:               # req_pid is accepted species, show the accepted photos and all of its synonyms photos
                images_list = SpcImages.objects.filter(Q(pid=pid) | Q(pid__in=syn_list)).order_by('-rank', 'quality', '?')
            if species.status == 'synonym':
                accid = species.getAcc()
                print("accid", accid)
                try:
                    myspecies = Species.objects.get(pk=accid)
                except Species.DoesNotExist:
                    myspecies = ''
            else:
                myspecies = species
            if myspecies.type == 'species':
                accepted = myspecies.accepted
            else:
                accepted = myspecies.hybrid

        # Build display in main table
        if images_list:
            i_1, i_2, i_3, i_4, i_5, i_7, i_8 = 0, 0, 0, 0, 0, 0, 0
            for x in images_list:
                if x.rank == 1 and i_1 <= 0:
                    i_1 += 1
                    display_items.append(x)
                elif x.rank == 2 and i_2 <= 0:
                    i_2 += 1
                    display_items.append(x)
                elif x.rank == 3 and i_3 <= 1:
                    i_3 += 1
                    display_items.append(x)
                elif x.rank == 4 and i_4 <= 3:
                    i_4 += 1
                    display_items.append(x)
                elif x.rank == 5 and i_5 <= 3:
                    i_5 += 1
                    display_items.append(x)
                elif x.rank == 7 and i_7 <= 2:
                    i_7 += 1
                    display_items.append(x)
                elif x.rank == 8 and i_8 < 2:
                    i_8 += 1
                    display_items.append(x)

        if species.type == 'hybrid':
            if accepted.seed_id and accepted.seed_id.type == 'species':
                try:
                    seed_obj = Species.objects.get(pk=accepted.seed_id.pid)
                except Species.DoesNotExist:
                    seed_obj = ''
                seedimg_list = SpcImages.objects.filter(pid=seed_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
            elif accepted.seed_id and accepted.seed_id.type == 'hybrid':
                try:
                    seed_obj = Hybrid.objects.get(pk=accepted.seed_id)
                except Hybrid.DoesNotExist:
                    seed_obj = ''
                if seed_obj:
                    seedimg_list = HybImages.objects.filter(pid=seed_obj.pid.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
                    assert isinstance(seed_obj, object)
                    if seed_obj.seed_id:
                        ss_type = seed_obj.seed_id.type
                        if ss_type == 'species':
                            ss_list = SpcImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                        elif ss_type == 'hybrid':
                            ss_list = HybImages.objects.filter(pid=seed_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                    if seed_obj.pollen_id:
                        sp_type = seed_obj.pollen_id.type
                        if sp_type == 'species':
                            sp_list = SpcImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
                        elif sp_type == 'hybrid':
                            sp_list = HybImages.objects.filter(pid=seed_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?')[: 1]
            # Pollen
            if accepted.pollen_id and accepted.pollen_id.type == 'species':
                try:
                    pollen_obj = Species.objects.get(pk=accepted.pollen_id.pid)
                except Species.DoesNotExist:
                    pollen_obj = ''
                pollimg_list = SpcImages.objects.filter(pid=pollen_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
            elif accepted.pollen_id and accepted.pollen_id.type == 'hybrid':
                try:
                    pollen_obj = Hybrid.objects.get(pk=accepted.pollen_id)
                except Hybrid.DoesNotExist:
                    pollen_obj = ''
                pollimg_list = HybImages.objects.filter(pid=pollen_obj.pid.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
                if pollen_obj.seed_id:
                    ps_type = pollen_obj.seed_id.type
                    if ps_type == 'species':
                        ps_list = SpcImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                    elif ps_type == 'hybrid':
                        ps_list = HybImages.objects.filter(pid=pollen_obj.seed_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                if pollen_obj.pollen_id:
                    pp_type = pollen_obj.pollen_id.type
                    if pp_type == 'species':
                        pp_list = SpcImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]
                    elif pp_type == 'hybrid':
                        pp_list = HybImages.objects.filter(pid=pollen_obj.pollen_id.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[: 1]

        if species.status == 'synonym':
            accid = species.getAcc()
            ancspc_list = AncestorDescendant.objects.filter(did=accid).filter(anctype='species').order_by('-pct')
        else:
            ancspc_list = AncestorDescendant.objects.filter(did=species.pid).filter(anctype='species').order_by('-pct')
        if req_species.status == 'synonym':
            # if request pid is a synopnym, return the synonym instance
            species = req_species
    role = request.GET.get('role', None)
    write_output(request, str(family))
    context = {'pid': species.pid, 'species': species,
               'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus,
               'display_items': display_items, 'family': family,
               'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list, 'role': role,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'app': app, 'ancspc_list': ancspc_list,
               'canonical_url': full_canonical_url,
               'tab': 'rel', 'view': 'information',
               }
    response = render(request, 'display/information.html', context)

    # Add Link header
    # response['Link'] = f'<{canonical_url}>; rel="canonical"'

    return response


def photos(request, pid=None):
    print("In photos", request)
    author = ''
    if pid is None:
        pid = request.GET.get('pid')
    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    if request.user.is_authenticated:
        author = Photographer.objects.filter(user_id=request.user.id)
        if author.exists():
            author = author.first().author_id
    related = ''
    related_species = ''
    related_pids = []
    private_list = []
    variety = ''
    tail = ''
    role = request.GET.get('role', None)
    syn = request.GET.get('syn', None)
    owner = request.GET.get('owner', None)
    # if not author or author == 'anonymous':
    #     author = None

    # Get application and family
    print("photos", request)

    app, family = get_application(request)

    # Define Species, Synonym and Image classes based on the application
    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')
    syn_list = Synonym.objects.filter(acc_id=pid)
    syn_pid = list(syn_list.values_list('spid', flat=True))

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')
    # for non-orchids request, family can be anything, depending on pid.
    if not family:
        family = species.gen.family

    # For Orchid, image classes could be species or hybrid depending on species.type
    if app == 'orchidaceae' and species.type == 'hybrid':
        SpcImages = apps.get_model(app, 'HybImages')
    else:
        SpcImages = apps.get_model(app, 'SpcImages')
    UploadFile = apps.get_model(app, 'UploadFile')

    # handle rank and quality update.
    orid = request.GET.get('id', None)
    if orid:
        rank = request.GET.get('rank', None)
        if rank:
            rank_update(rank, orid, SpcImages)

        quality = request.GET.get('quality', None)
        if quality:
            quality_update(quality, orid, SpcImages)

    # For synonym species, just render only synonym images and leave
    if species.status == 'synonym':
        public_list = SpcImages.objects.filter(pid=pid)  # public photos
        private_list = public_list.filter(rank=0)  # rejected photos
        upload_list = UploadFile.objects.filter(pid=pid)  # All upload photos
        context = {'species': species, 'author': author, 'family': family,
                   'variety': variety, 'pho': 'active', 'tab': 'pho', 'app': app,
                   'public_list': public_list, 'private_list': private_list,
                   'upload_list': upload_list,
                   'related': related, 'syn': syn, 'role': role,
                   }
        return render(request, 'display/photos.html', context)

    # For accepted species, generate synonym list, related list for dropdown menu
    this_species_name = species.genus + ' ' + species.species  # ignore infraspecific names
    if species.type != 'hybrid' or species.infraspe:
        #  This inclusion of infraspe is to add natural hybrid with infraspecific name
        related_list = Species.objects.filter(binomial__istartswith=this_species_name).exclude(type='hybrid').exclude(
            status='synonym')
    else:
        related_list = Species.objects.filter(binomial=this_species_name).exclude(type='species', status='synonym')

    # Now if related parameter is requested
    related = request.GET.get('related', '')
    if related == 'ALL' or not related.isnumeric():
        #  Include all infraspecifics
        related_pids = related_list.values_list('pid', flat=True)
        related = None
        related_species = None

    if related:
        try:
            related_species = Species.objects.get(pk=related)
        except Species.DoesNotExist:
            related_species = None

    # Now generate synonym list
    # syn_list = Synonym.objects.filter(acc_id=pid)
    # syn_pid = list(syn_list.values_list('spid', flat=True))
    if related_species:
        public_list = SpcImages.objects.filter(pid=related_species.pid)  # public photos
    elif len(related_list) > 0:
        public_list = SpcImages.objects.filter(pid__in=related_pids)  # public photos
    else:
        public_list = SpcImages.objects.filter(pid=pid)  # public photos
    if syn == 'Y':
        public_pid_list = public_list.values_list('pid', flat=True)
        public_list = SpcImages.objects.filter(Q(pid__in=public_pid_list) | Q(pid__in=syn_pid))

    # Generate upload list, public list and private list
    upload_list = []
    if request.user.is_authenticated:
        upload_list = UploadFile.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_pid))  # All upload photos
        if owner == 'Y':
            if isinstance(author, Photographer):
                public_list = public_list.filter(author=request.user.photographer.author_id)
                upload_list = upload_list.filter(author=request.user.photographer.author_id)
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            upload_list = upload_list.filter(author=request.user.photographer.author_id)  # Private photos
            private_list = private_list.filter(author=request.user.photographer.author_id)  # Private photos

    public_list = public_list.filter(rank__gt=0)  # public photos

    # Handle Variety filter
    variety = request.GET.get('variety', None)
    if variety == 'semi alba':
        variety = 'semialba'

    # Extract first word, potentially an infraspecific
    parts = ()
    if variety:
        parts = variety.split(' ', 1)
    if len(parts) > 1:
        tail = parts[1]
    var = variety
    if variety and tail:
        # TODO: Replace this with binomial filter
        public_list = public_list.filter(Q(variation__icontains=var) | Q(form__icontains=var) | Q(name__icontains=var)
                                         | Q(source_file_name__icontains=var) | Q(description__icontains=var)
                                         | Q(variation__icontains=tail) | Q(form__icontains=tail)
                                         | Q(name__icontains=tail) | Q(source_file_name__icontains=tail)
                                         | Q(description__icontains=tail))
    elif variety:
        public_list = public_list.filter(Q(variation__icontains=var) | Q(form__icontains=var) | Q(name__icontains=var)
                                         | Q(source_file_name__icontains=var) | Q(description__icontains=var))
    if public_list:
        if var == "alba":
            public_list = public_list.exclude(variation__icontains="semi")
        public_list = public_list.order_by('-rank', 'quality', '?')
        if private_list:
            private_list = private_list.order_by('created_date')

    write_output(request, str(family))
    context = {'species': species, 'author': author,
               'family': family,
               'variety': variety, 'pho': 'active', 'tab': 'pho', 'app': app, 'related_list': related_list,
               'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list, 'role': role,
               'syn_list': syn_list, 'related': related, 'syn': syn,
               'owner': owner,
               }
    return render(request, 'display/photos.html', context)


def videos(request, pid):
    author = get_reqauthor(request)
    accpid = 0
    syn = request.GET.get('syn', None)
    if not author or author == 'anonymous':
        author = None
    # author_list = Photographer.objects.all().order_by('displayname')
    app, family = get_application(request)
    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')
    Video = apps.get_model(app, 'Video')

    try:
        species = Species.objects.get(pk=pid)

    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    # Get synonym list
    # TODO: Get video list from Video class
    if species:
        if species.status != 'synonym':
            syn_list = Synonym.objects.filter(acc_id=pid)
            related_list = Species.objects.filter(genus=species.genus).filter(species=species.species).order_by(
                'binomial')
            # video_list = []
            video_list = Video.objects.filter(pid=pid)
        else:
            syn_list = Synonym.objects.filter(acc_id=accpid)
            video_list = Video.objects.filter(pid=accpid)
            accpid = Synonym.objects.get(pk=pid).acc_id
            accspecies = Species.objects.get(pk=accpid)
            related_list = Species.objects.filter(genus=accspecies.genus).filter(species=accspecies.species).order_by('binomial')

    write_output(request, str(family))
    context = {'species': species, 'author': author,
               'family': family,
               'vid': 'active', 'tab': 'vid', 'app':app,
               'video_list': video_list,
               'related_list': related_list, 'syn_list': syn_list,
               'view': 'videos',
               }
    return render(request, 'display/videos.html', context)


import openai

# Set your OpenAI API key here
openai.api_key = settings.OPENAI_API_KEY

def generate_image(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        try:
            response = openai.Image.create(
                model="image-dalle-2",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
            return render(request, 'your_template.html', {'image_url': image_url})
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")

    return render(request, 'your_form_template.html')
