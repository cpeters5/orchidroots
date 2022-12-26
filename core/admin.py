from django.contrib import admin
from .models import (Family, Subfamily, Tribe, Subtribe)
# from .models import (Country, Continent, Region, SubRegion, LocalRegion, GeoLocation,
#                    GeoLoc, Subgenus, Section, Subsection, Series)

admin.autodiscover()
admin.site.enable_nav_sidebar = False

class SubfamilyInline(admin.TabularInline):
    model = Subfamily

class FamilyAdmin(admin.ModelAdmin):
    pass
    list_display = ('family','author','year','status','source', 'application', 'common_name', 'kingdom', 'clss', 'order', 'orig_pid',)
    fields = [('family','author','year','status','source', 'application', 'common_name', 'kingdom', 'clss', 'order', 'orig_pid', 'description',)]
    ordering = ['family']
    search_fields = ['family','kingdom', 'clss', 'order']
    # inlines = [SubfamilyInline]


# class TribeInline(admin.TabularInline):
#     model = Tribe
#     exclude = ['num_genus', 'description', 'status']

class SubfamilyAdmin(admin.ModelAdmin):
    pass
    list_display = ('subfamily', 'family', 'author','year',)
    list_filter = ('family',)
    fields = [('subfamily', 'family', 'author','year','description',)]
    ordering = ['subfamily']
    search_fields = ['subfamily', 'family__family']
    # inlines = [TribeInline]


# class SubtribeInline(admin.TabularInline):
#     model = Subtribe


class TribeAdmin(admin.ModelAdmin):
    pass
    list_display = ('tribe', 'subfamily', 'family', 'author','year',)
    list_filter = ('family', 'subfamily')
    fields = [('tribe', 'family', 'subfamily', 'author','year','description',)]
    ordering = ['family', 'subfamily', 'tribe']
    search_fields = ['family__family', 'subfamily__subfamily', 'tribe']
    # inlines = [SubtribeInline]


class SubtribeAdmin(admin.ModelAdmin):
    pass
    list_display = ('family', 'subfamily', 'tribe', 'subtribe', 'author','year',)
    list_filter = ('family', 'subfamily', 'tribe', )
    fields = [('subtribe', 'family', 'subfamily', 'tribe', 'author','year','description',)]
    ordering = ['subtribe', 'family', 'subfamily', 'tribe']
    search_fields = ['subtribe', 'family__family', 'subfamily__subfamily', 'tribe__tribe']



# class SubgenusAdmin(admin.ModelAdmin):
#     list_display = ('subgenus','genus','source','year')
    # list_filter = ('source')
    # fields = ['subgenus','genus','source','author','citation','year','description']
    # ordering = ['subgenus','genus']
    # search_fields = ['subgenus','source']

    # fieldsets = (
    #     (None,            {'fields': ('subgenus','genus')}),
    #     ('Source', {'fields': ('author','citation','year','source','description')}),
    # )

# Genera
admin.site.register(Family, FamilyAdmin)
admin.site.register(Subfamily, SubfamilyAdmin)
admin.site.register(Tribe, TribeAdmin)
admin.site.register(Subtribe, SubtribeAdmin)
# admin.site.register(Subgenus,SubgenusAdmin)
# admin.site.register(Section)
# admin.site.register(Subsection)
# admin.site.register(Series)
# admin.site.register(Country)
# admin.site.register(Continent)
# admin.site.register(Region)
# admin.site.register(SubRegion)
# admin.site.register(LocalRegion)
# admin.site.register(GeoLocation)
# admin.site.register(GeoLoc)

# Donation

# @admin.register(Donation)
# class DonationAdmin(admin.ModelAdmin):
#     list_display = ('amount', 'source', 'donor_name', 'donor_display_name', 'country_code', 'status', 'created_date')
