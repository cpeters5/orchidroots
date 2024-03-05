from django.contrib import admin
from common.models import (Family, Subfamily, Tribe, Subtribe)
from .models import Genus, Species, Accepted, Hybrid, Synonym, SpcImages, TestSpecies
# from .models import (Country, Continent, Region, SubRegion, LocalRegion, GeoLocation,
#                    GeoLoc, Subgenus, Section, Subsection, Series)

admin.autodiscover()
admin.site.enable_nav_sidebar = False

class SpeciesInline(admin.TabularInline):
    model = Species
    max_num = 1
    fields = [('source', 'orig_pid', 'genus', 'species', 'infraspr', 'infraspe', 'author', 'status', 'type', 'year')]

class GenusAdmin(admin.ModelAdmin):
    pass
    list_display = ('pid', 'orig_pid', 'genus', 'author', 'year', 'status', 'source', 'family', 'subfamily', 'tribe', 'subtribe',)
    fields = [('orig_pid', 'genus', 'author', 'year', 'status', 'source', 'common_name', 'family', 'subfamily', 'tribe', 'subtribe',)]
    ordering = ['genus']
    list_filter = ('family',)
    search_fields = ['genus', 'common_name', 'family__family', 'subfamily__subfamily', 'tribe__tribe', 'subtribe__subtribe']
    inlines = [SpeciesInline]

class SynonymInline(admin.TabularInline):
    model = Synonym
    fk_name = "spid"
    fields = [('acc')]

class AcceptedInline(admin.TabularInline):
    model = Accepted
    fields = [('pid', 'common_name', 'distribution', 'introduced')]

class TestSpeciesAdmin(admin.ModelAdmin):
    pass
    list_display = ('genus',)
    fields = [('genus',)]
    ordering = ['genus']
    list_filter = ('genus',)
    search_fields = ['genus']


class SpeciesAdmin(admin.ModelAdmin):
    pass
    list_display = ('orig_pid', 'gen', 'genus', 'species', 'infraspr', 'infraspe', 'author', 'year', 'status', 'source')
    fields = [('source', 'orig_pid', 'gen', 'genus', 'species', 'infraspr', 'infraspe', 'author', 'status', 'type', 'year')]
    ordering = ['genus', 'species']
    list_filter = ('genus',)
    search_fields = ['genus', 'species']
    # inlines = [AcceptedInline]
    # inlines = [SynonymInline]


class SynonymAdmin(admin.ModelAdmin):
    pass
    list_display = ('spid', 'acc')
    fields = [('spid', 'acc')]
    ordering = ['spid']
    list_filter = ('spid', 'acc',)
    search_fields = ['spid', 'acc']

class AcceptedAdmin(admin.ModelAdmin):
    pass
    list_display = ('pid', 'binomial', 'common_name')
    fields = [('pid', 'binomial', 'common_name', 'distribution', 'introduced', 'comment')]
    ordering = ['binomial']
    list_filter = ('binomial',)
    search_fields = ['genus', 'binomial', 'common_name', 'distribution']

admin.site.register(TestSpecies, TestSpeciesAdmin)
admin.site.register(Genus, GenusAdmin)
admin.site.register(Species, SpeciesAdmin)
admin.site.register(Synonym, SynonymAdmin)
admin.site.register(Accepted, AcceptedAdmin)
