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

from ballot.models import Ballot
from project.models import Project
 
from django.test import Client, TestCase
from django.core.urlresolvers import reverse

import datetime

class TimelineTest(TestCase):
    fixtures = ['site.json']
    
    def __check_page(self,url):
        response = self.client.get(url)
        # not logged in, should redirect to login page
        self.failUnlessEqual(response.status_code, 302)

        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        
    def test_timeline(self):
        url = reverse('ballot.views.main_page',args=[])
        self.__check_page(url)
        
    def test_wg(self):
        url = reverse('ballot.views.wg_page',args=[])
        self.__check_page(url)
        
    def test_sponsor(self):
        url = reverse('ballot.views.sponsor_page',args=[])
        self.__check_page(url)
        
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
