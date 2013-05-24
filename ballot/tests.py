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
from project.models import Project
from util.tasks import run_test_task_queue #, init_test_task_queue

from django.test import TestCase
from django.core.urlresolvers import reverse

import datetime

class BallotTest(TestCase):
    fixtures = ['site.json']
    
    def __check_page(self,url):
        response = self.client.get(url)
        # not logged in, should redirect to login page
        self.failUnlessEqual(response.status_code, 302)

        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        return response
        
    def _check_ballot_page(self,url,export):
        from django.conf import settings
        static_url = settings.STATICFILES_URL
        response = self.__check_page(url)
        self.assertContains(response, 'ieeel.gif')
        response.content.index(static_url)
        response = self.client.get(export)
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, 'ieeel.gif')
        self.failUnlessRaises(ValueError, response.content.index,static_url)
        
    def test_main(self):
        url = reverse('ballot.views.main_page',args=[])
        self.__check_page(url)
        
    def test_wg(self):
        url = reverse('ballot.views.wg_page',args=[])
        export = ''.join([reverse('ballot.views.main_page',args=[]),'LetterBallots.html'])
        self._check_ballot_page(url, export)
        
    def test_sponsor(self):
        url = reverse('ballot.views.sponsor_page',args=[])
        export = ''.join([reverse('ballot.views.main_page',args=[]),'SponsorBallots.html'])
        self._check_ballot_page(url, export)
                
    def test_add_ballot(self):
        url = reverse('ballot.views.add_ballot',args=[])
        self.__check_page(url)
        
    def test_edit_ballot(self):
        proj = Project(name='test',order=0, doc_type='STD', description='', task_group='TGx', par_date=datetime.datetime.now())
        proj.save()
        bal = Ballot(number=123,project=proj, draft='1.0', opened=datetime.datetime.now(), pool=100)
        bal.closed = bal.opened + datetime.timedelta(days=15)
        bal.save()
        url = reverse('ballot.views.edit_ballot',args=[bal.number])
        self.__check_page(url)
        
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
        dn = DenormalizedBallot.objects.get(ballot_pk=bal.number)
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
        self.__check_page(url)
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
                
