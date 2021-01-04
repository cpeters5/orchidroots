# -*- coding: utf8 -*-
from django.http import HttpResponseRedirect

def orchid_home(request):
    return HttpResponseRedirect('/')

def genera(request):
    genustype = ''
    if 'genustype' in request.GET:
        genustype = request.GET['genustype']
    send_url = '/orchidlist/genera/?genustype=' + genustype
    return HttpResponseRedirect(send_url)

def all_species(request):
    type = ''
    if 'type' in request.GET:
        type = request.GET['type']
    genus = ''
    if 'genus' in request.GET:
        genus = request.GET['genus']
    if type == 'species':
        send_url = '/orchidlist/species/?genus=' + genus
    else:
        send_url = '/orchidlist/hybrid/?genus=' + genus
    return HttpResponseRedirect(send_url)

def family_tree (request,pid):
    gen = ''
    if 'gen' in request.GET:
        gen = request.GET['gen']

    send_url = '/detail/ancestrytree/?pid=' + str(pid) + '&role=pub'
    return HttpResponseRedirect(send_url)


def browse (request):
    return HttpResponseRedirect('/')


def search_match(request):
    role = 'pub'
    search = ''
    if 'q' in request.GET:
        q = request.GET['q']

    send_url = '/search/search_match/?search=' + q
    return HttpResponseRedirect(send_url)


# Detail
def species(request, pid):
    send_url = '/detail/information/?pid=' + str(pid) + '&role=pub'
    return HttpResponseRedirect(send_url)


def hybrids(request, pid):
    send_url = '/detail/information/?pid=' + str(pid) + '&role=pub'
    return HttpResponseRedirect(send_url)


def progeny(request):
    pid = ''
    if 'pid' in request.GET:
        pid = request.GET['pid']
    send_url = '/orchidlist/progeny/' + str(pid) + '/?role=pub'
    return HttpResponseRedirect(send_url)

def ancestor(request):
    pid = ''
    if 'pid' in request.GET:
        pid = request.GET['pid']
    if pid:
        send_url = '/detail/ancestor/?pid=' + str(pid) + '&role=pub'
    else:
        send_url = '/detail/ancestor/?tab=anc&role=pub'
    return HttpResponseRedirect(send_url)



