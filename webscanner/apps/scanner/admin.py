
from django.contrib.admin import site
from django.contrib import admin

from models import *


class ResultsInlineAdmin(admin.TabularInline):
    model = Results
    extra = 0
    readonly_fields = ('status', 'creation_date', 'test', 'group', 'importance')
    has_add_permission = lambda s, r: False


class CommandQueueInlineAdmin(admin.TabularInline):
    model = CommandQueue
    extra = 0
    readonly_fields = ('finish_date', 'run_date', 'status', 'testname', 'wait_for_download')
    has_add_permission = lambda s, r: False


class TestsAdmin(admin.ModelAdmin):
    model = Tests
    search_fields = ['uuid', 'url', 'user__email', 'user_ip', 'download_path']
    readonly_fields = ('uuid', 'uuid','url' , 'user_ip', 'user', 'creation_date' ,
                       'download_path', '_percent_progress','_duration',
                       'check_seo','check_performance','check_security','check_mail', 'download_status')
    ordering = ('-creation_date',)

    fieldsets = (
        (None, {'fields': (('uuid','url'),('user','user_ip'),'check_seo','check_performance','check_security','check_mail'),}),
        ("progress", {'fields': (('_percent_progress', '_duration'),)}),
        ('others', {'fields': ('creation_date','download_status','download_path','is_deleted')}),
        )

    list_per_page = 50
    list_display = ('uuid', 'url', 'user', '_percent_progress', '_duration',  'is_deleted', 'creation_date')
    list_filter = ('creation_date', 'is_deleted')
    list_select_related = True
    has_add_permission = lambda s,r:False

    inlines = [
        ResultsInlineAdmin,
        CommandQueueInlineAdmin
    ]

    def queryset(self, request):
        return super(TestsAdmin, self).queryset(request).select_related()

    def _percent_progress(self, obj):
        return u'%.2f %%' % obj.percent_progress()

    def _duration(self, obj):
        return u'%.2f s.' % obj.duration()

site.register(Tests, TestsAdmin)
