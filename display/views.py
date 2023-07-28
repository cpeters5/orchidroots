import string
import re
import logging
import random

from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
import django.shortcuts
from itertools import chain
from django.apps import apps
from utils.views import write_output, getRole, get_reqauthor, pathinfo, get_random_sponsor, get_application
from common.views import rank_update, quality_update
from core.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Intragen, HybImages
from accounts.models import User, Photographer, Sponsor

epoch = 1740
logger = logging.getLogger(__name__)
GenusRelation = []
Accepted = []
Synonym = []
f, sf, t, st = '', '', '', ''
redirect_message = 'species does not exist'
# num_show = 5
# page_length = 500


def information(request, pid=None):
    # As of June 2022, synonym will have its own display page
    # NOTE: seed and pollen id must all be accepted.
    from_path = pathinfo(request)
    app, family = get_application(request)
    if app == '':
        return HttpResponseRedirect('/')
    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')
    SpcImages = apps.get_model(app, 'SpcImages')
    Hybrid = apps.get_model(app, 'hybrid')
    AncestorDescendant = apps.get_model(app, 'AncestorDescendant')
    if app == 'orchidaceae':
        HybImages = apps.get_model(app, 'HybImages')
    else:
        HybImages = apps.get_model(app, 'SpcImages')


    ps_list = pp_list = ss_list = sp_list = ()
    max_items = 3000
    ancspc_list = []
    seedimg_list = []
    pollimg_list = []
    distribution_list = []
    if not pid:
        pid = 0
    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')

    related_list = Species.objects.filter(genus=species.genus).filter(species=species.species).exclude(pid=pid).exclude(status='synonym').order_by('binomial')

    # If pid is a synonym, convert to accept
    req_pid = pid
    req_species = species
    genus = species.gen
    display_items = []
    synonym_list = Synonym.objects.filter(acc=pid)
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
            accid = species.getAcc()
            accepted = Species.objects.get(pk=accid).hybrid
    else:
        if req_pid != pid:  # req_pid is a synonym, just show the synonym
            images_list = SpcImages.objects.filter(pid=req_pid).order_by('-rank', 'quality', '?')
        else:               # req_pid is accepted species, show the accepted photos and all of its synonyms photos
            images_list = SpcImages.objects.filter(Q(pid=pid) | Q(pid__in=syn_list)).order_by('-rank', 'quality', '?')
        if species.status == 'synonym':
            accid = species.getAcc()
            myspecies = Species.objects.get(pk=accid)
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
    offspring_list = chain(list(seed_list), list(pollen_list))
    offspring_count = len(seed_list) + len(pollen_list)
    if offspring_count > max_items:
        offspring_list = offspring_list[0:max_items]

    if species.type == 'hybrid':
        if accepted.seed_id and accepted.seed_id.type == 'species':
            seed_obj = Species.objects.get(pk=accepted.seed_id.pid)
            seedimg_list = SpcImages.objects.filter(pid=seed_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
        elif accepted.seed_id and accepted.seed_id.type == 'hybrid':
            seed_obj = Hybrid.objects.get(pk=accepted.seed_id)
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
            pollen_obj = Species.objects.get(pk=accepted.pollen_id.pid)
            pollimg_list = SpcImages.objects.filter(pid=pollen_obj.pid).filter(rank__lt=7).filter(rank__gt=0).order_by('-rank', 'quality', '?')[0: 3]
        elif accepted.pollen_id and accepted.pollen_id.type == 'hybrid':
            pollen_obj = Hybrid.objects.get(pk=accepted.pollen_id)
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

        ancspc_list = AncestorDescendant.objects.filter(did=species.pid).filter(anctype='species').order_by('-pct')
        if ancspc_list:
            for x in ancspc_list:
                img = x.aid.get_best_img()
                if img:
                    x.img = img.image_file
    if req_species.status == 'synonym':
        # if request pid is a synopnym, return the synonym instance
        species = req_species
    # if len(display_items) > 0:
    ads_insert = int(random.random() * len(display_items)) + 1
    sponsor = get_random_sponsor()
    role = ''
    if 'role' in request.GET:
        role = request.GET['role']
    write_output(request, str(family))
    context = {'pid': species.pid, 'species': species, 'synonym_list': synonym_list, 'accepted': accepted,
               'tax': 'active', 'q': species.name, 'type': 'species', 'genus': genus, 'related_list': related_list,
               'display_items': display_items, 'distribution_list': distribution_list, 'family': family,
               'offspring_list': offspring_list, 'offspring_count': offspring_count, 'max_items': max_items,
               'seedimg_list': seedimg_list, 'pollimg_list': pollimg_list, 'role': role,
               'ss_list': ss_list, 'sp_list': sp_list, 'ps_list': ps_list, 'pp_list': pp_list,
               'app': app, 'ancspc_list': ancspc_list, 'ads_insert': ads_insert, 'sponsor': sponsor,
               'from_path': from_path, 'tab': 'rel', 'view': 'information',
               }
    return render(request, "display/information.html", context)


def photos(request, pid=None):
    author = get_reqauthor(request)
    role = ''
    syn = 'N'
    related = ''
    variety = ''
    tail = ''
    if 'role' in request.GET:
        role = request.GET['role']
    if 'syn' in request.GET:
        syn = request.GET['syn']
    if not author or author == 'anonymous':
        author = None
    # author_list = Photographer.objects.all().order_by('displayname')
    app, family = get_application(request)
    if app == '':
        return HttpResponseRedirect('/')
    Species = apps.get_model(app, 'Species')
    Synonym = apps.get_model(app, 'Synonym')
    SpcImages = apps.get_model(app, 'SpcImages')
    if app == 'orchidaceae':
        HybImages = apps.get_model(app, 'HybImages')
    UploadFile = apps.get_model(app, 'UploadFile')

    if not pid and 'pid' in request.GET:
        pid = request.GET['pid']
        if pid:
            pid = int(pid)
        else:
            pid = 0

    try:
        species = Species.objects.get(pk=pid)
    except Species.DoesNotExist:
        return HttpResponseRedirect('/')
    related_list = Species.objects.filter(genus=species.genus).filter(species=species.species).order_by('binomial')
    related_pid = related_list.values_list('pid')
    if 'related' in request.GET:
        related = request.GET['related']
        if related != 'ALL':
            related_pid = [species.pid]

    if species:
        syn_list = Synonym.objects.filter(acc_id__in=related_pid)
        syn_pid = syn_list.values_list('spid')
        if app == 'orchidaceae' and species.type == 'hybrid':
            if syn == 'N':      # input pid is a synonym, just get images of the requested synonym
                public_list = HybImages.objects.filter(pid__in=related_pid)  # public photos
            else:                   # input pid is an accepted species, include images of its synonyms
                public_list = HybImages.objects.filter(Q(pid__in=related_pid) | Q(pid__in=syn_pid))  # public photos
        else:
            if syn == 'N':
                public_list = SpcImages.objects.filter(pid__in=related_pid)  # public photos
            else:
                public_list = SpcImages.objects.filter(Q(pid__in=related_pid) | Q(pid__in=syn_pid))  # public photos
        upload_list = UploadFile.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_pid))  # All upload photos
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            upload_list = upload_list.filter(author=author) # Private photos
            private_list = private_list.filter(author=author) # Private photos

    else:
        private_list = public_list = upload_list = []
    public_list = public_list.filter(rank__gt=0)  # public photos

    # Request rank/quality change.
    # Remove after implementing a dedicated curator task view.
    if app == 'orchidaceae' and species.type == 'hybrid':
        rank_update(request, HybImages)
        quality_update(request, HybImages)
    else:
        rank_update(request, SpcImages)
        quality_update(request, SpcImages)

    # Create lists

    # Handle Variety filter
    rel = ''
    if 'variety' in request.GET:
        variety = request.GET['variety']
        if variety == 'semi alba':
            variety = 'semialba'

    # Extract first term, possibly an infraspecific
    parts = variety.split(' ', 1)
    if len(parts) > 1:
        tail = parts[1]
    var = variety
    if variety and tail:
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
    if private_list and author:
        private_list = private_list.filter(author=author)
    ads_insert = int(random.random() * len(public_list)) + 1
    sponsor = get_random_sponsor()
    write_output(request, str(family))
    context = {'species': species, 'author': author,
               'family': family,
               'variety': variety, 'pho': 'active', 'tab': 'pho', 'app':app, 'related_list': related_list,
               'public_list': public_list, 'private_list': private_list, 'upload_list': upload_list, 'role': role,
               'syn_list': syn_list, 'related': related, 'syn': syn,
               # 'myspecies_list': myspecies_list, 'myhybrid_list': myhybrid_list,
               'ads_insert': ads_insert, 'sponsor': sponsor, 'view': 'photos',
               }
    return render(request, 'display/photos.html', context)
