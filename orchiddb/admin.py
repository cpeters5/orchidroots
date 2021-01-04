from django.contrib import admin
from .models import (Genus, Subfamily, Species, Hybrid, Accepted, Synonym, Intragen,Infragenspc, InfragenHybrid,
                     Comment, Culture, Similarity, SpcImages, HybImages, UploadFile, Country, Continent, Region,
                     SubRegion, LocalRegion, GeoLocation, GeoLoc, Distribution, Subgenus, Section, Subsection, Series,
                     Donation )

class SubgenusAdmin(admin.ModelAdmin):
    list_display = ('subgenus','genus','source','year')
    # list_filter = ('source')
    # fields = ['subgenus','genus','source','author','citation','year','description']
    ordering = ['subgenus','genus']
    search_fields = ['subgenus','source']

    fieldsets = (
        (None,            {'fields': ('subgenus','genus')}),
        ('Source', {'fields': ('author','citation','year','source','description')}),
    )

# Genera
admin.site.register(Subfamily)
admin.site.register(Genus)
# admin.site.register(Subgenus)
admin.site.register(Subgenus,SubgenusAdmin)
admin.site.register(Section)
admin.site.register(Subsection)
admin.site.register(Series)
admin.site.register(Infragenspc)
admin.site.register(Intragen)

# Orchid
admin.site.register(Species)
admin.site.register(Hybrid)
admin.site.register(InfragenHybrid)
admin.site.register(Accepted)
admin.site.register(Synonym)
admin.site.register(Comment)
admin.site.register(Culture)
admin.site.register(Similarity)

# Detail
admin.site.register(SpcImages)
admin.site.register(HybImages)
admin.site.register(UploadFile)

# Distribution
admin.site.register(Country)
admin.site.register(Continent)
admin.site.register(Region)
admin.site.register(SubRegion)
admin.site.register(LocalRegion)
admin.site.register(GeoLocation)
admin.site.register(GeoLoc)
admin.site.register(Distribution)

# Donation

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('amount', 'source', 'donor_name', 'donor_display_name', 'country_code', 'status', 'created_date')
