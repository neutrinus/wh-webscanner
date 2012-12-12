
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


class UserProfileInlineAdmin(admin.StackedInline):
    inline_classes = ('grp-collapse grp-open',)
    model = UserProfile


class UserAdmin(UserAdmin):
    inlines = UserAdmin.inlines + [ UserProfileInlineAdmin ]
    fieldsets = UserAdmin.fieldsets
    list_display = ('pk','is_active','is_staff','is_superuser','email','credits','last_login','date_joined')
    list_display_links = ('pk','email')
    ordering = ('date_joined',)

    def credits(self, user):
        return user.userprofile.credits
    credits.admin_order_field = 'userprofile__credits'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
