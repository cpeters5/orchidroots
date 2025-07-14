import logging

# views.py in your distribution application
from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator

from orchidaceae.models import Species, Distribution, Genus
from common.models import Continent, Region, SubRegion
from utils.views import write_output
app = 'orchidaceae'
logger = logging.getLogger(__name__)

def get_subregions(request):
    region_id = request.GET.get('region_id')
    if region_id:
        subregions = SubRegion.objects.filter(region_id=region_id).order_by('name')
    else:
        subregions = SubRegion.objects.all().order_by('name')
    data = [{'id': s.code, 'name': s.name} for s in subregions]
    return JsonResponse({'subregions': data})


def search(request):
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    page = (start // length) + 1
    per_page = length

    region_id = request.GET.get('region')
    subregion_id = request.GET.get('subregion')
    region_id = int(region_id) if region_id and region_id.isdigit() else None
    print("1", region_id, subregion_id)

    # ✅ Recover region_id from subregion_id if not provided
    if subregion_id and (not region_id or region_id == str(0)):
        try:
            region_id = SubRegion.objects.get(code=subregion_id).region_id
        except SubRegion.DoesNotExist:
            region_id = None
    genus = request.GET.get('genus')

    filters = Q()

    # ✅ EARLY EXIT if no region_id and no subregion_id
    if not region_id and not subregion_id:
        species_qs = Species.objects.none()
        genera = Genus.objects.none()
        subregions = SubRegion.objects.all()
    else:
        if subregion_id:
            filters &= Q(distributions__subregion_id=subregion_id)
        elif region_id:
            filters &= Q(distributions__region_id=region_id)

        search_term = request.GET.get('search[value]', '').strip()
        if search_term:
            filters &= (
                Q(binomial__icontains=search_term) |
                Q(gen__genus__icontains=search_term)
            )

        if genus:
            filters &= Q(gen__genus=genus)

        species_qs = Species.objects.filter(filters).distinct().order_by('binomial')

        # Sorting
        order_column_index = request.GET.get('order[0][column]', '0')
        order_direction = request.GET.get('order[0][dir]', 'asc')
        columns = ['speciesstat__best_image', 'binomial']

        if order_column_index.isdigit():
            sort_field = columns[int(order_column_index)]
            if order_direction == 'desc':
                sort_field = '-' + sort_field
            species_qs = species_qs.order_by(sort_field)

        genera_ids = species_qs.values_list('gen', flat=True).distinct()
        genera = Genus.objects.filter(pid__in=genera_ids).order_by('genus')

        subregions = SubRegion.objects.filter(region_id=region_id).order_by('name') if region_id else SubRegion.objects.all().order_by('name')

    # Paging
    paginator = Paginator(species_qs, per_page)
    page_obj = paginator.get_page(page)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        data = []
        for s in page_obj:
            if s.speciesstat and s.speciesstat.best_image:
                original_path = str(s.speciesstat.best_image)
                thumb_path = original_path.replace("images/species", "thumbs/species")
                image_url = f"/static/{thumb_path}"
            else:
                image_url = None

            data.append({
                'image': image_url,
                'species': s.binomial,
                'pid': s.pid,
            })

        return JsonResponse({
            'data': data,
            'recordsTotal': paginator.count,
            'recordsFiltered': paginator.count,
        })

    # Region dropdown is always shown
    regions = Region.objects.all().order_by('name')

    context = {
        'regions': regions,
        'subregions': subregions,
        'region_id': region_id,
        'subregion_id': subregion_id,
        'genera': genera,
        'genus': genus,
        'app': 'orchidaceae',
    }

    return render(request, 'distribution/search.html', context)
