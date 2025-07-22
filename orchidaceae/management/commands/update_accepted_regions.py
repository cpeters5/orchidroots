# orchidaceae/management/commands/populate_regions.py

from django.core.management.base import BaseCommand
from orchidaceae.models import Accepted, Distribution, Region  # Replace 'yourapp' with the app containing your models


def get_regions(pid):
    # Fetch region IDs associated with the species
    region_ids = Distribution.objects.filter(pid_id=pid).values_list('region_id', flat=True)

    # Fetch the corresponding Region names efficiently
    region_names = Region.objects.filter(id__in=region_ids).values_list('name', flat=True).order_by('name')

    # Return comma-separated string
    return ', '.join(region_names)


class Command(BaseCommand):
    help = 'Populate the regions field for all Accepted instances with comma-separated Region names. Optionally provide "update" to only process entries where regions is NULL.'

    def add_arguments(self, parser):
        parser.add_argument('mode', nargs='?', default='all', choices=['all', 'update'])


    def handle(self, *args, **options):
        mode = options['mode']
        if mode == 'update':
            accepted_qs = Accepted.objects.filter(regions__isnull=True)
        else:
            accepted_qs = Accepted.objects.all()

        for accepted in accepted_qs:
            pid = accepted.pid_id  # Get the raw primary key value of the related Species
            regions_str = get_regions(pid)
            accepted.regions = regions_str
            accepted.save()

        self.stdout.write(self.style.SUCCESS('Population of Accepted.regions completed.'))