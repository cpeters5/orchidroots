from django.shortcuts import render
import logging
import os
import shutil
import shortuuid
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_GET
# from django.core.urlresolvers import resolve
from django.db.models import Q
from django.http import HttpResponse
from django.urls import resolve, get_resolver, URLResolver, URLPattern
from django.apps import apps

from common.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Species, UploadFile, SpcImages, HybImages
from accounts.models import Photographer

logger = logging.getLogger(__name__)
import utils.config
applications = utils.config.applications


def regenerate_file(source_path, destination_folder):
    filename = os.path.basename(source_path)
    while True:
        # Generate a new unique filename using shortuuid
        unique_filename = shortuuid.uuid() + "_" + filename
        destination_path = os.path.join(destination_folder, unique_filename)

        # Check if the destination file already exists
        if not os.path.exists(destination_path):
            # If it doesn't exist, copy the file
            shutil.copy(source_path, destination_path)
            print(f"File regenerated successfully: {destination_path}")
            break
        else:
            print(f"Filename already exists: {unique_filename}. Regenerating...")

    return unique_filename


def pathinfo(request):
    path  = request.path.split('/')[2:][0]
    return path


def get_random_sponsor():
    from accounts.models import Sponsor
    from django.utils.timezone import datetime
    today = datetime.today().date()
    sponsors = Sponsor.objects.filter(is_active=1).filter(end_date__gte=today).order_by('?')[0:1]
    sponsor = None
    if sponsors:
        sponsor = sponsors[0]
    return sponsor


def get_searchdata(request):
    selected_app = ''
    area = ''
    if 'selected_app' in request.POST:
        selected_app = request.POST['selected_app']
    elif 'selected_app' in request.GET:
        selected_app = request.GET['selected_app']
    # else:
    #     area = ''

    if 'area' in request.POST:
        area = request.POST['area'].strip()
    elif 'area' in request.GET:
        area = request.GET['area'].strip()
    # else:
    #     area = ''

    return selected_app, area


def xget_searchdata(request):
    searchdata = 0

    if 'searchdata' in request.POST:
        searchdata = request.POST['searchdata']
    elif 'searchdata' in request.GET:
        searchdata = request.GET['searchdata']

    option_mapping = {
        1: ('', 'name'),
        2: ('', 'taxon'),
        3: ('aves', 'name'),
        4: ('aves', 'taxon'),
        5: ('animalia', 'name'),
        6: ('animalia', 'taxon'),
        7: ('fungi', 'name'),
        8: ('fungi', 'taxon'),
        9: ('other', 'name'),
        10: ('other', 'taxon'),
        11: ('orchidaceae', 'name'),
        12: ('orchidaceae', 'taxon')
    }
    selected_app, area = option_mapping.get(searchdata, (None,None))
    return selected_app, area


def get_application(request):
    family = request.GET.get('family', None)
    try:
        family = Family.objects.get(family=family)
        if family != '' and family.family != 'Orchidaceae':
            crit = 1
        app = family.application
    except Family.DoesNotExist:
        family = None
        app = None

    if not family:
        app = request.GET.get('app', None)
        if app not in applications:
            app = None
    return app, family


def get_taxonomy(request):
    alpha = request.GET.get('alpha', '')
    app = request.GET.get('app', None)
    if app not in applications:
        app = None

    if not app:
        family = request.GET.get('family', none)
        if family:
            try:
                family = Family.objects.get(family=family)
                app = family.application
            except Family.DoesNotExist:
                return [], alpha
        else:
            return [], alpha

    family_list = Family.objects.filter(application=app)

    if alpha != '':
        family_list = family_list.filter(family__istartswith=alpha)
    # favorite = Family.objects.filter(family__in=('Orchidaceae'))
    # family_list = favorite.union(family_list)
    return family_list, alpha


def getApp(request):
    return request.resolver_match.app_name


def write_output(request, detail=None):
    if str(request.user) != 'chariya' and request.user.is_authenticated:
        message = "ACCESS: " + request.path + " - " + str(request.user)
        if detail:
            message += " - " + detail
        logger.warn(message)
    return


