from django.contrib.sitemaps import Sitemap
from other.models import Species


class SpeciesSitemap(Sitemap):
    changefreq = "always"
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Species.objects.all()

    def lastmod(self, obj):
        return obj.modified_date

    def location(self, obj):
        return '/display/photos/%s/?family=%s' % (obj.pid, obj.family)
