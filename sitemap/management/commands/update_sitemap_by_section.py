from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count
from django.apps import apps
from urllib.parse import urlencode
from sitemap.models import SitemapEntry
from utils import config
applications = config.applications

class Command(BaseCommand):
    help = 'Update a specific section of the sitemap entries in the database'

    def add_arguments(self, parser):
        parser.add_argument('section', type=str,
                            help='The section to update (e.g., "animalia", "aves", "fungi", "other", "taxnomy", "orchidaceae")')

    def handle(self, *args, **options):
        section = options['section']

        if section not in ['animalia', 'aves', 'fungi', 'other', 'taxonomy', 'orchidaceae']:
        # if section not in ['animalia', 'aves', 'fungi', 'other', 'taxonomy', 'species', 'hybrid', 'orchidaceae']:
            self.stdout.write(self.style.ERROR(f'Invalid section: {section}'))
            return

        # Delete existing entries for the specified section
        SitemapEntry.objects.filter(section=section).delete()

        # Update the specified section
        update_method = getattr(self, f'update_{section}', None)
        if update_method:
            update_method()
        else:
            self.stdout.write(self.style.ERROR(f'No update method found for section: {section}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {section} sitemap entries'))

    def update_animalia(self):
        from animalia.models import Species, Genus
        app = 'animalia'
        from animalia.models import Species
        for item in Species.objects.all():
            SitemapEntry.objects.create(
                url=f"{settings.SITE_URL}/display/summary/{app}/{item.pid}/?family={item.family}",
                section=app,
                change_frequency='monthly',
                priority=0.2
            )
        # for genus in Genus.objects.all():
        #     query_params = urlencode({'genus': genus.genus,})
        #     genus_url = f"{settings.SITE_URL}/common/species/{app}/?{query_params}"
        #     SitemapEntry.objects.update_or_create(
        #         url=genus_url,
        #         section= app,
        #         defaults={
        #             'change_frequency': 'monthly',
        #             'priority': 0.7  # Higher priority for genus pages
        #         }
        #     )
            # if genus.genus in priority_genera:


    def update_aves(self):
        from aves.models import Species, Genus
        app = 'aves'
        from aves.models import Species
        for item in Species.objects.all():
            SitemapEntry.objects.create(
                url=f"{settings.SITE_URL}/display/summary/{app}/{item.pid}/?family={item.family}",
                section=app,
                change_frequency='monthly',
                priority=0.2
            )
        # for genus in Genus.objects.all():
        #     query_params = urlencode({'genus': genus.genus,})
        #     genus_url = f"{settings.SITE_URL}/common/species/{app}/?{query_params}"
        #     SitemapEntry.objects.update_or_create(
        #         url=genus_url,
        #         section=app,
        #         defaults={
        #             'change_frequency': 'monthly',
        #             'priority': 0.7  # Higher priority for genus pages
        #         }
        #     )

    def update_fungi(self):
        from fungi.models import Species, Genus
        app = 'fungi'
        from fungi.models import Species
        for item in Species.objects.all():
            SitemapEntry.objects.create(
                url=f"{settings.SITE_URL}/display/summary/{app}/{item.pid}/?family={item.family}",
                section=app,
                change_frequency='monthly',
                priority=0.2
            )
        # for genus in Genus.objects.all():
        #     query_params = urlencode({'genus': genus.genus,})
        #     genus_url = f"{settings.SITE_URL}/common/species/{app}/?{query_params}"
        #     SitemapEntry.objects.update_or_create(
        #         url=genus_url,
        #         section=app,
        #         defaults={
        #             'change_frequency': 'monthly',
        #             'priority': 0.7  # Higher priority for genus pages
        #         }
        #     )

    def update_other(self):
        from other.models import Species, Genus
        app = 'other'
        from other.models import Species
        for item in Species.objects.all():
            SitemapEntry.objects.create(
                url=f"{settings.SITE_URL}/display/summary/{app}/{item.pid}/?family={item.family}",
                section=app,
                change_frequency='monthly',
                priority=0.2
            )
        # for genus in Genus.objects.all():
        #     query_params = urlencode({'genus': genus.genus,})
        #     genus_url = f"{settings.SITE_URL}/common/species/{app}/?{query_params}"
        #     SitemapEntry.objects.update_or_create(
        #         url=genus_url,
        #         section=app,
        #         defaults={
        #             'change_frequency': 'monthly',
        #             'priority': 0.7  # Higher priority for genus pages
        #         }
        #     )

    def update_taxonomy(self):
        # query_params = urlencode({'family': 'Orchidaceae'})
        section = 'taxonomy'
        for app in applications:
            taxa_url = f"{settings.SITE_URL}/common/taxonomy/{app}/"
            SitemapEntry.objects.create(
                url=taxa_url,
                section=section,
                change_frequency='yearly',
                priority=0.2
            )
            family_url = f"{settings.SITE_URL}/common/family/{app}/"
            SitemapEntry.objects.create(
                url=family_url,
                section=section,
                change_frequency='yearly',
                priority=0.2
            )
            genus_url = f"{settings.SITE_URL}/common/genera/{app}/"
            SitemapEntry.objects.create(
                url=genus_url,
                section=section,
                change_frequency='monthly',
                priority=0.6
            )



