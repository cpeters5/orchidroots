# payments/views.py
from django.conf import settings
from django.views.generic.base import TemplateView, View
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
from django.core.mail import send_mail
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse, reverse_lazy
from django.template import RequestContext
from itertools import chain
from utils.json_encoder import LazyEncoder

from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import User
# from orchidaceae.views import mypaginator
from orchidaceae.models import Donation

import stripe # new
import json
import string
import pytz
import django.shortcuts
import random
import os, shutil
from decimal import Decimal
import logging
from django.apps import apps

logger = logging.getLogger(__name__)
User = get_user_model()
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
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                description='Donation Charge',
                source=request.POST['stripeToken']
            )
        except Exception as e:
            messages.error(request, 'An error occurred while charging your card, Please try again!!')
            return redirect(reverse_lazy('donation:donate', kwargs={'donateamt': donateamt}))
        context = {'amount_display':amount_display}
        return render(request, 'donation/charge.html',context)

    return HttpResponseRedirect('/')


class DonateView(TemplateView):
    template_name = 'donation/donateapp.html'
    donateamt = 1000
    donateamt_display = f'{donateamt / 100:.2f}'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paypal_client_id'] = settings.PAYPAL_CLIENT_ID
        context['key'] = settings.STRIPE_PUBLISHABLE_KEY
        context['donateamt'] = 0
        context['donateamt_display'] = 0
        if kwargs:
            context['donateamt'] = kwargs['donateamt']
            context['donateamt_display'] = f'{ context["donateamt"] / 100:.2f}'
        return context


class PaypalTransactionDoneView(View):

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            payer = data['payer']
            payload = {
                'donor_name': f"{payer['name']['given_name']} {payer['name']['surname']}",
                'donor_display_name': data['added-donor-name'],
                'source': Donation.Sources.PAYPAL,
                'source_id': data['id'],
                'status': Donation.Statuses.ACCEPTED if data['status'].lower() == 'completed' else Donation.Statuses.UNVERIFIED,
                'amount': sum([Decimal(purchase_unit['amount']['value']) for purchase_unit in data['purchase_units']]),
                'country_code': payer['address']['country_code']
            }

            Donation.objects.create(**payload)
            return JsonResponse({'status': 'success'}, encoder=LazyEncoder)
        except Exception as e:
            return JsonResponse({'status':'error', 'msg': str(e)}, encoder=LazyEncoder)


class ThankYouView(TemplateView):
    template_name = 'donation/donate.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        donateamt = kwargs['donateamt']
        if donateamt:
            context['donateamt_display'] = f'{donateamt / 100:.2f}'

        return context


def donate(request,donateamt=None): # new
    # donateamt_display = ''
    if donateamt:
        # donateamt = donateamt * 100
        donateamt_display = f'{donateamt:.2f}'

    if request.method == 'POST':
        try:
            donor_display_name = request.POST.get('donor_display_name', '')
            donor_email = request.POST.get('stripeEmail', '')
            donor_name = ''

            charge = stripe.Charge.create(
                amount=donateamt,
                currency='usd',
                description='Donation',
                source=request.POST['stripeToken']
            )
            if charge.get('customer', None):
                donor_name = charge['customer'].get('name', '')

            payload = {
                'donor_display_name': donor_display_name,
                'donor_name': donor_name,
                'donor_email': donor_email,  # Include the email
                'source': Donation.Sources.STRIPE,
                'source_id': charge['id'],
                'status': Donation.Statuses.ACCEPTED if charge['paid'] else Donation.Statuses.UNVERIFIED,
                'amount': Decimal(f'{charge["amount"] / 100:.2f}'),
                'country_code': charge['billing_details']['address']['country']
            }

            Donation.objects.create(**payload)

            # Send confirmation email
            if donor_email:  # Ensure email exists before sending
                send_mail(
                    subject="Thank you for your donation!",
                    message=(
                        f"Dear {donor_display_name},\n\n"
                        f"Thank you for your generous donation of ${donateamt / 100:.2f}. "
                        f"Your support helps us continue our mission.\n\n"
                        "Best regards,\nThe Team"
                    ),
                    from_email='noreply@bluenanta.com',  # Replace with your sender email
                    recipient_list=[donor_email],
                    fail_silently=False,
                )




            return redirect(reverse_lazy('donation:thankyou', kwargs={'donateamt': int(donateamt)}))

        except Exception as e:
            messages.error(request, 'An error occurred while charging your card, Please try again!!')
            return redirect(reverse_lazy('donation:donate', kwargs={'donateamt': donateamt}))
    return render(request, 'donation/donate.html',{})

