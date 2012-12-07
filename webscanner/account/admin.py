
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInlineAdmin(admin.TabularInline):
    model = UserProfile

class UserAdmin(UserAdmin):
    inlines = UserAdmin.inlines + [ UserProfileInlineAdmin ]

User.__unicode__ = lambda self: self.email

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