# Orchid only sections
#     Removed from sitemap.
    def xxupdate_species(self):
        from orchidaceae.models import Species, Genus
        print("Get genus with species - Counting species")
        for genus in Genus.objects.filter(genusstat__num_species__gt=0):
            query_params = urlencode({'genus': genus.genus,})
            genus_url = f"{settings.SITE_URL}/common/species/orchidaceae/?{query_params}"
            entry, created = SitemapEntry.objects.update_or_create(
                url=genus_url,
                section="species",
                defaults={
                    'change_frequency': 'monthly',
                    'priority': 0.7  # Higher priority for genus pages
                }
            )
            # if genus.genus in priority_genera:
            #     print(f"{'Added' if created else 'Updated'} species page: {genus_url}")

    #     Removed from sitemap.
    def xxupdate_hybrid(self):
        from orchidaceae.models import Species, Genus
        print("Get genus with hybrid - Counting hybrids")
        genera_with_hybrids = Genus.objects.filter(genusstat__num_hybrid__gt=0)
        # genera_with_hybrids = Genus.objects.annotate(hybrid_count=Count('or7gen')).filter(hybrid_count__gt=0)
        for genus in genera_with_hybrids:
            query_params = urlencode({'genus': genus.genus,})
            genus_url = f"{settings.SITE_URL}/common/hybrid/orchidaceae/?{query_params}"
            SitemapEntry.objects.update_or_create(
                url=genus_url,
                section="hybrid",
                defaults={
                    'change_frequency': 'monthly',
                    'priority': 0.7  # Higher priority for genus pages
                }
            )

    def update_orchidaceae(self):
        from orchidaceae.models import Species, Genus
        # Only for orchids
        print("Get info pages for species/hybrids")
        priority_genera = ['Cattleya', 'Dendrobium', 'Phalaenopsis', 'Paphiopedilum', 'Cymbidium', 'Rhyncholaeliocattleya',
                           'Oncidium', 'Vanda', 'Rhyncattleanthe', 'Cattlianthe', 'Miltoniopsis', 'Masdevallia', 'Tolumnia', 'Phragmipedium']

        for species in Species.objects.all():
            if species.status == 'synonym':
                priority = 0.3
            elif species.genus in priority_genera:
                priority = 0.5
            else:
                priority = 0.4
            species_url = f"{settings.SITE_URL}/display/summary/orchidaceae/{species.pid}/"
            SitemapEntry.objects.update_or_create(
                url=species_url,
                section="orchidaceae",
                defaults={
                    'change_frequency': 'monthly',
                    'priority': priority
                }
            )