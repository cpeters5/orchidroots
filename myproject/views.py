from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.apps import apps
import random
import string

Genus = apps.get_model('orchiddb', 'Genus')
Species = apps.get_model('orchiddb', 'Species')
SpcImages = apps.get_model('orchiddb', 'SpcImages')
HybImages = apps.get_model('orchiddb', 'HybImages')
Comment = apps.get_model('orchiddb', 'Comment')
num_img = 20


def orchid_home(request):
    randgenus = Genus.objects.exclude(status='synonym').extra(where=["num_spc_with_image + num_hyb_with_image > 0"]
                                                              ).values_list('pid', flat=True).order_by('?')
    # Number of visits to this view, as counted in the session variable.
    # num_visits = request.session.get('num_visits', 0)
    # request.session['num_visits'] = num_visits + 1
    randimages = []
    for e in randgenus:
        if len(randimages) >= num_img:
            break
        if SpcImages.objects.filter(gen=e):
            img = SpcImages.objects.filter(gen=e).filter(rank__gt=0).filter(rank__lt=7).order_by('-rank', 'quality', '?'
                                                                                                 )[0:1]
            if img and len(img):
                randimages.append(img[0])

    random.shuffle(randimages)
    role = 'pub'
    if 'role' in request.GET:
        role = request.GET['role']
    context = {'title': 'orchid_home', 'role': role, 'randimages': randimages, 'level': 'detail', 'tab': 'sum', }
    return render(request, 'orchid_home.html', context)


def require_get(view_func):
    def wrap(request, *args, **kwargs):
        if request.method != "GET":
            return HttpResponseBadRequest("Expecting GET request")
        return view_func(request, *args, **kwargs)
    wrap.__doc__ = view_func.__doc__
    wrap.__dict__ = view_func.__dict__
    wrap.__name__ = view_func.__name__
    return wrap


@require_get
def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /private/",
        "Disallow: /junk/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
