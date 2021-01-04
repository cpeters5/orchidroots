from django.contrib import admin
# from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile

from .forms import UserAdminCreationForm, UserAdminChangeForm
from .models import User, Profile, Photographer

class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'email', 'fullname','credited_name','admin','staff','active','created_date')
    list_filter = ('admin','fullname','credited_name','staff','active')
    fieldsets = (
        (None,            {'fields': ('username',)}),
        ('email address', {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('fullname','credited_name','specialty')}),
        ('Permissions', {'fields': ('admin','staff','active',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username','email', 'password', 'password2','fullname','specialty',)}
        ),
    )
    search_fields = ('email','username','fullname','specialty')
    ordering = ('username','email',)
    filter_horizontal = ()


# class ProfileAdmin(BaseUserAdmin):
#     search_fields = ('fullname','user','photo_credit','specialty',)
#     list_display = ('fullname', 'user', 'photo_credit','specialty','country')


class PhotographerAdmin(admin.ModelAdmin):
    pass
    list_display = ('author_id','fullname','user_id','displayname','expertise')
    list_filter = ('expertise',)
    fields = ['author_id',('fullname','displayname'),('affiliation','status'),'url']
    ordering = ['fullname']
    search_fields = ['author_id','fullname']



admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Photographer,PhotographerAdmin)



# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)