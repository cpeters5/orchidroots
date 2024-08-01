# sitemap/management/commands/update_sitemap.py
# 1) pip install django-crontab
# 2) settings.py: add django_crontab to INSTALL_APP
# 3) settings.py:  add CRONJOBS = [('0 3 * * *', 'django.core.management.call_command', ['update_sitemaps'])]
# 4) restart server
# 5) python manage.py crontab add (or remove, show)

from django.core.management.base import BaseCommand
from sitemap.models import SitemapEntry

class Command(BaseCommand):
    help = 'Update the sitemap entries in the database'

    def handle(self, *args, **options):
        # Clear existing entries (optional)
        SitemapEntry.objects.all().delete()

        # Add or update entries
        print("processing animalia")
        from animalia.models import Species  # Replace with your actual model
        for item in Species.objects.all():
            SitemapEntry.objects.update_or_create(
                url=f"https://www.orchidroots.com/display/photos/{item.pid}/?family={item.family}",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        print("processing aves")
        from aves.models import Species  # Replace with your actual model
        for item in Species.objects.all():
            SitemapEntry.objects.update_or_create(
                url=f"https://www.orchidroots.com/display/photos/{item.pid}/?family={item.family}",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        print("processing fungi")
        from fungi.models import Species  # Replace with your actual model
        for item in Species.objects.all():
            SitemapEntry.objects.update_or_create(
                url=f"https://www.orchidroots.com/display/photos/{item.pid}/?family={item.family}",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        print("processing other")
        from other.models import Species  # Replace with your actual model
        for item in Species.objects.all():
            SitemapEntry.objects.update_or_create(
                url=f"https://www.orchidroots.com/display/photos/{item.pid}/?family={item.family}",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        print("processing orchidaceae")
        from orchidaceae.models import Species  # Replace with your actual model
        for item in Species.objects.all():
            SitemapEntry.objects.update_or_create(
                url=f"https://www.orchidroots.com/display/information/{item.pid}/",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully updated sitemap entries'))