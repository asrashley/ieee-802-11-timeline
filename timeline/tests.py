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
from project.models import Project
from ballot.models import Ballot
from timeline.models import DenormalizedProjectBallots, ProjectBallotsBacklog, check_project_ballot_backlog
from util.tasks import run_test_task_queue

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

class TimelineTestBase(TestCase):
    fixtures = ['site.json']
    PROJECT_COUNT = 0
    BALLOT_COUNT = 0
    
    def _check_page(self,url):
        response = self.client.get(url)
        # not logged in, should redirect to login page
        self.failUnlessEqual(response.status_code, 302)

        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        return response
    
    def test_timeline(self):
        static_url = settings.STATICFILES_URL
        self.assertEqual(Project.objects.count(),self.PROJECT_COUNT)
        self.assertEqual(Ballot.objects.count(),self.BALLOT_COUNT)
        url = reverse('timeline.views.main_page',args=[])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        #response.content.index(static_url)
        self.assertContains(response,static_url)
        
    def test_html_export(self):
        static_url = settings.STATICFILES_URL
        url = ''.join([reverse('timeline.views.main_page',args=[]),'timeline.html'])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        self.assertContains(response, 'oilerplate')
        self.failUnlessRaises(ValueError, response.content.index,static_url)
        
    def test_shtml_export(self):
        static_url = settings.STATICFILES_URL
        url = ''.join([reverse('timeline.views.main_page',args=[]),'timeline.shtml'])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        self.assertContains(response, '#include file="banner_head.html')
        self.assertNotContains(response, 'oilerplate')
        self.failUnlessRaises(ValueError, response.content.index,static_url)

class TestProjectsNoBallots(TimelineTestBase):
    fixtures = ['site.json', 'projects.json']
    PROJECT_COUNT = 37

class TestProjectsAndBallots(TimelineTestBase):
    fixtures = ['site.json', 'projects.json', 'ballots.json']
    PROJECT_COUNT = 37
    BALLOT_COUNT = 269
    
    def test_denormalise(self):
        self.assertEqual(Project.objects.count(),self.PROJECT_COUNT)
        self.assertEqual(Ballot.objects.count(),self.BALLOT_COUNT)
        self.assertEqual(DenormalizedProjectBallots.objects.count(),0)
        for proj in Project.objects.all():
            pbb = ProjectBallotsBacklog(project_pk=proj.pk)
            pbb.update_initial_wg = True 
            pbb.update_recirc_wg = True
            pbb.update_initial_sb = True
            pbb.update_recirc_sb = True
            pbb.save()
        check_project_ballot_backlog()
        run_test_task_queue(self.client)
        self.assertEqual(DenormalizedProjectBallots.objects.count(),self.PROJECT_COUNT)
        proj = Project.objects.get(pk=38)
        dpb = DenormalizedProjectBallots.objects.get(project_pk=proj.pk)
        self.assertEqual(len(dpb.initial_wg_ballots),1)
        self.assertEqual(len(dpb.recirc_wg_ballots),4)
        self.assertEqual(len(dpb.initial_sb_ballots),1)
        self.assertEqual(len(dpb.recirc_sb_ballots),6)
        self.test_html_export()
            
class TestProjectsAndBallotsDN(TimelineTestBase):
    fixtures = ['site.json', 'projects.json', 'ballots.json', 'timelines.json']
    PROJECT_COUNT = 37
    BALLOT_COUNT = 269
