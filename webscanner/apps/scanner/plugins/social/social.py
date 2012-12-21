#! /usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
import urllib
import urllib2
import json
import re
from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
from scanner.plugins.plugin import PluginMixin
from scanner.models import STATUS,RESULT_STATUS, RESULT_GROUP
from settings import PATH_TMPSCAN, MEDIA_ROOT, MEDIA_URL


class PluginSocial(PluginMixin):
    name = unicode(_('Social'))
    wait_for_download = False

    def check_facebook(self, command):
        #normalized_url  string  The normalized URL for the page being shared.
        #share_count int The number of times users have shared the page on Facebook.
        #like_count  int The number of times Facebook users have "Liked" the page, or liked any comments or re-shares of this page.
        #comment_count   int The number of comments users have made on the shared story.
        #total_count int The total number of times the URL has been shared, liked, or commented on.
        #click_count int The number of times Facebook users have clicked a link to the page from a share or like.
        #comments_fbid   int The object_id associated with comments plugin comments for this url. This can be used to query for comments using the comment FQL table.
        #commentsbox_count   int The number of comments from a comments box on this URL. This only includes top level comments, not replies.

        api_url = "https://api.facebook.com/method/fql.query"
        args = {
            'query' : "select total_count,like_count,comment_count,share_count,click_count from link_stat where url='%s'"%command.test.url,
            'format' : 'json',
        }

        template = Template(open(os.path.join(os.path.dirname(__file__),'templates/facebook.html')).read())

        args_enc = urllib.urlencode(args)
        rawdata = urllib.urlopen(api_url, args_enc).read()
        fb_data = json.loads(rawdata)[0]

        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.seo,importance=3)
        res.output_desc = unicode(_("Facebook stats"))
        res.output_full = template.render(Context({'fb_data':fb_data}))

        if fb_data["total_count"] < 10:
            res.status = RESULT_STATUS.warning
        else:
            res.status = RESULT_STATUS.success
        res.save()

    def check_twitter(self, command):
        api_url = "http://urls.api.twitter.com/1/urls/count.json"
        args = {
            'url' : command.test.url,
        }

        template = Template(open(os.path.join(os.path.dirname(__file__),'templates/twitter.html')).read())

        args_enc = urllib.urlencode(args)
        rawdata = urllib.urlopen(api_url, args_enc).read()
        tw_data = json.loads(rawdata)

        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.seo,importance=2)
        res.output_desc = unicode(_("Twitter stats"))
        res.output_full = template.render(Context({'tw_data':tw_data}))

        if tw_data["count"] < 10:
            res.status = RESULT_STATUS.warning
        else:
            res.status = RESULT_STATUS.success
        res.save()


    def check_gplus(self, command):
        template = Template(open(os.path.join(os.path.dirname(__file__),'templates/gplus.html')).read())

        url = "https://plusone.google.com/u/0/_/+1/fastbutton?count=true&url=%s" % command.test.url

        rawdata = urllib2.urlopen(url).read()
        #<div id="aggregateCount" class="V1">1\xc2\xa0936</div>

        #remove non-breaking space
        rawdata = rawdata.replace("\xc2\xa0","")

        gplus1 = int(re.search(r"id\=\"aggregateCount\"[^>]*>([\d\s ]+)",rawdata).group(1))

        from scanner.models import Results
        res = Results(test=command.test, group=RESULT_GROUP.seo,importance=2)
        res.output_desc = unicode(_("Google+ stats"))
        res.output_full = template.render(Context({'gplus1':gplus1}))

        if gplus1 < 10:
            res.status = RESULT_STATUS.warning
        else:
            res.status = RESULT_STATUS.success
        res.save()


    def run(self, command):
        from scanner.models import Results

        if not command.test.check_seo:
            return STATUS.success
        self.check_facebook(command)
        self.check_twitter(command)
        self.check_gplus(command)


        #as plugin finished - its success
        return STATUS.success