def get_author(request):
    if not request.user.is_authenticated or request.user.tier.tier < 2:
        return None, None

    author_list = Photographer.objects.exclude(user_id__isnull=True).order_by('displayname')
    author = request.user.photographer.author_id
    author = request.GET.get('author', None)
    if request.user.tier.tier > 2 and 'author':
        try:
            author = Photographer.objects.get(pk=author)
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')
    elif request.user.tier.tier == 2:
        try:
            author = Photographer.objects.filter(user_id=request.user.id)[0]
        except Photographer.DoesNotExist:
            author = Photographer.objects.get(author_id='anonymous')

    return author, author_list

def get_reqauthor(request):
    author = None
    if request.user.is_authenticated:
        if request.user.tier.tier > 2:
            author = request.GET.get('author', None)
            if author == "---" or author == '':
                author = None
            if author:
                try:
                    author = Photographer.objects.get(pk=author)
                except Photographer.DoesNotExist:
                    author = None
        elif request.user.tier.tier > 1:
            try:
                author = Photographer.objects.get(user_id=request.user)
            except Photographer.DoesNotExist:
                author = None
    return author



def imgdir():
    imgdir = 'utils/images/'
    hybdir = imgdir + 'hybrid/'
    spcdir = imgdir + 'species/'
    return imgdir, hybdir, spcdir


# Return best image file for a species object
def get_random_img(spcobj):
    if spcobj.get_best_img():
        spcobj.img = spcobj.get_best_img().image_file
    else:
        spcobj.img = 'noimage_light.jpg'
    return spcobj.img


def is_int(s):
    try:
        int(s)
    except ValueError:
        return False
    return True


def paginator(request, full_list, page_length, num_show):
    page_list = []
    first_item = 0
    last_item = 0
    next_page = 0
    prev_page = 0
    last_page = 0
    page = 0
    page_range = 0
    total = len(full_list)
    if page_length > 0:
        paginator = Paginator(full_list, page_length)
        page = int(request.GET.get('page', '1'))

        try:
            page_list = paginator.page(page)
            last_page = paginator.num_pages
        except EmptyPage:
            page_list = paginator.page(1)
            last_page = 1
        next_page = page + 1
        if next_page > last_page:
            next_page = last_page
        prev_page = page - 1
        if prev_page < 1:
            prev_page = 1

        first_item = (page - 1) * page_length + 1
        last_item = first_item + page_length - 1
        if last_item > total:
            last_item = total
        # Get the index of the current page
        index = page_list.number - 1  # edited to something easier without index
        # This value is maximum index of your pages, so the last page - 1
        max_index = len(paginator.page_range)
        # You want a range of 7, so lets calculate where to slice the list
        start_index = index - num_show if index >= num_show else 0
        end_index = index + num_show if index <= max_index - num_show else max_index
        # My new page range
        page_range = paginator.page_range[start_index: end_index]
    return page_range, page_list, last_page, next_page, prev_page, page_length, page, first_item, last_item


def getRole(request):
    role = request.GET.get('role', None)
    if not role and 'role' in request.POST:
        role = request.POST['role']
        if not role:
            role = none
    if request.user.is_authenticated:
        if not role:
            if request.user.tier.tier < 2:
                role = 'pub'
            elif request.user.tier.tier == 2:
                # Tier 2 users (private) role default to private
                role = 'pri'
            else:
                role = 'cur'
        return role
    return 'pub'

