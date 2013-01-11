
from django.core.urlresolvers import reverse
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
    list_display = ('pk','email', 'is_active','credits','last_login','date_joined', 'is_staff','is_superuser', 'user_tests_link')
    list_display_links = ('pk','email')
    ordering = ('date_joined',)

    def credits(self, user):
        return user.userprofile.credits
    credits.admin_order_field = 'userprofile__credits'

    def user_tests_link(self, user):
        return '<a href="%s?user=%s" target="_blank">tests</a>' % (reverse('admin:scanner_tests_changelist'), user.pk)
    user_tests_link.allow_tags = True


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
