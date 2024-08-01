from django.urls import reverse
from django.utils import timezone
from .models import SitemapEntry


def generate_sitemap_index(request):
    sitemap_count = (SitemapEntry.objects.count() // 50000) + 1

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for i in range(1, sitemap_count + 1):
        xml_content += f'  <sitemap>\n'
        xml_content += f'    <loc>{request.build_absolute_uri(reverse("sitemap_section", args=[i]))}</loc>\n'
        xml_content += f'    <lastmod>{timezone.now().isoformat()}</lastmod>\n'
        xml_content += f'  </sitemap>\n'

    xml_content += '</sitemapindex>'

    return xml_content


def generate_sitemap_section(section):
    start = (int(section) - 1) * 50000
    end = start + 50000
    entries = SitemapEntry.objects.all()[start:end]

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for entry in entries:
        xml_content += f'  <url>\n'
        xml_content += f'    <loc>{entry.url}</loc>\n'
        if entry.last_modified:
            xml_content += f'    <lastmod>{entry.last_modified.isoformat()}</lastmod>\n'
        xml_content += f'    <changefreq>weekly</changefreq>\n'
        xml_content += f'    <priority>0.5</priority>\n'
        xml_content += f'  </url>\n'

    xml_content += '</urlset>'

    return xml_content