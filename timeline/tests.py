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
from project.models import Project, DenormalizedProject
from ballot.models import Ballot, DenormalizedBallot
from timeline.models import DenormalizedProjectBallots #, ProjectBallotsBacklog, check_project_ballot_backlog
from timeline.views import backlog_poll
from util.tests import LoginBasedTest
from util.cache import CacheControl

from django.core.urlresolvers import reverse
from django.conf import settings

import json, os

class TimelineTestBase(LoginBasedTest):
    fixtures = ['site.json']
    PROJECT_COUNT = 0
    BALLOT_COUNT = 0
        
    def test_timeline(self):
        static_url = settings.STATICFILES_URL
        self.assertEqual(Project.objects.count(),self.PROJECT_COUNT)
        self.assertEqual(Ballot.objects.count(),self.BALLOT_COUNT)
        url = reverse('timeline.views.main_page',args=[])
        response = self._check_page(url)
        self.assertContains(response, 'ieeel.gif')
        #response.content.index(static_url)
        self.assertContains(response,static_url)
        if DenormalizedProject.objects.exists():
            for proj in Project.objects.all():
                self.assertContains(response, reverse('project.views.edit_project',args=[proj.slug]))
                for field in ['name','description', 'task_group', 'task_group_url','doc_version']: #proj._meta.fields:
                    value = getattr(proj,field)
                    if value:
                        self.assertContains(response, value, msg_prefix='%s.%s'%(proj.task_group,field))
        if DenormalizedProjectBallots.objects.exists() and DenormalizedBallot.objects.exists():            
            for ballot in DenormalizedBallot.objects.all():
                if ballot.ballot_type!=Ballot.Procedural.code:
                    self.assertContains(response, reverse('ballot.views.edit_ballot',args=[ballot.pk]))
                    self.assertContains(response, '%.1f'%ballot.draft, msg_prefix='%s LB%d.%s'%(ballot.project_name,ballot.number,field))
                    if ballot.closed:
                        self.assertContains(response, ballot.closed.isoformat(), msg_prefix='%s LB%d.%s'%(ballot.project_name,ballot.number,field))
                    if ballot.result:
                        self.assertContains(response, '%2d%%'%ballot.result, msg_prefix='%s LB%d.%s'%(ballot.project_name,ballot.number,field))

    def test_html_export(self):
        BASE_DIR = os.path.dirname(__file__)
        static_url = settings.STATICFILES_URL
        url = ''.join([reverse('timeline.views.main_page',args=[]),'timeline.html'])
        response = self._check_page(url)
        self._check_css(os.path.join(BASE_DIR,"static","css","timeline.css"), response)
        self._check_site_css(response)
        self.assertContains(response, 'ieeel.gif')
        self.assertNotContains(response, static_url)
        self.failUnlessRaises(ValueError, response.content.index,static_url)
        
    def test_shtml_export(self):
        BASE_DIR = os.path.dirname(__file__)
        static_url = settings.STATICFILES_URL
        url = ''.join([reverse('timeline.views.main_page',args=[]),'timeline.shtml'])
        response = self._check_page(url)
        self._check_css(os.path.join(BASE_DIR,"static","css","timeline.css"), response)
        self.assertContains(response, 'ieeel.gif')
        self.assertContains(response, '#include file="banner_head.html')
        self.assertNotContains(response, static_url)
        self.failUnlessRaises(ValueError, response.content.index,static_url)

class TestProjectsNoBallots(TimelineTestBase):
    fixtures = ['site.json', 'projects.json']
    PROJECT_COUNT = 37

