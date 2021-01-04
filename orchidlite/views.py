# -*- coding: utf8 -*-
import string
from django.http import HttpResponse, HttpResponseRedirect

def orchidlite_home(request):
    return HttpResponseRedirect('/orchid_home/')
    # context = {'title': 'orchidlight_home'}
    # return django.shortcuts.render(request, 'orchidlite/orchidlite_home.html', context)


def all_species(request):
    return HttpResponseRedirect('/orchidlist/species')


def search(request):
    role = 'pub'
    search = ''
    if 'q' in request.GET:
        q = request.GET['q']

    send_url = '/search/search_match/?search=' + q
    return HttpResponseRedirect(send_url)


def genera(request):
    genustype = ''
    if 'genustype' in request.GET:
        genustype = request.GET['genustype']
    send_url = '/orchidlist/genera/?genustype=' + genustype
    return HttpResponseRedirect(send_url)


def species(request, pid):
    send_url = '/detail/information/?pid=' + str(pid)
    return HttpResponseRedirect(send_url)


def hybrids(request, pid):
    send_url = '/detail/information/?pid=' + str(pid)
    return HttpResponseRedirect(send_url)
