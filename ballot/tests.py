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

from ballot.models import Ballot, DenormalizedBallot
from ballot.views import BallotForm
from project.models import Project
from util.tasks import run_test_task_queue

from django.test import TestCase
from django.core.urlresolvers import reverse

import datetime
from django.conf import settings
from util.tests import LoginBasedTest

class BallotBaseTest(LoginBasedTest):            
    def _check_ballot_page(self,url,export, redirect=False):
        static_url = settings.STATICFILES_URL
        status_code = 302 if redirect else 200
        response = self._check_page(url, status_code)
        if redirect:
            url=response.get('Location')
            response = self._check_page(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, 'ieeel.gif')
        response.content.index(static_url)
        response = self.client.get(export)
        self.assertContains(response, 'ieeel.gif')
        self.failUnlessRaises(ValueError, response.content.index,static_url)
        return response
        
class BallotTest(BallotBaseTest):
    fixtures = ['site.json', 'projects.json', 'ballots.json']

    def _check_ballot(self,ballot,response, prefix):
        if ballot.draft:
            self.assertContains(response,ballot.draft, msg_prefix=prefix)
        if ballot.pool:
            self.assertContains(response,ballot.pool, msg_prefix=prefix)
        if ballot.vote_for:
            self.assertContains(response,ballot.vote_for, msg_prefix=prefix)
        if ballot.vote_against:
            self.assertContains(response,ballot.vote_against, msg_prefix=prefix)
        if ballot.draft_url:
            self.assertContains(response,ballot.draft_url, msg_prefix=prefix)
        if ballot.redline_url:
            self.assertContains(response,ballot.redline_url, msg_prefix=prefix)
        if ballot.resolution_url:
            self.assertContains(response,ballot.resolution_url, msg_prefix=prefix)
        if ballot.template_url:
            self.assertContains(response,ballot.template_url, msg_prefix=prefix)
        if ballot.pool_url:
            self.assertContains(response,ballot.pool_url, msg_prefix=prefix)
        days = ballot.days
        if days>0:
            self.assertContains(response,days, msg_prefix=prefix)            
                
    def test_wg(self, params=None):
        url = reverse('ballot.views.wg_page',args=[])
        if params is not None:
            url += '?'+'&'.join(['%s=%s'%(k,str(v)) for k,v in params.iteritems()])
        export = ''.join([reverse('ballot.views.main_page',args=[]),'LetterBallots.html'])
        response = self._check_ballot_page(url, export)
        for ballot in Ballot.objects.all():
            if ballot.ballot_type!=Ballot.SBInitial.code and ballot.ballot_type!=Ballot.SBRecirc.code:
                self.assertContains(response,ballot.number, msg_prefix='WorkingGroup')
                self.assertContains(response,ballot.project.task_group, msg_prefix='WorkingGroup')
                self._check_ballot(ballot, response, 'WorkingGroup')
                
    def test_refresh_wg(self):
        url = reverse('ballot.views.wg_page',args=[])
        response = self._check_page(url+'?refresh=1', status_code=302)
        run_test_task_queue(self.client)
        response = self._check_page(url+'?redraw=0', status_code=302)
        run_test_task_queue(self.client)
        response = self._check_page(url+'?redraw=1', status_code=302)
        run_test_task_queue(self.client)
            
    def test_sponsor(self, params=None,redirect=False):
        url = reverse('ballot.views.sponsor_page',args=[])
        if params is not None:
            url += '?'+'&'.join(['%s=%s'%(k,str(v)) for k,v in params.iteritems()])
        export = ''.join([reverse('ballot.views.main_page',args=[]),'SponsorBallots.html'])
        response = self._check_ballot_page(url, export, redirect=redirect)
        for ballot in Ballot.objects.all():
            if ballot.ballot_type==Ballot.SBInitial.code or ballot.ballot_type==Ballot.SBRecirc.code:
                self.assertContains(response,ballot.project.name, msg_prefix='Sponsor')
                self._check_ballot(ballot, response, 'Sponsor')
        self.assertContains(response,'IEEE-SA SPONSOR BALLOTS AS RELATED TO IEEE 802.11 WG')
                
    def test_refresh_sb(self):
        self.test_sponsor({'refresh':1}, redirect=True)
        self.test_sponsor({'redraw':0}, redirect=True)
        self.test_sponsor({'redraw':1}, redirect=True)
                