# def getOtherModels(request, family=None):
#     app, subfamily, tribe, subtribe = '', '', '', ''
#     if not family:
#         family = request.GET.get('family', None)
#         if not family and 'family' in request.POST:
#             family = request.POST['family']
#
#     if family != 'other':
#         try:
#             family = Family.objects.get(pk=family)
#             app = family.application
#         except Family.DoesNotExist:
#             family = ''
#             app = 'other'
#     else:
#         family = ''
#         app = 'other'
#
#     if 'subfamily' in request.GET:
#         subfamily = request.GET['subfamily']
#         if subfamily:
#             try:
#                 subfamily = Subfamily.objects.get(pk=subfamily)
#             except Subfamily.DoesNotExist:
#                 subfamily = ''
#             if subfamily.family:
#                 family = subfamily.family
#     if 'tribe' in request.GET:
#         tribe = request.GET['tribe']
#         if tribe:
#             try:
#                 tribe = Tribe.objects.get(pk=tribe)
#             except Tribe.DoesNotExist:
#                 tribe = ''
#             if tribe.subfamily:
#                 subfamily = tribe.subfamily
#             if subfamily.family:
#                 family = tribe.subfamily.family
#     if 'subtribe' in request.GET:
#         subtribe = request.GET['subtribe']
#         if subtribe:
#             try:
#                 subtribe = Subtribe.objects.get(pk=subtribe)
#             except Subtribe.DoesNotExist:
#                 subtribe = ''
#             if subtribe.tribe:
#                 tribe = subtribe.tribe
#             if tribe.subfamily:
#                 subfamily = tribe.subfamily
#             if subfamily.family:
#                 family = subfamily.family
#     Genus = ''
#     Species = ''
#     Accepted = ''
#     Hybrid = ''
#     Synonym = ''
#     Distribution = ''
#     SpcImages = ''
#     HybImages = ''
#     UploadFile = ''
#     Intragen = ''
#     if app:
#         if app == 'orchidaceae':
#             from detail.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm
#             # only exist for orchidaceae
#             GenusRelation = apps.get_model(app.lower(), 'GenusRelation')
#             HybImages = apps.get_model(app.lower(), 'HybImages')
#             Intragen = apps.get_model(app.lower(), 'Intragen')
#         else:
#             HybImages = apps.get_model(app.lower(), 'SpcImages')
#         Genus = apps.get_model(app.lower(), 'Genus')
#         Hybrid = apps.get_model(app.lower(), 'Hybrid')
#         Species = apps.get_model(app.lower(), 'Species')
#         Accepted = apps.get_model(app.lower(), 'Accepted')
#         Ancestordescendant = apps.get_model(app.lower(), 'AncestorDescendant')
#         Synonym = apps.get_model(app.lower(), 'Synonym')
#         Distribution = apps.get_model(app.lower(), 'Distribution')
#         SpcImages = apps.get_model(app.lower(), 'SpcImages')
#         UploadFile = apps.get_model('common', 'UploadFile')
#     return Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen


# def getModels(request, family=None):
#     app = request.GET.get('app', None)
#     family = request.GET.get('family', None)
#     if 'family' in request.POST:
#         family = request.POST['family']
#     try:
#         family = Family.objects.get(pk=family)
#         if not app:
#             app = family.application
#     except Family.DoesNotExist:
#         family = ''
#         if not app:
#             app = 'other'
#
#     subfamily = request.GET.get('subfamily', None)
#     if subfamily:
#         try:
#             subfamily = Subfamily.objects.get(pk=subfamily)
#         except Subfamily.DoesNotExist:
#             subfamily = ''
#         if subfamily.family:
#             family = subfamily.family
#     tribe = request.GET.get('tribe', None)
#     if tribe:
#         try:
#             tribe = Tribe.objects.get(pk=tribe)
#         except Tribe.DoesNotExist:
#             tribe = ''
#         if tribe.subfamily:
#             subfamily = tribe.subfamily
#         if subfamily.family:
#             family = tribe.subfamily.family
#
#     subtribe = request.GET.get('subtribe', None)
#     if subtribe:
#         try:
#             subtribe = Subtribe.objects.get(pk=subtribe)
#         except Subtribe.DoesNotExist:
#             subtribe = ''
#         if subtribe.tribe:
#             tribe = subtribe.tribe
#         if tribe.subfamily:
#             subfamily = tribe.subfamily
#         if subfamily.family:
#             family = subfamily.family
#     Genus = ''
#     Species = ''
#     Accepted = ''
#     Hybrid = ''
#     Synonym = ''
#     Distribution = ''
#     SpcImages = ''
#     HybImages = ''
#     UploadFile = ''
#     Intragen = ''
#     if app:
#         if app == 'orchidaceae':
#             from detail.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm
#             # only exist for orchidaceae
#             GenusRelation = apps.get_model(app.lower(), 'GenusRelation')
#             HybImages = apps.get_model(app.lower(), 'HybImages')
#             Intragen = apps.get_model(app.lower(), 'Intragen')
#         else:
#             HybImages = apps.get_model(app.lower(), 'SpcImages')
#         Genus = apps.get_model(app.lower(), 'Genus')
#         Hybrid = apps.get_model(app.lower(), 'Hybrid')
#         Species = apps.get_model(app.lower(), 'Species')
#         Accepted = apps.get_model(app.lower(), 'Accepted')
#         Ancestordescendant = apps.get_model(app.lower(), 'AncestorDescendant')
#         Synonym = apps.get_model(app.lower(), 'Synonym')
#         Distribution = apps.get_model(app.lower(), 'Distribution')
#         SpcImages = apps.get_model(app.lower(), 'SpcImages')
#         UploadFile = apps.get_model('common', 'UploadFile')
#     return Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen


