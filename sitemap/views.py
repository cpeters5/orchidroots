from django.http import HttpResponse
from .custom_sitemaps import generate_sitemap_index, generate_sitemap_section

def sitemap_index(request):
    xml_content = generate_sitemap_index(request)
    return HttpResponse(xml_content, content_type='application/xml')

def sitemap_section(request, section):
    xml_content = generate_sitemap_section(section)
    return HttpResponse(xml_content, content_type='application/xml')