class BallotTestNoData(BallotBaseTest):
    fixtures = ['site.json']
    def test_main(self):
        url = reverse('ballot.views.main_page',args=[])
        self._check_page(url+'?refresh=1', status_code=302)
        response = self._check_page(url)
        url = reverse('ballot.views.wg_page',args=[])
        self.assertContains(response,url)
        url = reverse('ballot.views.sponsor_page',args=[])
        self.assertContains(response,url)
        url = reverse('ballot.views.add_ballot',args=[])
        self.assertContains(response,url)
        self._check_page(url+'?refresh=1')

    def test_add_ballot(self):
        self.failUnlessEqual(Project.objects.count(),0)
        self.failUnlessEqual(Ballot.objects.count(),0)
        proj = Project(name='test',order=0, doc_type='STD', description='ballot test', task_group='TGx', par_date=datetime.datetime.now())
        proj.save()
        self.failUnlessEqual(Project.objects.count(),1)
        url = reverse('ballot.views.add_ballot',args=[])
        response = self._check_page(url)
        data = {
                'project' : proj.pk,
                'number':123,
                'draft': 1.0,
                'opened' : '2013-05-01',
                'closed' : '2013-05-16',
                'ballot_type' : Ballot.WGInitial.code,
                'pool': 321,
                'vote_for':'',
                'vote_against':'',
                'vote_abstain':'',
                'vote_invalid':'',
                'comments':'',
                'instructions_url': 'http://grouper.ieee.org/instructions',
                'draft_url': 'http://grouper.ieee.org/draft',
                'redline_url':'',
                'resolution_url':'',
                'template_url': 'http://grouper.ieee.org/template',
                'pool_url': 'http://grouper.ieee.org/pool',
                'curstat': response.context['form'].initial['curstat'],
                'curpk':'',
                'submit':'Save'
                }
        response = self.client.post(url, data, follow=True)      
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(Ballot.objects.count(),1)
        data['draft'] = 2.0
        del data['submit']
        data['cancel'] = 'Cancel' 
        data['number'] += 1
        response = self.client.post(url, data, follow=True)      
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(Ballot.objects.count(),1)
        ballot = Ballot.objects.get(pk=123)
        self.failUnless(ballot.is_wg_ballot)
        self.failUnless(ballot.is_initial_ballot)
        
    def test_edit_ballot(self):
        proj = Project(name='test',order=0, doc_type='STD', description='test edit ballot', task_group='TGx', par_date=datetime.datetime.now())
        proj.save()
        bal = Ballot(number=123,project=proj, ballot_type=Ballot.WGInitial.code, draft='1.0', opened=datetime.datetime.now(), pool=100)
        bal.closed = bal.opened + datetime.timedelta(days=15)
        bal.save()
        url = reverse('ballot.views.edit_ballot',args=[bal.number])
        response = self._check_page(url)
        data = response.context['form'].initial
        for key in data.keys():
            if data[key] is None:
                data[key] = ''
        data['curpk'] = bal.pk
        data['draft'] = '2.0'
        data['submit']='Save'
        form = BallotForm(data, instance=bal)
        valid = form.is_valid()
        self.failUnless(valid)
        response = self.client.post(url,data)
        self.failIf(response.status_code!=302 and response.status_code!=303)
        self.failUnlessEqual(Ballot.objects.count(),1)
        bal = Ballot.objects.get(pk=123)
        self.failUnlessEqual(float(bal.draft),2.0)
        # test renumbering the ballot, which should cause the old ballot object to be deleted
        data['number'] = 125
        form = BallotForm(data, instance=bal)
        valid = form.is_valid()
        self.failUnless(valid)
        response = self.client.post(url,data)
        self.failIf(response.status_code!=302 and response.status_code!=303)
        self.failUnlessEqual(Ballot.objects.count(),1)
        bal = Ballot.objects.get(pk=125)
        self.failUnlessRaises(Ballot.DoesNotExist,Ballot.objects.get,pk=123)
        
    def test_delete_ballot(self):
        proj = Project(name='test',order=0, doc_type='STD', description='', task_group='TGx', par_date=datetime.datetime.now())
        proj.save()
        bal = Ballot(number=123,project=proj, draft='1.0', opened=datetime.datetime.now(), pool=100)
        bal.closed = bal.opened + datetime.timedelta(days=15)
        bal.save()
        self.failUnlessEqual(bal.pk,123)
        self.failUnlessEqual(Ballot.objects.count(),1)
        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        url = reverse('ballot.views.main_page',args=[])
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(Ballot.objects.count(),1)
        #run_test_task_queue(response.request)
        run_test_task_queue(self.client)
        self.failUnlessEqual(Ballot.objects.count(),1)
        dn = DenormalizedBallot.objects.get(pk=bal.pk)
        self.failIfEqual(dn,None)
        self.failUnlessEqual(Ballot.objects.count(),1)
        Ballot.objects.filter(pk=bal.number).delete()
        run_test_task_queue(self.client)
        self.failUnlessRaises(DenormalizedBallot.DoesNotExist, DenormalizedBallot.objects.get, pk=123)
        
    def test_renumber_ballot(self):
        proj = Project(name='test',order=0, doc_type='STD', description='', task_group='TGx', par_date=datetime.datetime.now())
        proj.save()
        self.failUnlessEqual(Project.objects.count(),1)
        self.failUnlessEqual(Ballot.objects.count(),0)
        bal = Ballot(number=123,project=proj, draft='1.0', opened=datetime.datetime.now(), pool=100)
        bal.closed = bal.opened + datetime.timedelta(days=15)
        bal.save()
        self.failUnlessEqual(Ballot.objects.count(),1)
        url = reverse('ballot.views.main_page',args=[])
        self._check_page(url)
        #response = self.client.get(url)
        run_test_task_queue(self.client)
        dn = DenormalizedBallot.objects.get(pk=bal.pk)
        bal2 = Ballot.objects.get(number=bal.number)
        bal2.number = 321
        bal2.save()
        Ballot.objects.get(number=123).delete()
        run_test_task_queue(self.client)
        self.failUnlessRaises(DenormalizedBallot.DoesNotExist, DenormalizedBallot.objects.get, number=123)
        dn = DenormalizedBallot.objects.get(number=bal2.number)
                
