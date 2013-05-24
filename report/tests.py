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
#  Project Name        :    IEEE 802.11 Timeline Tool
#
#  Author              :    Alex Ashley
#
#############################################################################
from report.models import MeetingReport

from django.test import TestCase
from django.core.urlresolvers import reverse

class ReportTestBase(TestCase):
    def _check_page(self,url):
        print url
        response = self.client.get(url)
        # not logged in, should redirect to login page
        self.failUnlessEqual(response.status_code, 302)

        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        return response
        
class EmptyReportTest(ReportTestBase):
    fixtures = ['site.json']
    def test_report(self):
        from django.conf import settings
        static_url = settings.STATICFILES_URL
        url = reverse('report.views.main_page',args=[])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        response.content.index(static_url)
        
    def test_export(self):
        from django.conf import settings
        static_url = settings.STATICFILES_URL
        url = ''.join([reverse('report.views.main_page',args=[]),'meeting-reports.html'])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        self.failUnlessRaises(ValueError, response.content.index,static_url)

class ReportTest(ReportTestBase):
    from django.conf import settings
    static_url = settings.STATICFILES_URL
    fixtures = ['site.json','reports.json']
    
    def test_report(self):
        self.assertGreater(MeetingReport.objects.count(), 0, "Failed to load reports.json fixture")
        url = reverse('report.views.main_page',args=[])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        response.content.index(self.static_url)
        
    def test_export(self):
        self.assertGreater(MeetingReport.objects.count(), 0, "Failed to load reports.json fixture")
        url = ''.join([reverse('report.views.main_page',args=[]),'meeting-reports.html'])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        self.failUnlessRaises(ValueError, response.content.index,self.static_url)
