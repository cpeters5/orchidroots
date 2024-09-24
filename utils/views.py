from django.shortcuts import render
import logging
import os
import shutil
import shortuuid
import re
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_GET
# from django.core.urlresolvers import resolve
from django.db.models import Func, Q, Value, CharField
from django.urls import resolve, get_resolver, URLResolver, URLPattern
from django.apps import apps
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.shortcuts import redirect
from urllib.parse import urlparse, urlencode, parse_qs

from common.models import Family, Subfamily, Tribe, Subtribe
from orchidaceae.models import Species, UploadFile, SpcImages, HybImages
from accounts.models import Photographer, User

logger = logging.getLogger(__name__)
import utils.config
applications = utils.config.applications

# Use in django query to match ignore spece character
class RemoveSpaces(Func):
    function = 'REPLACE'
    template = "%(function)s(%(expressions)s, ' ', '')"




def redirect_to_referrer(request, default_url='/', excluded_params=None):
    """
    Redirects to the referring page with all original GET parameters.

    Args:
    request: The HttpRequest object.
    default_url: The name of the URL to redirect to if no referrer is found.
    excluded_params: A list of GET parameters to exclude from the redirect.

    Returns:
    HttpResponseRedirect to the referrer or default URL.
    """
    referer = request.META.get('HTTP_REFERER')

    if referer:
        parsed_uri = urlparse(referer)
        path = parsed_uri.path

        # Get the original GET parameters, excluding any specified
        params = request.GET.copy()
        if excluded_params:
            for param in excluded_params:
                params.pop(param, None)

        query_string = urlencode(params)

        # Combine the path and parameters
        redirect_url = f"{path}?{query_string}" if query_string else path

        return HttpResponseRedirect(redirect_url)
    else:
        # If there's no referer, redirect to the default URL
        return redirect(default_url)


def clean_search_string(search_string):
    # search_string = search_string.replace('.', '')
    search_string = search_string.replace(' mem ', ' Memoria ')
    search_string = search_string.replace(' Mem ', ' Memoria ')
    search_string = search_string.replace(' mem. ', ' Memoria ')
    search_string = search_string.replace(' Mem. ', ' Memoria ')
    search_string = re.sub(r'\s+', ' ', search_string)
    search_string =  search_string.replace("’", "'")
    return search_string

def expand_genus_name(search_string):
    # Check if the first word is a full genus name, or an abreviation, then epand it
    # Return full genus name and updated search_string
    first_word = search_string.split()[0]
    print("first_word", first_word)
    # Check if the first word is a genus
    Genus = apps.get_model('orchidaceae', 'Genus')
    try:
        genus = Genus.objects.get(genus=first_word)
        print("genus", genus)
        # Return the first word as genus, search_string unchanged
        genus = genus.genus
    except Genus.DoesNotExist:
        if not first_word.endswith('.'):
            first_word = first_word + '.'
        genus = Genus.objects.filter(abrev=first_word)
        # Found an abreviation, expanded it
        # Return expanded genus and updated search-string
        if genus and len(genus) > 0:
            genus = genus[0].genus
            words = search_string.split()
            words[0] = genus
            search_string = ' '.join(words)
        else:
            genus = ''
        # No genus in the string. Return '' for genus and unchanged search_string (as species name)

    return genus, search_string




def clean_query(search_string):
    rest = ''
    if ' ' not in search_string:
        genus_string = search_string
    else:
        (genus_string, rest) = search_string.split(' ', 1)

    if genus_string:
        genus_list = Binomial.objects.filter(abrev=genus_string)

    # test if genus_string is an abreviation

    clean_species = clean_name(rest)
    return genus_string + clean_species


def clean_name(search_string):

    cleaned_name = search_string.replace(" ", "").replace("-", "").replace(",", "").replace("'", "").replace("\"", "").replace(
        ".", "")
    return cleaned_name


# Add IP to log when encountered malicious requests
def handle_bad_request(request):
    pid = request.GET.get('pid', '')
    full_url = request.build_absolute_uri()
    if not pid or not pid.isnumeric():
        logger.info(f">>> Received URL: {full_url}")
        # Try to get the real IP from the X-Real-IP header
        client_ip = request.META.get('HTTP_X_REAL_IP')
        # If not available, fall back to X-Forwarded-For
        if not client_ip:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(',')[0]  # Get the first IP in the list

        # If still not found, fall back to REMOTE_ADDR
        if not client_ip:
            client_ip = request.META.get('REMOTE_ADDR', '')

        return HttpResponse("URL and IP address has been logged.")


