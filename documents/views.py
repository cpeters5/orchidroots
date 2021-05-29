from django.shortcuts import render
from django.apps import apps
from django.contrib.auth.decorators import login_required

User = apps.get_model('accounts', 'User')

# Create your views here.
def list(request):
    context = {}
    return render(request, 'documents/list.html', context)

def help(request):
    context = {}
    return render(request, 'documents/help.html', context)

def releasenote_v4(request):
    context = {}
    return render(request, 'documents/releasenote_v4.html', context)

def bylaws(request):
    context = {}
    return render(request, 'documents/bylaws.html', context)

def articles(request):
    context = {}
    return render(request, 'documents/articles_of_incorporation.html', context)

def req501c3(request):
    context = {}
    return render(request, 'documents/req501c3.html', context)

def disclaimer(request):
    context = {}
    return render(request, 'documents/disclaimer.html', context)

def termsofuse(request):
    context = {}
    return render(request, 'documents/termsofuse.html', context)


@login_required
def future_development(request):
    # if request.user.tier.tier < 5:
    #     return HttpResponseRedirect(reverse('/'))
    context = {}
    return render(request, 'documents/future_development.html', context)


def greetings(request):
    context = {}
    return render(request, 'documents/greetings.html', context)


def faq(request):
    context = {}
    return render(request, 'documents/faq.html', context)

def curator(request):
    curator_list = User.objects.filter(tier=3).order_by('fullname')
    context = {'curator_list':curator_list}
    return render(request, 'documents/curator.html', context)

@login_required
def migration(request):
    # if request.user.tier.tier < 5:
    #     return HttpResponseRedirect(reverse('/'))
    context = {}
    return render(request, 'documents/migration.html', context)

@login_required
def maintenance(request):
    # if request.user.tier.tier < 5:
    #     return HttpResponseRedirect(reverse('/'))
    context = {}
    return render(request, 'documents/maintenance.html', context)


def navigation(request):
    context = {}
    return render(request, 'documents/navigation.html', context)


def identinstruction(request):
    context = {}
    return render(request, 'documents/identinstruction.html', context)

def datamodel(request):
    context = {}
    return render(request, 'documents/datamodel.html', context)


def photosubmissionguideline(request):
    context = {}
    return render(request, 'documents/photosubmissionguideline.html', context)

def photoacquisionguideline(request):
    context = {}
    return render(request, 'documents/photoacquisitionguideline.html', context)


def instructionupload_curate(request):
    context = {}
    return render(request, 'documents/instructionupload_curate.html', context)


def instructionupload_private(request):
    context = {}
    return render(request, 'documents/instructionupload_private.html', context)


def instructionupload(request):
    context = {}
    return render(request, 'documents/instructionupload.html', context)


def development(request):
    context = {}
    return render(request, 'documents/development.html', context)


def changes(request):
    context = {}
    return render(request, 'documents/changes.html', context)


def termofuse(request):
    context = {}
    return render(request, 'documents/termofuse.html', context)


def privacy_policy(request):
    context = {}
    return render(request, 'documents/privacy_policy.html', context)


def contact(request):
    context = {}
    return render(request, 'documents/contact.html', context)


def whoweare(request):
    context = {}
    return render(request, 'documents/whoweare.html', context)

