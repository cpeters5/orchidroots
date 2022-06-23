from django.shortcuts import render
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_GET
# from django.core.urlresolvers import resolve
from django.db.models import Q
from django.http import HttpResponse
from django.urls import resolve, get_resolver, URLResolver, URLPattern
from django.apps import apps

from core.models import Family
from core.models import Subfamily
from core.models import Tribe
from core.models import Subtribe
from orchidaceae.models import Species, UploadFile, SpcImages, HybImages
from accounts.models import Photographer

logger = logging.getLogger(__name__)


def change_family(request):
    path = request.path
    path_list = {
            '': '',
            'browse': 'browse',
            '/common/genera/': '/common/genera/',
            'species': 'species',
            'hybrid': 'hybrid',
            '/common/search_species/': '/common/search_species/',
            'curate_newupload': 'curate_newupload',
            'myphoto': 'myphoto_browspc',
            'myphoto_browspc': 'myphoto_browspc',
            'myphoto_browsehyb': 'myphoto_browsehyb'
    }
    return path_list[path]


def get_family_list(request):
    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']
    if alpha != '':
        family_list = Family.objects.filter(family__istartswith=alpha)
    else:
        family_list = Family.objects.all()
    favorite = Family.objects.filter(family__in=('Orchidaceae', 'Bromeliaceae', 'Cactaceae'))
    family_list = favorite.union(family_list)
    return family_list, alpha

def getApp(request):
    return request.resolver_match.app_name

def write_output(request, detail=None):
    if str(request.user) != 'chariya' and request.user.is_authenticated:
        message = "ACCESS: " + request.path + " - " + str(request.user)
        if detail:
            message += " - " + detail
        logger.error(message)
    return


def get_author(request):
    if not request.user.is_authenticated or request.user.tier.tier < 2:
        return None, None

    author_list = Photographer.objects.exclude(user_id__isnull=True).order_by('displayname')
    author = request.user.photographer.author_id
    if request.user.tier.tier > 2 and 'author' in request.GET:
        author = request.GET['author']
        if author:
            author = Photographer.objects.get(pk=author)
    # if not author and request.user.tier.tier > 1:
    #     try:
    #         author = Photographer.objects.get(user_id=request.user)
    #     except Photographer.DoesNotExist:
    #         author = Photographer.objects.get(author_id='anonymous')
    return author, author_list

def get_reqauthor(request):
    author = None
    if request.user.is_authenticated:
        if request.user.tier.tier > 2:
            if 'author' in request.GET:
                author = request.GET['author']
            if author == "---" or author == '':
                author = None
            if author is not None:
                author = Photographer.objects.get(pk=author)
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
        if 'page' in request.GET:
            page = request.GET.get('page', '1')
        if not page or page == 0:
            page = 1
        else:
            page = int(page)

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
    role = ''
    if 'role' in request.GET:
        role = request.GET['role']
    elif 'role' in request.POST:
        role = request.POST['role']
    if request.user.is_authenticated:
        if not role:
            if request.user.tier.tier < 2:
                role = 'pub'
            elif request.user.tier.tier == 2:
                # Tier 2 users (private) role default to private
                role = 'pri'
            else:
                role = 'cur'
                if 'role' in request.GET:
                    role = request.GET['role']
                # Decommission public role (set as default)
                if role == 'pub':
                    role = 'pri'
        return role
    return 'pub'

def getModels(request, family=None):
    subfamily, tribe, subtribe = '', '', ''
    if not family:
        if 'family' in request.GET:
            family = request.GET['family']
        elif 'family' in request.POST:
            family = request.POST['family']
        if 'newfamily' in request.GET:
            newfamily = request.GET['newfamily']
            if newfamily == 'other':
                family = ''
                app = 'other'
            else:
                family = newfamily
    if family != 'other':
        try:
            family = Family.objects.get(pk=family)
            app = family.application
        except Family.DoesNotExist:
            family = ''
            app = 'other'
    else:
        family = ''
        app = 'other'

    if 'subfamily' in request.GET:
        subfamily = request.GET['subfamily']
        if subfamily:
            try:
                subfamily = Subfamily.objects.get(pk=subfamily)
            except Subfamily.DoesNotExist:
                subfamily = ''
            if subfamily.family:
                family = subfamily.family
    if 'tribe' in request.GET:
        tribe = request.GET['tribe']
        if tribe:
            try:
                tribe = Tribe.objects.get(pk=tribe)
            except Tribe.DoesNotExist:
                tribe = ''
            if tribe.subfamily:
                subfamily = tribe.subfamily
            if subfamily.family:
                family = tribe.subfamily.family
    if 'subtribe' in request.GET:
        subtribe = request.GET['subtribe']
        if subtribe:
            try:
                subtribe = Subtribe.objects.get(pk=subtribe)
            except Subtribe.DoesNotExist:
                subtribe = ''
            if subtribe.tribe:
                tribe = subtribe.tribe
            if tribe.subfamily:
                subfamily = tribe.subfamily
            if subfamily.family:
                family = subfamily.family
    Genus = ''
    Species = ''
    Accepted = ''
    Hybrid = ''
    Synonym = ''
    Distribution = ''
    SpcImages = ''
    HybImages = ''
    UploadFile = ''
    Intragen = ''
    if app:
        if app == 'orchidaceae':
            from detail.forms import UploadFileForm, UploadSpcWebForm, UploadHybWebForm, AcceptedInfoForm, HybridInfoForm, SpeciesForm, RenameSpeciesForm
            # only exist for orchidaceae
            GenusRelation = apps.get_model(app.lower(), 'GenusRelation')
            HybImages = apps.get_model(app.lower(), 'HybImages')
            Intragen = apps.get_model(app.lower(), 'Intragen')
        else:
            HybImages = apps.get_model(app.lower(), 'SpcImages')
        Genus = apps.get_model(app.lower(), 'Genus')
        Hybrid = apps.get_model(app.lower(), 'Hybrid')
        Species = apps.get_model(app.lower(), 'Species')
        Accepted = apps.get_model(app.lower(), 'Accepted')
        Ancestordescendant = apps.get_model(app.lower(), 'AncestorDescendant')
        Synonym = apps.get_model(app.lower(), 'Synonym')
        Distribution = apps.get_model(app.lower(), 'Distribution')
        SpcImages = apps.get_model(app.lower(), 'SpcImages')
        UploadFile = apps.get_model('common', 'UploadFile')
    return Genus, Species, Accepted, Hybrid, Synonym, Distribution, SpcImages, HybImages, app, family, subfamily, tribe, subtribe, UploadFile, Intragen


