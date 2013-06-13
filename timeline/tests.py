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
from timeline.models import DenormalizedProjectBallots, ProjectBallotsBacklog, check_project_ballot_backlog
from timeline.views import backlog_poll
from util.tasks import run_test_task_queue
from util.tests import LoginBasedTest
from util.cache import CacheControl

from django.core.urlresolvers import reverse
from django.conf import settings

import json

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
            for proj in Project.objects.all().iterator():
                self.assertContains(response, reverse('project.views.edit_project',args=[proj.pk]))
                for field in ['name','description', 'task_group', 'task_group_url','doc_version']: #proj._meta.fields:
                    value = getattr(proj,field)
                    if value:
                        self.assertContains(response, value, msg_prefix='%s.%s'%(proj.task_group,field))
        if DenormalizedProjectBallots.objects.exists() and DenormalizedBallot.objects.exists():            
            for ballot in DenormalizedBallot.objects.all().iterator():
                if ballot.ballot_type!=Ballot.Procedural.code:
                    self.assertContains(response, reverse('ballot.views.edit_ballot',args=[ballot.pk]))
                    for field in ['draft','closed','result']:
                        value = getattr(ballot,field)
                        if value:
                            self.assertContains(response, value, msg_prefix='%s LB%d.%s'%(ballot.project_name,ballot.number,field))
        
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
    
    def _check_denormalized_project(self,ballots):
        for b in ballots:
            self.assertEqual(b.pk, b.number)
            
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
        for dpb in DenormalizedProjectBallots.objects.all().iterator():
            self._check_denormalized_project(dpb.initial_wg_ballots)
            self._check_denormalized_project(dpb.recirc_wg_ballots)
            self._check_denormalized_project(dpb.initial_sb_ballots)
            self._check_denormalized_project(dpb.recirc_sb_ballots)
        self.test_html_export()
            
    def test_refresh_main(self):
        self.failUnlessEqual(ProjectBallotsBacklog.objects.count(),0)
        poll_url = reverse('timeline.views.backlog_poll',args=[])
        poll = backlog_poll(self.get_request(poll_url))
        status = json.loads(poll.content)
        self.failUnlessEqual(status['backlog'],False)
        self.failUnlessEqual(status['count'],0)

        url = reverse('timeline.views.main_page',args=[])
        self._check_page(url+'?refresh=1', status_code=302)
        poll = backlog_poll(self.get_request(poll_url))
        status = json.loads(poll.content)
        self.failUnlessEqual(status['backlog'],True)
        run_test_task_queue(self.client)
        #response = self._check_page(url)
        poll = backlog_poll(self.get_request(poll_url))
        status = json.loads(poll.content)
        self.failUnlessEqual(status['count'],self.PROJECT_COUNT)
        self.failUnlessEqual(status['backlog'],False)
        self.assertEqual(DenormalizedProjectBallots.objects.count(),self.PROJECT_COUNT)
        proj = Project.objects.get(pk=38)
        dpb = DenormalizedProjectBallots.objects.get(project_pk=proj.pk)
        self.assertEqual(len(dpb.initial_wg_ballots),1)
        self.assertEqual(len(dpb.recirc_wg_ballots),4)
        self.assertEqual(len(dpb.initial_sb_ballots),1)
        self.assertEqual(len(dpb.recirc_sb_ballots),6)
        for dpb in DenormalizedProjectBallots.objects.all().iterator():
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
        run_test_task_queue(self.client)
        
        in_progress_ver = cc.in_progress_ver
        published_ver = cc.published_ver
        withdrawn_ver = cc.withdrawn_ver
        self._check_page(url+'?redraw=1', status_code=302)
        self.failUnlessEqual(in_progress_ver, cc.in_progress_ver)
        self.failUnlessEqual(withdrawn_ver, cc.withdrawn_ver)
        self.failIfEqual(published_ver, cc.published_ver)
        run_test_task_queue(self.client)
        
        in_progress_ver = cc.in_progress_ver
        published_ver = cc.published_ver
        withdrawn_ver = cc.withdrawn_ver
        self._check_page(url+'?redraw=2', status_code=302)
        self.failUnlessEqual(in_progress_ver, cc.in_progress_ver)
        self.failUnlessEqual(published_ver, cc.published_ver)
        self.failIfEqual(withdrawn_ver, cc.withdrawn_ver)
        run_test_task_queue(self.client)

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
        ProjectBallotsBacklog.request_update(38)
        check_project_ballot_backlog(True)
        run_test_task_queue(self.client)
        DenormalizedProjectBallots.objects.get(pk=38)
        