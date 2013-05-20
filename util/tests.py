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

from util.io import from_isodatetime, flatten
from util.tasks import run_test_task_queue
from ballot.models import *
from project.models import *

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

import datetime, decimal, sys
import unittest
import time

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
            
class ImportPageTest(TestCase):
    NOT_IDEMPOTENT = []

    def setUp(self):
        from util import tasks 
        tasks._test_task_queue = []
        tasks._completed_tasks = []

    def _post_import(self,url,filename,length=0):
        testfile = open(filename,'r')
        data = {
                'wipe_projects' : False,
                'wipe_ballots': False,
                'import' : 'Import',
                'file' : testfile
                }
        try:
            response = self.client.post(url, data, follow=True)
        except:
            raise
        finally:
            testfile.close()
        progress = response.context['progress']
        progress_url = reverse('util.views.import_progress',args=[progress.pk])
        self.failUnlessEqual(response.redirect_chain[0][1],302)
        self.failUnless(response.redirect_chain[0][0].endswith(progress_url))
        #print response.content
        #self.failIf(response.context['errors'])
        #print response.content
        if length:
            self.assertContains(response, 'input file contains %d line'%length)
        #self.assertContains(response, 'Finished Importing')
        while progress.finished is None:
            run_test_task_queue(response.request)
            response = self.client.get(progress_url)
            self.failUnlessEqual(response.status_code, 200)
            progress = response.context['progress']
        return response
        
class ImportHtmlPageTest(ImportPageTest):
    fixtures = ['site.json','projects.json']
    LB_BALLOT_HTML = 'util/fixtures/LetterBallots.htm'
    SB_BALLOT_HTML = 'util/fixtures/SponsorBallots.htm'
    
    def test_html_import(self):
        """
        Tests import page
        """

        url = reverse('util.views.import_page',args=[])
        response = self.client.get(url)
        # not logged in, should redirect to login page
        self.failUnlessEqual(response.status_code, 302)

        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, '<input type="submit" name="submit"')
        
        response = self._post_import(url, self.LB_BALLOT_HTML)

        #print 'results',response.context['results']
        counts = {}
        tmodels = { Ballot:0, Project: 0 }
        for m in tmodels.keys():
            self.failIfEqual(m.objects.count(),tmodels[m],msg='%s model has %d items, should have more than %d items'%
                                 (m._meta.verbose_name,m.objects.count(),tmodels[m]))
            counts[m] = m.objects.count()
        tmodels[Ballot] = counts[Ballot]
        
        # Check that a second attempt to import the data does not cause errors and does not add any new objects to the database
        response = self._post_import(url, self.LB_BALLOT_HTML)
        for m in tmodels.keys():
            self.failUnlessEqual(m.objects.count(),counts[m],msg='%s model had %d items, but after a second import has %d'%
                                 (m._meta.verbose_name,counts[m],m.objects.count()))
        
        response = self._post_import(url, self.SB_BALLOT_HTML)
        for m in tmodels.keys():
            self.failIfEqual(m.objects.count(),tmodels[m],msg='%s model has %d items, should have more than %d items'%
                                 (m._meta.verbose_name,m.objects.count(),tmodels[m]))
            counts[m] = m.objects.count()
            
        # Check that a second attempt to import the data does not cause errors and does not add any new objects to the database
        response = self._post_import(url, self.SB_BALLOT_HTML)
        for m in tmodels.keys():
            self.failUnlessEqual(m.objects.count(),counts[m],msg='%s model had %d items, but after a second import has %d'%
                                 (m._meta.verbose_name,counts[m],m.objects.count()))
     
class ImportCsvPageTest(ImportPageTest):
    fixtures = ['site.json']
    #TESTFILE = 'util/fixtures/timeline-2010-10-27-1146.csv' 
    TESTFILE = ('util/fixtures/timeline-2010-11-02-1439.csv' ,187)
    
    def test_csv_import(self):
        """
        Tests import page with CSV files
        """
            
        url = reverse('util.views.import_page',args=[])
        response = self.client.get(url)
        # not logged in, should redirect to login page
        self.failUnlessEqual(response.status_code, 302)

        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')

        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, '<input type="submit" name="submit"')
        #print response
        response = self._post_import(url, self.TESTFILE[0], self.TESTFILE[1])
        counts = {}
        tmodels = { Ballot:0, Project: 0 }
        for m in tmodels.keys():
            self.failIfEqual(m.objects.count(),tmodels[m],msg='%s model has %d items, should have more than %d items'%
                                 (m._meta.verbose_name,m.objects.count(),tmodels[m]))
            counts[m] = m.objects.count()
        # Check that a second attempt to import the data does not cause errors and does not add any new objects to the database
        response = self._post_import(url, self.TESTFILE[0], self.TESTFILE[1])
        for m in tmodels.keys():
            if m in self.NOT_IDEMPOTENT:
                self.failIfEqual(m.objects.count(),counts[m],msg='%s model had %d items, but after a second import it still has %d'%
                                     (m._meta.verbose_name,counts[m],m.objects.count()))
            else:
                self.failUnlessEqual(m.objects.count(),counts[m],msg='%s model had %d items, but after a second import has %d'%
                                     (m._meta.verbose_name,counts[m],m.objects.count()))
        
class ImportCsvPageTest2(ImportCsvPageTest):
    fixtures = ['site.json','projects.json'] 
    #TESTFILE = 'util/fixtures/ballots-2010-10-27-1410.csv' 
    TESTFILE = ('util/fixtures/ballots-2010-11-02-1439.csv',153)
     
class ImportCsvPageTest3(ImportCsvPageTest):
    fixtures = ['site.json','projects.json'] 
    #TESTFILE = 'util/fixtures/ballots-2010-10-27-1410.csv' 
    TESTFILE = ('util/fixtures/ballots-zero-fields.csv',3) 
    NOT_IDEMPOTENT = [Ballot]
    
class MainPageTest(TestCase):
    fixtures = ['site.json']
    
    def test_get_index_view(self):
        "GET tests on front page"
        # The data is ignored, but let's check it doesn't crash the system
        # anyway.
        data = {'var': u'\xf2'}
        response = self.client.get('/', data)

        # Check some response details
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        