def getmyphotos(request, author, app, species, Species, Synonym, UploadFile, SpcImages, HybImages, role):
    # Get species and hybrid lists that the user has at least one photo
    if request.user.username == 'chariya' and author:
        print("2 author = " + str(author))
    myspecies_list = Species.objects.filter(type='species')
    myhybrid_list = Species.objects.filter(type='hybrid')
    my_spc_list = []
    my_hyb_list = []
    my_upl_list = []
    if request.user.username == 'chariya':
        print("2.1 myspecies_list = " + str(len(myspecies_list)))
    if author and author.author_id != '' and author is not None:
        my_upl_list = list(UploadFile.objects.filter(author=author).values_list('pid', flat=True).distinct())
        my_spc_list = list(SpcImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
        if app == 'orchidaceae':
            my_hyb_list = list(HybImages.objects.filter(author=author).values_list('pid', flat=True).distinct())
    # list for dropdown select
        myspecies_list = myspecies_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_spc_list)).order_by('genus', 'species')
        myhybrid_list = myhybrid_list.filter(Q(pid__in=my_upl_list) | Q(pid__in=my_hyb_list)).order_by('genus', 'species')
    if request.user.username == 'chariya':
        print("2.2 myspecies_list = " + str(len(myspecies_list)))

    # Get list for display
    if species:
        req_pid = species.pid
        pid = species.pid
        syn_list = ()
        syn_list = Synonym.objects.filter(acc_id=req_pid).values_list('spid')
        if app == 'orchidaceae' and species.type == 'hybrid':
            if req_pid != pid:      # input pid is a synonym, just get images of the requested synonym
                public_list = HybImages.objects.filter(pid=req_pid)  # public photos
            else:                   # input pid is an accepted species, include images of its synonyms
                public_list = HybImages.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # public photos
        else:
            if req_pid != pid:
                public_list = SpcImages.objects.filter(pid=req_pid)  # public photos
            else:
                public_list = SpcImages.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # public photos
        upload_list = UploadFile.objects.filter(Q(pid=species.pid) | Q(pid__in=syn_list))  # All upload photos
        private_list = public_list.filter(rank=0)  # rejected photos
        if role == 'pri':
            upload_list = upload_list.filter(author=author) # Private photos
            private_list = private_list.filter(author=author) # Private photos

        if not author or author == 'anonymous' :  # Display only rank > 0
            public_list  = public_list.filter(rank__gt=0)
    else:
        private_list = public_list = upload_list = []

    return private_list, public_list, upload_list, myspecies_list, myhybrid_list

# def get_view_name_by_path(path):
#     result = resolve(path=path)
#     return result.view_name
#
#
# def find_url_pattern_by_name(name):
#     if name is None:
#         return None
#
#     def deep_find(rs):
#         for r in rs.url_patterns:
#             if isinstance(r, URLResolver):
#                 result = deep_find(r)
#                 if result is not None:
#                     return result
#             elif isinstance(r, URLPattern):
#                 if r.name == name:
#                     return r.pattern
#
#     return deep_find(get_resolver())
#

@require_GET
def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /accounts/",
        "Disallow: /core/",
        "Disallow: /detail/",
        "Disallow: /documents/",
        "Disallow: /donations/",
        "Disallow: /natural/",
        "Disallow: /orchid/",
        "Disallow: /orchidaceae/",
        "Disallow: /orchidlist/",
        "Disallow: /orchidlight/",
        "Disallow: /orchiddb/",
        "Disallow: /other/",
        "Disallow: /search/",
        "Disallow: /utils/",
        "User-Agent: PetalBot",
        "Disallow: /",

    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

