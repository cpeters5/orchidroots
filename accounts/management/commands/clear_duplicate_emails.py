from django.core.management.base import BaseCommand
from django.db.models import Count
from accounts.models import User
from allauth.account.models import EmailAddress



class Command(BaseCommand):
    help = "Clears all duplicate emails "


    def handle(self, *args, **options):
        users = User.objects.values('email').annotate(Count('id')).order_by().filter(id__count__gt=1)
        users = User.objects.filter(email__in=[user['email'] for user in users if user['email'] != ''])
        for user in users:
            user.email = ''
            emails = EmailAddress.objects.filter(user=user)
            emails.delete()
            user.save()