# payments/views.py
from django.conf import settings
from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from django import template
from PIL import Image, ExifTags
from io import BytesIO
from django.db.models import Q
from django.core.files import File
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse, reverse_lazy
from django.template import RequestContext
from itertools import chain

from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import User
from detail.views import getmyphotos, get_random_img
from orchidlist.views import mypaginator

import stripe # new
import json
import string
import pytz
import django.shortcuts
import random
import os, shutil

from django.apps import apps
User = get_user_model()

from django.apps import apps

stripe.api_key = settings.STRIPE_SECRET_KEY # new
amount = 2000
amount_display = f'{amount/100:.2f}'
# donateamt = 0
# donateamt_display = f'{donateamt/100:.2f}'


#--- donation

class PaymentView(TemplateView):
    template_name = 'donation/donationapp.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['key'] = settings.STRIPE_PUBLISHABLE_KEY
        context['amount'] = amount
        context['amount_display'] = amount_display
        return context


def charge(request): # new
    if request.method == 'POST':
        charge = stripe.Charge.create(
            amount=amount,
            currency='usd',
            description='A Django charge',
            source=request.POST['stripeToken']
        )
        context = {'amount_display':amount_display,'namespace':'donation',}
        return render(request, 'donation/charge.html',context)

    return HttpResponseRedirect('/')


class DonateView(TemplateView):
    template_name = 'donation/donateapp.html'
    donateamt = 1000
    donateamt_display = f'{donateamt / 100:.2f}'

    # def get(self, request, *args, **kwargs):
    #     context['donateamt'] = kwargs['donateamt']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['key'] = settings.STRIPE_PUBLISHABLE_KEY
        context['donateamt'] = 0
        context['donateamt_display'] = 0
        if kwargs:
            context['donateamt'] = kwargs['donateamt']
            context['donateamt_display'] = f'{ context["donateamt"] / 100:.2f}'
        return context

def donate(request,donateamt=None): # new
    donateamt_display = ''
    if donateamt:
        donateamt_display = f'{donateamt / 100:.2f}'
    # if request.GET.get('donateamt'):
    #     donateamt_display = request.GET['donateamt']
        # donateamt_display = f'{request.GET["donateamt"] / 100:.2f}'

    if request.method == 'POST':
        charge = stripe.Charge.create(
            amount=donateamt,
            currency='usd',
            description='Donation',
            source=request.POST['stripeToken']
        )
        context = {'donateamt_display':donateamt_display,'namespace':'donation',}
        return render(request, 'donation/donate.html',context)
    return render(request, 'donation/donate.html',{})