def xgetSuperGeneric(request):
    family, subfamily, tribe, subtribe = '', '', '', ''

    subtribe = request.GET.get('subtribe', None)
    if subtribe:
        try:
            subtribe = Subtribe.objects.get(pk=subtribe)
        except Subtribe.DoesNotExist:
            subtribe = ''
        if subtribe and subtribe.tribe:
            tribe = subtribe.tribe
        if tribe and tribe.subfamily:
            subfamily = tribe.subfamily
        if subfamily and subfamily.family:
            family = subfamily.family

    tribe = request.GET.get('tribe', None)
    if tribe:
        try:
            tribe = Tribe.objects.get(pk=tribe)
        except Tribe.DoesNotExist:
            tribe = ''
        if tribe and tribe.subfamily:
            subfamily = tribe.subfamily
        if subfamily and subfamily.family:
            family = tribe.subfamily.family

    subfamily = request.GET.get('subfamily', None)
    if subfamily:
        try:
            subfamily = Subfamily.objects.get(pk=subfamily)
        except Subfamily.DoesNotExist:
            subfamily = ''
        if subfamily and subfamily.family:
            family = subfamily.family

    return family, subfamily, tribe, subtribe

# Only for Orchidaceae
def getSuperGeneric(request):
    subtribe = request.GET.get('subtribe', None)
    if subtribe:
        try:
            subtribe = Subtribe.objects.get(pk=subtribe)
        except Subtribe.DoesNotExist:
            subtribe = ''

    tribe = request.GET.get('tribe', None)
    if tribe:
        try:
            tribe = Tribe.objects.get(pk=tribe)
        except Tribe.DoesNotExist:
            tribe = ''

    subfamily = request.GET.get('subfamily', None)
    if subfamily:
        try:
            subfamily = Subfamily.objects.get(pk=subfamily)
        except Subfamily.DoesNotExist:
            subfamily = ''

    return subfamily, tribe, subtribe


# Used in myphotos views only
def getmyphotos(author, app):
    # Get species and hybrid lists that the user has at least one photo
    myspecies_list = Species.objects.exclude(status='synonym').filter(type='species')
    myhybrid_list = Species.objects.exclude(status='synonym').filter(type='hybrid')

    my_upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
    my_spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    if app == 'orchidaceae':
        my_hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    else:
        my_hyb_list = []
    # list for dropdown select
    myspecies_list = myspecies_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_spc_list)).order_by('genus', 'species')
    myhybrid_list = myhybrid_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_hyb_list)).order_by('genus', 'species')

    return myspecies_list, myhybrid_list



def getphotos(author, app, species=None):
    # Get list for display
    if species:
        syn_list = Synonym.objects.filter(acc_id=species.pid).values_list('spid')
        if app == 'orchidaceae' and species.type == 'hybrid':
            if species.status == 'synonym':      # input pid is a synonym, just get images of the requested synonym
                public_list = HybImages.objects.filter(pid=species.pid)  # public photos
            else:                   # input pid is an accepted species, include images of its synonyms
                public_list = HybImages.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # public photos
        else:
            if species.status == 'synonym':
                public_list = SpcImages.objects.filter(pid=species.pid)  # public photos
            else:
                public_list = SpcImages.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # public photos
        upload_list = UploadFile.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # All upload photos
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            upload_list = upload_list.filter(author=author) # Private photos
            private_list = private_list.filter(author=author) # Private photos

    else:
        private_list = public_list = upload_list = []

    return private_list, public_list, upload_list

