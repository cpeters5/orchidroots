# sitemap/management/commands/update_sitemap.py
# 1) pip install django-crontab
# 2) settings.py: add django_crontab to INSTALL_APP
# 3) settings.py:  add CRONJOBS = [('0 3 * * *', 'django.core.management.call_command', ['update_sitemaps'])]
# 4) restart server
# 5) python manage.py crontab add (or remove, show)

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.conf import settings
from urllib.parse import urlencode
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
                url=f"{settings.SITE_URL}/display/information/{item.pid}/?family={item.family}",
                section="animalia",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        print("processing aves")
        from aves.models import Species  # Replace with your actual model
        for item in Species.objects.all():
            SitemapEntry.objects.update_or_create(
                url=f"{settings.SITE_URL}/display/information/{item.pid}/?family={item.family}",
                section="aves",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        print("processing fungi")
        from fungi.models import Species  # Replace with your actual model
        for item in Species.objects.all():
            SitemapEntry.objects.update_or_create(
                url=f"{settings.SITE_URL}/display/information/{item.pid}/?family={item.family}",
                section="fungi",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        print("processing other")
        from other.models import Species  # Replace with your actual model
        for item in Species.objects.all():
            SitemapEntry.objects.update_or_create(
                url=f"{settings.SITE_URL}/display/information/{item.pid}/?family={item.family}",
                section="other",
                defaults={
                    'change_frequency': 'monthly',
                    # 'priority': 0.5  # Optional
                }
            )

        print("processing orchidaceae")
        from orchidaceae.models import Species, Genus  # Replace with your actual model
        # List of genera to include in the sitemap
        priority_genera  = ['Cattleya', 'Dendrobium', 'Phalaenopsis', 'Paphiopedilum', 'Cymbidium', 'Rhyncholaeliocattleya',
                             'Oncidium', 'Vanda', 'Rhyncattleanthe', 'Cattlianthe', 'Miltoniopsis', 'Masdevallia', 'Tolumnia', 'Phragmipedium']

        print("Get genus")
        # Add newbrowse pages for genera_with_species
        query_params = urlencode({'family': 'Orchidaceae'})
        genus_url = f"{settings.SITE_URL}/orchidaceae/genera/?{query_params}"
        entry, created = SitemapEntry.objects.update_or_create(
            url=genus_url,
            section="genera",
            defaults={
                'change_frequency': 'monthly',
                'priority': 0.5  # Higher priority for genus pages
            }
        )
        print(f"{'Added' if created else 'Updated'} genera page: {genus_url}")


        print("Get genus with species - Counting species")
        genera_with_species = Genus.objects.annotate(species_count=Count('or5gen')).filter(species_count__gt=0)
        # Add newbrowse pages for genera_with_species
        for genus in genera_with_species:
            query_params = urlencode({'family': 'Orchidaceae', 'genus': genus.genus, 'type': 'species'})
            genus_url = f"{settings.SITE_URL}/orchidaceae/species/?{query_params}"
            entry, created = SitemapEntry.objects.update_or_create(
                url=genus_url,
                section="species",
                defaults={
                    'change_frequency': 'monthly',
                    'priority': 0.7  # Higher priority for genus pages
                }
            )
            if genus in priority_genera:
                print(f"{'Added' if created else 'Updated'} species and hybrid page: {genus_url}")

        print("Get genus with hybrid - Counting hybrids")
        genera_with_hybrids = Genus.objects.annotate(hybrid_count=Count('or7gen')).filter(hybrid_count__gt=0)
        # Add newbrowse pages for genera_with_hybrid
        for genus in genera_with_hybrids:
            query_params = urlencode({'family': 'Orchidaceae', 'genus': genus.genus, 'type': 'hybrid'})
            genus_url = f"{settings.SITE_URL}/orchidaceae/hybrid/?{query_params}"
            entry, created = SitemapEntry.objects.update_or_create(
                url=genus_url,
                section="hybrid",
                defaults={
                    'change_frequency': 'monthly',
                    'priority': 0.7  # Higher priority for genus pages
                }
            )
            # if genus in priority_genera:
                # print(f"{'Added' if created else 'Updated'} species and hybrid page: {genus_url}")

        print("Get info pages for species")
        for genus in priority_genera:
            genus = Genus.objects.filter(genus=genus).annotate(
                species_count=Count('or5gen')
            ).first()

            if genus and genus.species_count > 0:
                for species in Species.objects.filter(gen=genus):
                    species_url = f"{settings.SITE_URL}/display/information/{species.pid}/?family={species.family}"
                    entry, created = SitemapEntry.objects.update_or_create(
                        url=species_url,
                        section="information",
                        defaults={
                            'change_frequency': 'monthly',
                            'priority': 0.5
                        }
                    )
                    # if created:
                    #     print(f"Added species page: {species_url}")
            else:
                print(f"Skipping empty genus: {genus_name}")

        print("Finished processing orchidaceae")

        self.stdout.write(self.style.SUCCESS('Successfully updated sitemap entries'))