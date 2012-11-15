
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin
from django.contrib.admin import site
from django.contrib import admin
from django import forms

from models import *

#site.unregister(User)
#site.register(User,UserWithProfile)


class ResultsInlineAdmin(admin.TabularInline):
    model = Results
    extra = 0
    readonly_fields = ( 'creation_date', )

class CommandQueueInlineAdmin(admin.TabularInline):
    model = CommandQueue
    extra = 0
    readonly_fields = ( 'finish_date', 'run_date' )

class TestsAdmin(admin.ModelAdmin):
    model = Tests
    list_per_page = 100
    readonly_fields = ( 'user_ip', 'user', 'creation_date' ,'download_path')
    list_display = ('url','priority', 'percent_progress', 'user', 'is_deleted', 'creation_date')
    ordering = ('-creation_date',)
    list_filter = ('creation_date', 'is_deleted')
    search_fields = ['uuid', 'url', 'user_ip', 'download_path']
    inlines = [
        ResultsInlineAdmin,
        CommandQueueInlineAdmin
    ]

site.register(Tests, TestsAdmin)




