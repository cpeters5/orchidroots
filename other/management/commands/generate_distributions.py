from django.core.management.base import BaseCommand
from django.apps import apps
Species = apps.get_model('other', 'Species')
Accepted = apps.get_model('other', 'Accepted')
Location = apps.get_model('other', 'Location')
Distribution = apps.get_model('other', 'Distribution')


class Command(BaseCommand):
    help = "Read description from other/Description and print out unique values / load to database. "


    def handle(self, *args, **options):
        pids = Species.objects.filter(source='POWO').values_list('pid', flat=True)
        distributions = Accepted.objects.exclude(distribution__isnull=True).filter(pid__in=pids)
        locations = Location.objects.all().values_list('dist', flat=True)
        i = 0
        locations = list(locations)
        for rec in distributions:
            dists = rec.distribution.split(', ')
            for item in dists:
                item= item.lower()
                item = item.replace('á', 'a')
                item = item.strip()
                if item not in locations:
                    loc = Location(dist=item, name=item)
                    loc.save()
                    i += 1
                    print(i, rec.pid_id, ">"+item+"<")
                    locations.append(item)
                loc = Location.objects.get(dist=item)
                xisting = Distribution.objects.filter(dist=loc, pid=rec.pid)
                if len(xisting) == 0:
                    dist = Distribution(pid=rec.pid, dist=loc)
                    dist.save()

        # for item in locations:
        #     print(item)
