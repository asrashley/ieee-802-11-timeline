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

import datetime

from django.core.urlresolvers import reverse
from django.conf import settings

from report.models import MeetingReport
from util.tests import LoginBasedTest

class EmptyReportTest(LoginBasedTest):
    fixtures = ['site.json']
    def test_report(self):
        static_url = settings.STATICFILES_URL
        url = reverse('report.views.main_page',args=[])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        response.content.index(static_url)
        m = MeetingReport(session=123.5, 
                          start=datetime.date(2013,1,1), 
                          end=datetime.date(2013,1,8),
                          pending=False,
                          report='http://example.net/report.pdf',
                          minutes_doc='http://example.net/minutes.doc',
                          minutes_pdf='http://example.net/minutes.pdf',
                          venue='Waikoloa HI USA',
                          location='Hilton Waikoloa Village',
                          meeting_type=MeetingReport.Plenary.code
                          )
        m.save()
        m2 = MeetingReport.objects.get(session=123.5)
        
    def test_export(self):
        static_url = settings.STATICFILES_URL
        url = ''.join([reverse('report.views.main_page',args=[]),'meeting-reports.html'])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        self.failUnlessRaises(ValueError, response.content.index,static_url)

class ReportTest(LoginBasedTest):
    static_url = settings.STATICFILES_URL
    fixtures = ['site.json','reports.json']
    
    def _check_response(self,response):
        fields = ['session_num','report','minutes_doc','minutes_pdf','venue','location']
        for report in MeetingReport.objects.all():
            for field in fields:
                val = getattr(report, field)
                if val:
                    self.assertContains(response, val, msg_prefix=field)
        
    def test_report(self):
        self.assertGreater(MeetingReport.objects.count(), 0, "Failed to load reports.json fixture")
        url = reverse('report.views.main_page',args=[])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        response.content.index(self.static_url)
        self._check_response(response)
    
    def test_export(self):
        self.assertGreater(MeetingReport.objects.count(), 0, "Failed to load reports.json fixture")
        url = ''.join([reverse('report.views.main_page',args=[]),'meeting-reports.html'])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        self.failUnlessRaises(ValueError, response.content.index,self.static_url)
        self._check_response(response)
