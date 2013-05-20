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
