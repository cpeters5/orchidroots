from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from utils.views import write_output, is_int, getRole
from django.apps import apps
Genus = apps.get_model('orchidaceae', 'Genus')

# Create your views here.
def information(request, pid=None):
    role = getRole(request)
    family = 'Orchidaceae'
    if pid:
        send_url = '/common/information/' + str(pid) + '/?family=' + str(family) + '&role=' + role
    else:
        send_url = '/'
    return HttpResponseRedirect(send_url)

def browse(request):
    role = getRole(request)
    if 'genus' in request.GET:
        genus = request.GET.get('genus')
    else:
        genus = ''
    family = 'Orchidaceae'
    send_url = '/common/browse/?genus=' + str(genus) + '&family=' + str(family) + '&role=' + role + '&display=checked'
    return HttpResponseRedirect(send_url)
