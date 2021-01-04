from django.core.management.base import BaseCommand
from accounts.models import User
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = "Clears email address from a certain user"

    def add_arguments(self, parser):
        parser.add_argument('--username', help='User Username' )
        parser.add_argument('--email', help='User Email')

    def handle(self, *args, **options):
        if options['username']:
            users = User.objects.filter(username=options['username'])
        elif options['email']:
            users = User.objects.filter(email=options['email'])
        else:
            raise Exception('Include --username or --email')

        for user in users:
            user.email = ''
            emails = EmailAddress.objects.filter(user=user)
            emails.delete()
            user.save()


