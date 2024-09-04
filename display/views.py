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


def summary(request, app, pid=None):
    # As of June 2022, synonym will have its own display page
    # NOTE: seed and pollen id must all be accepted.
    #  Handle a faulty url redirection (/display/information/application/1234)
    if app == 'application':
        app = 'orchidaceae'

    if not pid:
        pid = request.GET.get('pid', '')

    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    family = request.GET.get('family', 'Orchidaceae')
    try:
        family = Family.objects.get(family=family)
    except Family.DoesNotExist:
        family = Family.objects.get(family='Orchidaceae')

    if not app:
        app = request.GET.get('app', '')
        if not app:
            app = family.application
        canonical_url = request.build_absolute_uri(f'/display/summary/{app}/{pid}/')
        return HttpResponsePermanentRedirect(canonical_url)

    # Construct the canonical URL
    canonical_url = request.build_absolute_uri(f'/display/summary/{app}/{pid}/')
    # If accessed via query parameter, redirect to the canonical URL
    # TODO - Just orchid for now. Add canonical_url for other app / family later.
    if 'pid' in request.GET:
        return HttpResponsePermanentRedirect(canonical_url)

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

    # Check if there are infraspecific.
    if species.type == 'hybrid' and species.source == 'RHS':
        infraspecifics = 0
        canonical_url = ''
    else:
        this_species_name = species.genus + ' ' + species.species  # ignore infraspecific names
        main_species = Species.objects.filter(binomial=this_species_name)
        if len(main_species) > 0:
            species = main_species[0]
        infraspecifics = len(Species.objects.filter(binomial__istartswith=this_species_name))


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
    role = get_role(request)
    write_output(request, str(family))
    context = {'pid': species.pid, 'species': species,
               'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus,
               'display_items': display_items, 'family': family,
               'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list, 'role': role,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'app': app, 'ancspc_list': ancspc_list, 'infraspecifics': infraspecifics,
               'canonical_url': canonical_url,
               'tab': 'rel', 'view': 'information',
               }
    response = render(request, 'display/summary.html', context)
    return response


def summary_tmp(request, pid=None):
    # As of June 2022, synonym will have its own display page
    # NOTE: seed and pollen id must all be accepted.
    #  Handle a faulty url redirection (/display/information/application/1234)
    app = request.GET.get('app', '')

    if not pid:
        pid = request.GET.get('pid', '')

    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    family = request.GET.get('family', 'Orchidaceae')
    try:
        family = Family.objects.get(family=family)
    except Family.DoesNotExist:
        family = Family.objects.get(family='Orchidaceae')
    app = family.application

    # Construct the canonical URL
    canonical_url = request.build_absolute_uri(f'/display/summary/{app}/{pid}/')
    return HttpResponsePermanentRedirect(canonical_url)


def information(request, pid=None):
    # As of June 2022, synonym will have its own display page
    # NOTE: seed and pollen id must all be accepted.
    if pid is None:
        pid = request.GET.get('pid')

    if not pid or not str(pid).isnumeric():
        handle_bad_request(request)
        return HttpResponseRedirect('/')

    app, family = get_application(request)

    canonical_url = request.build_absolute_uri(f'/display/summary/{app}/{pid}/')

    # If accessed via query parameter, redirect to the canonical URL
    # if family == 'Orchidaceae' and 'pid' in request.GET:
    return HttpResponsePermanentRedirect(canonical_url)


def photos(request, pid=None):
    app = request.GET.get('app')
    if not pid:
        pid = request.GET.get('pid', '')

    if not pid or not str(pid).isnumeric() or app not in applications:
        handle_bad_request(request)
        return HttpResponseRedirect('/')
    # If family is request, find application and use it
    if not app:
        family = request.GET.get('family', 'Orchidaceae')
        try:
            family = Family.objects.get(family=family)
        except Family.DoesNotExist:
            family = Family.objects.get(family='Orchidaceae')
        app = family.application

    canonical_url = request.build_absolute_uri(f'/display/photos/{app}/{pid}/')
    return HttpResponsePermanentRedirect(canonical_url)

def get_role(request):
    role = request.GET.get('role', '')
    if not role and request.user.is_authenticated:
        if not role and request.user.tier.tier >= 3:
            role = 'cur'
        else:
            role = 'pri'
    elif not request.user.is_authenticated:
        role = 'pub'
    return role

def gallery(request, app, pid=None):
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
    private_list = []
    role = get_role(request)
    owner = request.GET.get('owner', '')
    # if not author or author == 'anonymous':
    #     author = None

    # Get application and family

    # Define Species, Synonym and Image classes based on the application
    Species = apps.get_model(app, 'Species')
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    family = species.family
    # for non-orchids request, family can be anything, depending on pid.

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

    canonical_url = request.build_absolute_uri(f'/display/photos/{pid}/?app={app}')

    # For synonym species, just render only synonym images and leave
    if species.status == 'synonym':
        public_list = SpcImages.objects.filter(pid=pid)  # public photos
        private_list = public_list.filter(rank=0)  # rejected photos
        upload_list = UploadFile.objects.filter(pid=pid)  # All upload photos
        context = {'species': species, 'author': author, 'family': family,
                   'pho': 'active', 'tab': 'pho', 'app': app,
                   'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list,
                   'canonical_url': canonical_url,
                   'role': role,
                   }
        return render(request, 'display/photos.html', context)

    public_list = SpcImages.objects.filter(pid=pid)  # public photos

    #     Handle synonyms
    public_pid_list = public_list.values_list('pid', flat=True)
    public_list = SpcImages.objects.filter(pid__in=public_pid_list)

    # Generate upload list, public list and private list
    upload_list = []
    if request.user.is_authenticated:
        upload_list = UploadFile.objects.filter(pid=species.pid)  # All upload photos
        if owner == 'Y':
            if isinstance(author, Photographer):
                public_list = public_list.filter(author=request.user.photographer.author_id)
                upload_list = upload_list.filter(author=request.user.photographer.author_id)
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            upload_list = upload_list.filter(author=request.user.photographer.author_id)  # Private photos
            private_list = private_list.filter(author=request.user.photographer.author_id)  # Private photos

    public_list = public_list.filter(rank__gt=0)  # public photos

    # Extract first word, potentially an infraspecific
    if public_list:
        public_list = public_list.order_by('-rank', 'quality', '?')
        if private_list:
            private_list = private_list.order_by('created_date')

    write_output(request, str(family))
    context = {'species': species, 'author': author,
               'family': family,
               'pho': 'active', 'tab': 'pho', 'app': app,
               'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list, 'role': role,
               'canonical_url': canonical_url,
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
    Video = apps.get_model(app, 'Video')

    try:
        species = Species.objects.get(pk=pid)

    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    # Get synonym list
    # TODO: Get video list from Video class
    if species:
        if species.status != 'synonym':
            video_list = Video.objects.filter(pid=pid)
        else:
            video_list = Video.objects.filter(pid=accpid)

    canonical_url = request.build_absolute_uri(f'/display/video/{pid}/?app={app}')

    write_output(request, str(family))
    context = {'species': species, 'author': author,
               'family': family,
               'vid': 'active', 'tab': 'vid', 'app':app,
               'video_list': video_list,
               'canonical_url': canonical_url,
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
