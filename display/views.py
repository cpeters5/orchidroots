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
from utils.views import write_output, getRole, get_reqauthor, pathinfo, get_application, handle_bad_request
from common.views import rank_update, quality_update
from common.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Intragen, HybImages
from accounts.models import User, Photographer
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


def summary(request, app=None, pid=None):
    if isinstance(app, int):
        pid = app
        app = None
    query_app = request.GET.get('app', None)
    query_pid = request.GET.get('pid', None)
    app = app or query_app
    pid = pid or query_pid

    # Handle an old typo in sitemaps.  Crawlers still crawled these urls
    if app == None or app == 'application':
        app = 'orchidaceae'

    # handle various old paths, will be eventually removed.
    if not pid:
        # Worst case scenario when no explicit pid requested. Send it to homepage.
        return HttpResponsePermanentRedirect(reverse('home'))

    # Either 'app' or pid is from query string, redirect to the canonical URL
    if query_pid != None or app == None:
        app = None or 'orchidaceae'
        return HttpResponsePermanentRedirect(reverse('display:summary', args=[app, pid]))

    # Construct the canonical URL
    canonical_url = request.build_absolute_uri(f'/display/summary/{app}/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')

    Species = apps.get_model(app, 'Species')
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    family = species.family

    # If requested species is a synonym, convert it to accepted species
    req_species = species #(could be synonym of accepted)
    req_pid = pid
    if species.status == 'synonym':
        species =species.getAccepted()
        pid = species.pid

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
    genus = species.gen
    display_items = []
    syn_list = Synonym.objects.filter(acc_id=pid).values_list('spid')

    if species.gen.family.family == 'Orchidaceae' and species.type == 'hybrid':
        images_list = HybImages.objects.filter(pid=req_pid).order_by('-rank', 'quality', '?')
    else:
        if req_species.status == 'synonym':
            images_list = SpcImages.objects.filter(pid=req_pid).order_by('-rank', 'quality', '?')
        else:
            images_list = SpcImages.objects.filter(Q(pid=pid) | Q(pid__in=syn_list)).order_by('-rank', 'quality', '?')

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

    # get infraspecific list if exists
    infra = len(species.get_infraspecifics())

    # If hybrid, find its parents
    if species.type == 'hybrid':
        if species.hybrid.seed_id and species.hybrid.seed_id.type == 'species':
            try:
                seed_obj = Species.objects.get(pk=species.hybrid.seed_id.pid)
            except Species.DoesNotExist:
                seed_obj = ''
            seedimg_list = SpcImages.objects.filter(pid=seed_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
        elif species.hybrid.seed_id and species.hybrid.seed_id.type == 'hybrid':
            try:
                seed_obj = Hybrid.objects.get(pk=species.hybrid.seed_id)
            except Hybrid.DoesNotExist:
                try:
                    seed_obj = Synonym.objects.get(pk=species.hybrid.seed_id.pid)
                    seed_obj = seed_obj.acc.hybrid
                except Synonym.DoesNotExist:
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
        if species.hybrid.pollen_id and species.hybrid.pollen_id.type == 'species':
            try:
                pollen_obj = Species.objects.get(pk=species.hybrid.pollen_id.pid)
            except Species.DoesNotExist:
                pollen_obj = ''
            pollimg_list = SpcImages.objects.filter(pid=pollen_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
        elif species.hybrid.pollen_id and species.hybrid.pollen_id.type == 'hybrid':
            try:
                pollen_obj = Hybrid.objects.get(pk=species.hybrid.pollen_id)
            except Hybrid.DoesNotExist:
                try:
                    pollen_obj = Synonym.objects.get(pk=species.hybrid.pollen_id.pid)
                    pollen_obj = pollen_obj.acc.hybrid
                except Synonym.DoesNotExist:
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

    # determine if synonyms tab is needed
    syn_list = species.get_synonyms()
    synonyms = len(syn_list)

    role = get_role(request)
    write_output(request, str(family) + ' ' + species.binomial)
    context = {'pid': species.pid, 'species': species,
               'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus,
               'display_items': display_items, 'family': family,
               'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list, 'role': role,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'app': app, 'ancspc_list': ancspc_list, 'infra': infra, 'synonyms': synonyms,
               'canonical_url': canonical_url,
               'tab': 'rel', 'view': 'information',
               }
    response = render(request, 'display/summary.html', context)
    return response


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


def photos(request, app=None, pid=None):
    # Cleanup request url
    # Get models
    if isinstance(app, int):
        pid = app
        app = None
    query_app = request.GET.get('app', None)
    query_pid = request.GET.get('pid', None)

    family = request.GET.get('family', None)

    app = app or query_app
    pid = pid or query_pid

    # Old ip /display/photosw/<pid>/?family=Orchidaceae
    # Redirect to /display/photos/orchidaceae/<pid>
    if not app and family:
        if family == 'Orchidaceae':
            app = 'orchidaceae'
        else:
            try:
                family = Family.objects.get(pk=family)
                app = family.application
            except Family.DoesNotExist:
                # Nothing we can do
                return HttpResponsePermanentRedirect(reverse('home'))
        return HttpResponsePermanentRedirect(reverse('display:photos', args=[app, pid]))

    if not pid:
        # Worst case scenario when no explicit pid requested. Send it to homepage.
        return HttpResponsePermanentRedirect(reverse('home'))

    # handle old urls. Either 'app' or pid is from query string, send to the canonical URL
    if query_pid != None or app == None:
        app = None or 'orchidaceae'
        return HttpResponsePermanentRedirect(reverse('display:photos', args=[app, pid]))

    #  Logic starts here
    #  Get author (to enable private photos display)
    author = ''
    if request.user.is_authenticated:
        author = Photographer.objects.filter(user_id=request.user.id)
        if author.exists():
            author = author.first().author_id
    private_list = []
    role = get_role(request)
    owner = request.GET.get('owner', '')

    # Get models
    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')
    UploadFile = apps.get_model(app, 'UploadFile')
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponsePermanentRedirect(reverse('home'))

    # For Orchid, image classes could be species or hybrid depending on species.type
    if app == 'orchidaceae' and species.type == 'hybrid':
        SpcImages = apps.get_model(app, 'HybImages')
    else:
        SpcImages = apps.get_model(app, 'SpcImages')

    # get family
    # for non-orchid request, family is identified by pid.
    family = species.family

    # handle rank and quality update.
    orid = request.GET.get('id', None)
    if orid:
        rank = request.GET.get('rank', None)
        if rank:
            rank_update(rank, orid, SpcImages)

        quality = request.GET.get('quality', None)
        if quality:
            quality_update(quality, orid, SpcImages)

    # Build canonical url
    canonical_url = request.build_absolute_uri(f'/display/photos/{app}/{pid}/').replace('www.orchidroots.com', 'orchidroots.com')

    # For synonym species, just render only synonym images
    if species.status == 'synonym':
        public_list = SpcImages.objects.filter(pid=pid).exclude(status='synonym')  # public photos
        # synonym_pid_list = public_list.values_list('pid', flat=True)
        private_list = public_list.filter(rank=0)  # rejected photos
        upload_list = UploadFile.objects.filter(pid=pid)  # All upload photos
        context = {'species': species, 'author': author, 'family': family,
                   'pho': 'active', 'tab': 'pho', 'app': app,
                   'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list,
                   'canonical_url': canonical_url,
                   'role': role,
                   }
        return render(request, 'display/photos.html', context)

    # Get infraspecific list for species
    pid_list = [pid]
    infra = species.get_infraspecifics()
    if infra:
        pid_list = list(infra.values_list('pid', flat=True).values_list('pid', flat=True))
    infra = len(infra)

    #  For typical photos request (e.g. from navigation tab), include ALL photos, including infraspecifics and synonyms.
    syn = request.GET.get('syn', '')

    syn_list = list(species.get_synonyms().values_list('spid', flat=True))
    synonyms = len(syn_list)
    print("synonyms", syn_list)
    if syn == 'Y':
        # get list of all synonyms of requested species
        if syn_list:
            pid_list = pid_list + syn_list
    pid_list = list(set(pid_list))

    public_list = SpcImages.objects.filter(pid__in=pid_list)
    # Get upload list, public list and private list
    upload_list, private_list = [], []
    if request.user.is_authenticated:
        upload_list = UploadFile.objects.filter(pid=species.pid)  # All upload photos
        if owner == 'Y':
            if isinstance(author, Photographer):
                public_list = public_list.filter(author=request.user.photographer.author_id)
                upload_list = upload_list.filter(author=request.user.photographer.author_id)
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            # This shouldn't happen. Need to change the design: make sure user.role and photographer instance is insync.
            if isinstance(request.user.photographer, Photographer):
                upload_list = upload_list.filter(author=request.user.photographer.author_id)  # Private photos
                private_list = private_list.filter(author=request.user.photographer.author_id)  # Private photos

    if public_list:
        public_list = public_list.exclude(rank=0).order_by('-rank', 'quality', '?')  # public photos
    if private_list:
        private_list = private_list.order_by('created_date')

    # for img in public_list:
    #     print("img", img.id, img.pid, img.get_displayname())
    write_output(request, str(family) + ' ' + species.binomial)
    context = {'species': species, 'author': author,
               'family': family,
               'pho': 'active', 'tab': 'pho', 'app': app,
               'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list, 'role': role,
               'canonical_url': canonical_url,
               'infra': infra, 'synonyms': synonyms,
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

    canonical_url = request.build_absolute_uri(f'/display/video/{pid}/?app={app}').replace('www.orchidroots.com', 'orchidroots.com')

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