class TestProjectsAndBallots(TimelineTestBase):
    fixtures = ['site.json', 'projects.json', 'ballots.json']
    PROJECT_COUNT = 37
    BALLOT_COUNT = 269
    
    def _check_denormalized_project(self,ballots):
        for b in ballots:
            self.assertEqual(b.pk, b.number)

    def test_denormalise(self):
        self.assertEqual(Project.objects.count(),self.PROJECT_COUNT)
        self.assertEqual(DenormalizedProject.objects.count(),self.PROJECT_COUNT)
        self.assertEqual(Ballot.objects.count(),self.BALLOT_COUNT)
        self.assertEqual(DenormalizedProjectBallots.objects.count(),0)
        for proj in DenormalizedProject.objects.all():
            DenormalizedProjectBallots.request_update(proj)
        self.wait_for_backlog_completion([DenormalizedProjectBallots,DenormalizedProject], 10+self.BALLOT_COUNT+self.PROJECT_COUNT)
        self.assertEqual(DenormalizedProjectBallots.objects.count(),self.PROJECT_COUNT)
        proj = Project.objects.get(pk=38)
        dpb = DenormalizedProjectBallots.objects.get(pk=proj.pk)
        print dpb
        self.assertEqual(dpb.pk,proj.pk)
        self.assertEqual(dpb.project_task_group,proj.task_group)
        self.assertEqual(len(dpb.initial_wg_ballots),1)
        self.assertEqual(len(dpb.recirc_wg_ballots),4)
        self.assertEqual(len(dpb.initial_sb_ballots),1)
        self.assertEqual(len(dpb.recirc_sb_ballots),6)
        for dpb in DenormalizedProjectBallots.objects.all():
            self._check_denormalized_project(dpb.initial_wg_ballots)
            self._check_denormalized_project(dpb.recirc_wg_ballots)
            self._check_denormalized_project(dpb.initial_sb_ballots)
            self._check_denormalized_project(dpb.recirc_sb_ballots)
        self.test_html_export()
            
    def __disabled_refresh_main(self):
        #self.failUnlessEqual(ProjectBallotsBacklog.objects.count(),0)
        stats = DenormalizedProjectBallots.backlog_poll()
        self.failUnless(stats.idle)
        poll_url = reverse('timeline.views.backlog_poll',args=[])
        poll = backlog_poll(self.get_request(poll_url))
        status = json.loads(poll.content)
        self.failUnlessEqual(status['backlog'],0)
        url = reverse('timeline.views.main_page',args=[])
        self._check_page(url+'?refresh=1', status_code=302)
        self.wait_for_backlog_completion([DenormalizedProject, DenormalizedProjectBallots], Project.objects.count()+Ballot.objects.count())
        poll = backlog_poll(self.get_request(poll_url))
        print poll.content
        status = json.loads(poll.content)
        self.failUnlessEqual(status['backlog'],0)
        self.assertEqual(DenormalizedProjectBallots.objects.count(),self.PROJECT_COUNT)
        proj = Project.objects.get(pk=38)
        dpb = DenormalizedProjectBallots.objects.get(project_pk=proj.pk)
        self.assertEqual(len(dpb.initial_wg_ballots),1)
        self.assertEqual(len(dpb.recirc_wg_ballots),4)
        self.assertEqual(len(dpb.initial_sb_ballots),1)
        self.assertEqual(len(dpb.recirc_sb_ballots),6)
        for dpb in DenormalizedProjectBallots.objects.all():
            self._check_denormalized_project(dpb.initial_wg_ballots)
            self._check_denormalized_project(dpb.recirc_wg_ballots)
            self._check_denormalized_project(dpb.initial_sb_ballots)
            self._check_denormalized_project(dpb.recirc_sb_ballots)
        cc = CacheControl()
        in_progress_ver = cc.in_progress_ver
        published_ver = cc.published_ver
        withdrawn_ver = cc.withdrawn_ver
        self._check_page(url+'?redraw=0', status_code=302)
        self.failIfEqual(in_progress_ver, cc.in_progress_ver)
        self.failUnlessEqual(published_ver, cc.published_ver)
        self.failUnlessEqual(withdrawn_ver, cc.withdrawn_ver)
        self.wait_for_backlog_completion([DenormalizedProject, DenormalizedProjectBallots], Project.objects.count()+Ballot.objects.count())
        
        in_progress_ver = cc.in_progress_ver
        published_ver = cc.published_ver
        withdrawn_ver = cc.withdrawn_ver
        self._check_page(url+'?redraw=1', status_code=302)
        self.failUnlessEqual(in_progress_ver, cc.in_progress_ver)
        self.failUnlessEqual(withdrawn_ver, cc.withdrawn_ver)
        self.failIfEqual(published_ver, cc.published_ver)
        self.wait_for_backlog_completion([DenormalizedProject, DenormalizedProjectBallots], Project.objects.count()+Ballot.objects.count())
        
        in_progress_ver = cc.in_progress_ver
        published_ver = cc.published_ver
        withdrawn_ver = cc.withdrawn_ver
        self._check_page(url+'?redraw=2', status_code=302)
        self.failUnlessEqual(in_progress_ver, cc.in_progress_ver)
        self.failUnlessEqual(published_ver, cc.published_ver)
        self.failIfEqual(withdrawn_ver, cc.withdrawn_ver)
        self.wait_for_backlog_completion([DenormalizedProject, DenormalizedProjectBallots], Project.objects.count()+Ballot.objects.count())

        in_progress_ver = cc.in_progress_ver
        published_ver = cc.published_ver
        withdrawn_ver = cc.withdrawn_ver
        self._check_page(url+'?redraw=badNumber', status_code=302)
        self.failUnlessEqual(in_progress_ver, cc.in_progress_ver)
        self.failUnlessEqual(published_ver, cc.published_ver)
        self.failUnlessEqual(withdrawn_ver, cc.withdrawn_ver)
        
class TestProjectsAndBallotsDN(TimelineTestBase):
    fixtures = ['site.json', 'projects.json', 'ballots.json', 'timelines.json']
    PROJECT_COUNT = 37
    BALLOT_COUNT = 269
    
    def test_request_update(self):
        DenormalizedProjectBallots.objects.filter(pk=38).delete()
        proj = Project.objects.get(pk=38)
        DenormalizedProject.request_update(proj)
        self.wait_for_backlog_completion([DenormalizedProject, DenormalizedProjectBallots], Project.objects.count()+Ballot.objects.count())
        proj = DenormalizedProject.objects.get(pk=38) 
        DenormalizedProjectBallots.request_update(proj)
        #check_project_ballot_backlog(True)
        self.wait_for_backlog_completion([DenormalizedProject, DenormalizedProjectBallots], Project.objects.count()+Ballot.objects.count())
        DenormalizedProjectBallots.objects.get(pk=38)
        