from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count
from urllib.parse import urlencode
from sitemap.models import SitemapEntry
from orchidaceae.models import Species, Genus

class Command(BaseCommand):
    help = 'Update a specific section of the sitemap entries in the database'

    def add_arguments(self, parser):
        parser.add_argument('section', type=str,
                            help='The section to update (e.g., "animalia", "aves", "fungi", "other", "genera", "species", "hybrid", "information")')

    def handle(self, *args, **options):
        section = options['section']

        if section not in ['animalia', 'aves', 'fungi', 'other', 'genera', 'species', 'hybrid', 'information']:
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
        from animalia.models import Species
        for item in Species.objects.all():
            SitemapEntry.objects.create(
                url=f"{settings.SITE_URL}/display/information/{item.pid}/?family={item.family}",
                section="animalia",
                change_frequency='monthly',
                priority=0.2
            )

    def update_aves(self):
        from aves.models import Species
        for item in Species.objects.all():
            SitemapEntry.objects.create(
                url=f"{settings.SITE_URL}/display/information/{item.pid}/?family={item.family}",
                section="aves",
                change_frequency='monthly',
                priority=0.2
            )

    def update_fungi(self):
        from fungi.models import Species
        for item in Species.objects.all():
            SitemapEntry.objects.create(
                url=f"{settings.SITE_URL}/display/information/{item.pid}/?family={item.family}",
                section="fungi",
                change_frequency='monthly',
                priority=0.2
            )

    def update_other(self):
        from other.models import Species
        for item in Species.objects.all():
            SitemapEntry.objects.create(
                url=f"{settings.SITE_URL}/display/information/{item.pid}/?family={item.family}",
                section="other",
                change_frequency='monthly',
                priority=0.2
            )

    def update_genera(self):
        query_params = urlencode({'family': 'Orchidaceae'})
        genus_url = f"{settings.SITE_URL}/orchidaceae/genera/?{query_params}"
        SitemapEntry.objects.create(
            url=genus_url,
            section="genera",
            change_frequency='monthly',
            priority=0.6
        )

    def update_species(self):
        print("Get genus with species - Counting species")
        genera_with_species = Genus.objects.annotate(species_count=Count('or5gen')).filter(species_count__gt=0)
        priority_genera = ['Cattleya', 'Dendrobium', 'Phalaenopsis', 'Paphiopedilum', 'Cymbidium', 'Rhyncholaeliocattleya',
                           'Oncidium', 'Vanda', 'Rhyncattleanthe', 'Cattlianthe', 'Miltoniopsis', 'Masdevallia', 'Tolumnia', 'Phragmipedium']
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
            # if genus.genus in priority_genera:
            #     print(f"{'Added' if created else 'Updated'} species page: {genus_url}")

    def update_hybrid(self):
        print("Get genus with hybrid - Counting hybrids")
        genera_with_hybrids = Genus.objects.annotate(hybrid_count=Count('or7gen')).filter(hybrid_count__gt=0)
        for genus in genera_with_hybrids:
            query_params = urlencode({'family': 'Orchidaceae', 'genus': genus.genus, 'type': 'hybrid'})
            genus_url = f"{settings.SITE_URL}/orchidaceae/hybrid/?{query_params}"
            SitemapEntry.objects.update_or_create(
                url=genus_url,
                section="hybrid",
                defaults={
                    'change_frequency': 'monthly',
                    'priority': 0.7  # Higher priority for genus pages
                }
            )

    def update_information(self):
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
            species_url = f"{settings.SITE_URL}/display/information/{species.pid}/?family={species.family}"
            SitemapEntry.objects.update_or_create(
                url=species_url,
                section="information",
                defaults={
                    'change_frequency': 'monthly',
                    'priority': priority
                }
            )