# Generate unique file name. Used in ApproveMediaPhoto method
def regenerate_file(source_path, destination_folder):
    # Truncate file name if too long
    new_source_path = truncate_filename(source_path, 30)

    filename = os.path.basename(new_source_path)
    while True:
        # Generate a new unique filename using shortuuid
        unique_filename = shortuuid.uuid() + "_" + filename
        destination_path = os.path.join(destination_folder, unique_filename)

        # Check if the destination file already exists
        if not os.path.exists(destination_path):
            # If it doesn't exist, copy the file
            shutil.copy(source_path, destination_path)
            break
        else:
            continue
    return unique_filename


def truncate_filename(filepath, max_length=40):
    # Split the path into directory and filename
    parts = filepath.rsplit('/', 1)
    if len(parts) == 2:
        directory, filename = parts
    else:
        directory, filename = '', parts[0]

    # Split the filename into name and extension
    name, ext = filename.rsplit('.', 1)

    # Calculate the maximum length for the name
    max_name_length = max_length - len(ext) - 1  # -1 for the dot

    # Truncate the name if necessary
    if len(name) > max_name_length:
        name = name[:max_name_length]

    # Reconstruct the filename
    new_filename = f"{name}.{ext}"

    # Reconstruct the full path
    if directory:
        return f"{directory}/{new_filename}"
    else:
        return new_filename


# Not used
def pathinfo(request):
    path  = request.path.split('/')[2:][0]
    return path

# Get family and app from request
# If not exist, force return Orchidaceae
def get_application(request):
    full_path = request.get_full_path()
    parsed_url = urlparse(full_path)
    query_params = parse_qs(parsed_url.query)
    family = query_params.get('family', [None])[0]
    app = query_params.get('app', [None])[0]

    # family = request.GET.get('family', None)
    if family:
        try:
            family = Family.objects.get(family=family)
        except Family.DoesNotExist:
            family = Family.objects.get(family='Orchidaceae')
        app = family.application
    else:
        app = request.GET.get('app', None)
        if app == 'orchidaceae':
            family = Family.objects.get(family='Orchidaceae')
        elif app not in applications or app == '':
            # If neither family nor app give, assume orchid is requested
            family = Family.objects.get(family='Orchidaceae')
            app = family.application
        else:  #for other apps, return family = None. family will be identified from the pid
            family = None
    return app, family

def get_family(family):
    try:
        family = Family.objects.get(family=family)
    except Family.DoesNotExist:
        family = Family.objects.get(family='Orchidaceae')
    if isinstance(family, Family):
        app = family.application
    else:
        family = ''
        app = ''
    return app, family


# Logging message for tracing users requests
def write_output(request, detail=None):
    if request.user.is_authenticated:
        message = "ACCESS: " + request.path + " - " + str(request.user)
        if detail:
            message += " - " + detail
        logger.warn(message)
    return

# Used in my photos views. Probably can do without
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

# Used in detail.uploadFile (orchidaceae) and common.upload_file (all other)
def get_reqauthor(request):
    # Return photogrtapher object
    author = None
    if request.user.is_authenticated:
        author = request.GET.get('author', request.user.photographer)

        if not isinstance(author, Photographer):
            try:
                author = Photographer.objects.get(pk=author)
            except Photographer.DoesNotExist:
                author = Photographer.objects.get(author_id='anonymous')
        if not author:
            author = request.user.photographer
    if isinstance(author, User):
        author = Photographer.objects.filter(user_id=author[0].id)
        if len(author) > 0:
            author = author[0]
    return author


def thumbdir():
    imgdir = 'utils/thumbs/'
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


def getRole(request):
    role = request.GET.get('role', '')
    if not role and 'role' in request.POST:
        role = request.POST['role']
        if not role:
            role = ''
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


#  Enhance SQL queries
class Replace(Func):
    function = 'REPLACE'
    template = "%(function)s(%(expressions)s, %(pattern)s, %(replacement)s)"

    def __init__(self, expression, pattern, replacement='', **extra):
        super().__init__(
            expression,
            pattern=Value(pattern),
            replacement=Value(replacement),
            **extra
        )


# Applying multiple REPLACE
class MultiReplace(Func):
    def __init__(self, expression, **extra):
        replacements = [
            (' ', ''),  # Remove spaces
            ("'", '')  # Remove single quotes
        ]
        for old, new in replacements:
            expression = Replace(expression, old, new)
        super().__init__(expression, **extra)

