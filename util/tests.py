#############################################################################
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#############################################################################
#
#  Project Name        :    IEEE 802.11 Timeline Tool#                                                                            *
#
#  Author              :    Alex Ashley
#
#############################################################################

from util.io import from_isodatetime, flatten, parse_date
from util.tasks import run_test_task_queue
from util.models import SiteURLs

from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.db.models.fields import URLField
from django.conf import settings
from django.utils import http

import datetime, decimal
import unittest

class LoginBasedTest(TestCase):    
    def setUp(self):
        self.logged_in = None
        self._user = None
        self._factory = None
        
    def _check_page(self,url, status_code=200):
        response = self.client.get(url)
        if not self.logged_in:
            # not logged in, should redirect to login page
            self.failUnlessEqual(response.status_code, 302)
            self.assertRedirects(response,settings.LOGIN_URL+'?next='+http.urlquote(url))
            self.logged_in = self.client.login(username='test', password='password')
            self.failUnless(self.logged_in, 'Could not log in')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, status_code)
        return response
    
    @property
    def user(self):
        if self._user is None:
            self._user = authenticate(username='test', password='password')
        return self._user
    
    @property
    def factory(self):
        if self._factory is None:
            self._factory = RequestFactory()
        return self._factory
    
    def get_request(self,url):
        request = self.factory.get(url)
        request.user = self.user 
        return request
    
    def wait_for_backlog_completion(self, models, timeout):
        count = 0
        if not isinstance(models,list):
            models = [models]
        for m in models:
            p = m.backlog_poll()
            count += p.active + p.waiting
        idle_count = 2
        timeout = idle_count * max(count,timeout) 
        while idle_count>0:
            run_test_task_queue(self.client)
            idle = True
            for m in models:
                p = m.backlog_poll()
                idle = idle and p.idle
            if idle:
                idle_count -= 1
            else:
                timeout -= 1
                self.failIf(timeout<0)
        
class UtilTest(unittest.TestCase):
    def test_from_isodatetime(self):
        """
        Tests converting from ISO 8601 string to Python datetime / timedelta objects
        """
        tests = [
                 ('2009-02-27T10:00:00Z', datetime.datetime(2009,2,27,10,0,0) ),
                 ('PT14H00M00S', datetime.timedelta(hours=14) ),
                 ('PT00H45M00S', datetime.timedelta(minutes=45) ),
                 ('PT01:45:19', datetime.timedelta(hours=1,minutes=45,seconds=19) ),
                 ]
        for test in tests:
            tc = from_isodatetime(test[0])
            self.failUnlessEqual(tc,test[1])

    def test_flatten(self):
        """
        Tests converting Python objects to form suitable for storage
        """
        tests = [
                 ([1,2,3],[1,2,3]),
                 ([1,2L,3],[1,'2',3]),
                 ( [1, 2L, 3, datetime.datetime(2009, 8, 13, 10, 52, 8, 734209)], [1, '2', 3, '2009-08-13T10:52:08.734209Z']),
                 ( (1, 2L, 3, datetime.datetime(2009, 8, 13, 10, 52, 8, 734209)), (1, '2', 3, '2009-08-13T10:52:08.734209Z') ),
                 ( [decimal.Decimal('5.2'), u'Hello World', datetime.date(2009, 8, 13)], ['5.2', 'Hello World', '2009-08-13'] ),
                 ({'a': decimal.Decimal('5.2'), 'c': datetime.date(2009, 8, 13), 'b': u'Hello World'}, {'a': '5.2', 'c': '2009-08-13', 'b': 'Hello World'}),
                 ]
        for test in tests:
            f = flatten(test[0])
            self.failUnlessEqual(f,test[1])
            
    def test_date_parse(self):
        dates = [
                 ('2008-05-03', datetime.datetime(2008,5,3)), 
                 ('05/30/06', datetime.datetime(2006,5,30)), 
                 ('05/30/2006', datetime.datetime(2006,5,30)), 
                 ('Mon Sep 27, 2010', datetime.datetime(2010,9,27)),
                 ('Sep 16 2007 - 23:59 ET', datetime.datetime(2007,9,17,4,59)),
                 ('October 16 2007 - 23:59 ET', datetime.datetime(2007,10,17,4,59)),
                 ('May 2, 2007 - 23:59 ET', datetime.datetime(2007,5,3,4,59)),
                 ('Sep-14', datetime.datetime(2014,9,1)),
                 ('09/xx/14', datetime.datetime(2014,9,1)), 
                 ('May 14', datetime.datetime(2014,5,1)), 
                 ('Oct 2014', datetime.datetime(2014,10,1)), 
                 ('October 7 2014', datetime.datetime(2014,10,7)) ,
                 ('Jul 26 2013', datetime.datetime(2013,7,26)), 
                 ('March 26 2013', datetime.datetime(2013,3,26)) 
                 ]
        for s,d in dates:
            v = parse_date(s)
            self.failIfEqual(v,None,s)
            self.failUnlessEqual(v,d,s)
                               
class EditUrlsPageTest(LoginBasedTest):
    fixtures = ['site.json','projects.json']
    
    def test_edit_urls(self):
        """
        Tests edit urls page
        """

        default = SiteURLs.get_urls()
        url = reverse('util.views.edit_urls',args=[])
        response = self._check_page(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, '<input type="submit" name="submit"')
        urls = response.context['object']
        post = {'submit':'submit'}
        for field in urls._meta.fields:
            if field.editable and not field.primary_key :
                dft = getattr(default,field.attname)
                a = getattr(urls,field.attname)
                self.failUnlessEqual(a,dft)
                if isinstance(field,URLField):
                    post[field.attname] = a+'/Test'
                else:
                    # assume it's an email field
                    post[field.attname] = 'Test User <test@example-net.org>'
        response = self.client.post(url, post, follow=True)      
        # The POST should have caused the site URLs to change, so get the new URLS and compare them to the defaults
        new_urls = SiteURLs.get_urls()
        for field in urls._meta.fields:
            if not field.primary_key:
                dft = getattr(default,field.attname)
                a = getattr(new_urls,field.attname)
                self.failIfEqual(a,dft)
                if field.editable:
                    self.failUnlessEqual(a,post[field.attname])
        del post['submit']
        post['cancel']='Cancel'
        post['timeline_history'] = 'http://example.domain.com/cancel/test'
        self.client.post(url, post, follow=True)
        self.failIfEqual(post['timeline_history'], new_urls.timeline_history)