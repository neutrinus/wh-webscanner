"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'webscanner.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
#from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard
#from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """

    def init_with_context(self, context):
        site_name = _("WebCheck admin dashboard")  # get_admin_site_name(context)

        self.children.append(modules.AppList(
            _('Django stuff'),
            column=1,
            collapsible=False,
            models=('django.contrib.*',),
        ))
        # append an app list module for "Applications"
        self.children.append(modules.AppList(
            _('WebCheck internals'),
            collapsible=False,
            column=1,
            css_classes=('collapse closed',),
            models=('scanner.*','payments.*','accounts.*',),
        ))

        # append a group for "Administration" & "Applications"
        self.children.append(modules.AppList(
            _('Other modules'),
            column=2,
            collapsible=True,
            css_classes=('collapse closed',),
            exclude=('django.contrib.*','scanner.*','payments.*','account.*'),
        ))

        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _('Links'),
            column=3,
            children=[
                {
                    'title': _('Django Documentation'),
                    'url': 'http://docs.djangoproject.com/',
                    'external': True,
                },
                {
                    'title': _('Grappelli Documentation'),
                    'url': 'http://packages.python.org/django-grappelli/',
                    'external': True,
                },
            ]
        ))

        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=30,
            collapsible=False,
            column=3,
        ))


