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

import decimal, logging, re, json

from util.io import from_isodatetime, flatten, parse_date, to_python
from util.tasks import run_test_task_queue
from util.models import SiteURLs
from util.db import bulk_delete
from util.tests import LoginBasedTest
from ballot.models import Ballot, DenormalizedBallot
from project.models import Project, DenormalizedProject
from timeline.models import DenormalizedProjectBallots
from report.models import MeetingReport
from system.views import import_page, import_progress
from system.io import project_fields

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.db.models.fields import URLField
                               
class ImportPageTest(LoginBasedTest):
    NOT_IDEMPOTENT = []

    def _post_import(self,url,filename,length=0, wipe_projects=False, wipe_ballots=False):
        testfile = open(filename,'r')
        data = {
                'wipe_projects' : wipe_projects,
                'wipe_ballots': wipe_ballots,
                'import' : 'Import',
                'file' : testfile
                }
        try:
            response = self.client.post(url, data, follow=True)
            #request = self.factory.post(url, data)
            #request.user = self.user 
            #response = import_page(request, next='/')
        except:
            raise
        finally:
            testfile.close()
        #progress_url =  response.get('Location')
        self.failUnlessEqual(response.redirect_chain[0][1],302)
        progress = response.context['progress']
        progress_url = reverse('system.views.import_progress',args=[progress.pk])
        self.failUnless(response.redirect_chain[0][0].endswith(progress_url))
        #self.failIf(response.context['errors'])
        if length:
            self.assertContains(response, 'input file contains %d line'%length)
        timeout = 3*length
        while progress.finished is None:
            timeout -= 1
            self.failIfEqual(timeout,0)
            run_test_task_queue(self.client)
            response = self.client.get(progress_url)
            #request = self.factory.get(progress_url)
            #request.user = self.user 
            #response = import_progress(request, progress.pk)
            self.failUnlessEqual(response.status_code, 200)
            progress = response.context['progress']
        done_url = reverse('system.views.import_done',args=[progress.pk])
        response = self.client.get(done_url)
        self.failUnlessEqual(response.status_code, 200)
        return response
        
class ImportHtmlBallotTest(ImportPageTest):
    fixtures = ['site.json','projects.json']
    LB_BALLOT_HTML = 'system/fixtures/LetterBallots.htm'
    SB_BALLOT_HTML = 'system/fixtures/SponsorBallots.htm'
    
    def test_ballot_import(self):
        """
        Tests import page
        """
        url = reverse('system.views.import_page',args=[])
        response = self._check_page(url)
        self.assertContains(response, '<input type="submit" name="submit"')
        
        response = self._post_import(url, self.LB_BALLOT_HTML)
        print response
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
            
        # Check that a second attempt to import the data does not cause errors 
        # and does not add any new objects to the database
        response = self._post_import(url, self.SB_BALLOT_HTML)
        for m in tmodels.keys():
            self.failUnlessEqual(m.objects.count(),counts[m],msg='%s model had %d items, but after a second import has %d'%
                                 (m._meta.verbose_name,counts[m],m.objects.count()))
            
class ImportHtmlTimelineTest(ImportPageTest):
    fixtures = ['site.json']
    LB_BALLOT_HTML = 'system/fixtures/LetterBallots.htm'
    SB_BALLOT_HTML = 'system/fixtures/SponsorBallots.htm'
    TIMELINE_HTML = 'system/fixtures/Timelines.htm'
    
    def test_timeline_import(self):
        """
        Tests import page with a timelines.html
        """
        url = reverse('system.views.import_page',args=[])
        self._check_page(url)
        response = self._post_import(url, self.TIMELINE_HTML)
        #print 'response',response
        self.assertEqual(Project.objects.count(),37)

class ImportHtmlReportTest(ImportPageTest):
    fixtures = ['site.json']
    
    def test_meeting_import(self):
        url = reverse('system.views.import_page',args=[])
        self._check_page(url)
        response = self._post_import(url, 'system/fixtures/MeetingReports.htm')
        self.assertEqual(MeetingReport.objects.count(),135+7-1)

class ImportCsvPageTest(ImportPageTest):
    fixtures = ['site.json']
    TESTFILE = ('system/fixtures/timeline-2010-11-02-1439.csv' ,187)
    MODELS = [Ballot, Project]
    
    def test_csv_import(self):
        """
        Tests import page with CSV files
        """
            
        url = reverse('system.views.import_page',args=[])
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
        tmodels = {}
        for m in self.MODELS:
            tmodels[m]=0
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
    TESTFILE = ('system/fixtures/ballots-2010-11-02-1439.csv',153)
     
class ImportCsvPageTest3(ImportCsvPageTest):
    fixtures = ['site.json','projects.json'] 
    TESTFILE = ('system/fixtures/ballots-zero-fields.csv',3) 
    NOT_IDEMPOTENT = [Ballot]
    
class ImportCsvPageTest4(ImportCsvPageTest):
    fixtures = ['site.json']
    TESTFILE = ('system/fixtures/timeline-2011-03-20-1740.csv', 384)
    MODELS = [Project, Ballot, MeetingReport]
    
    def test_cancel_import(self):
        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        testfile = open(self.TESTFILE[0],'r')
        data = {
                'wipe_projects' : False,
                'wipe_ballots': False,
                'cancel' : 'Cancel',
                'file' : testfile
                }
        url = reverse('system.views.import_page',args=[])
        try:
            response = self.client.post(url, data, follow=True)
        except:
            raise
        finally:
            testfile.close()
        try:
            progress = response.context['progress']
            raise AssertionError('Cancelling import failed')
        except KeyError:
            pass
        self.failUnlessEqual(response.redirect_chain[0][1],302)
        
class ImportCsvWipeTest(ImportPageTest):
    fixtures = ['site.json','projects.json','ballots.json','timelines.json','reports.json']
    TESTFILE = ('system/fixtures/timeline-2013-05-23-1708.csv', 452)
    MODELS = [Project, Ballot, MeetingReport]
    
    def test_wipe_import(self):
        self.assertEqual(Project.objects.count(),37)
        self.assertEqual(Ballot.objects.count(),269)
        self.assertEqual(MeetingReport.objects.count(),141)
        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        url = reverse('system.views.import_page',args=[])
        response = self._post_import(url, self.TESTFILE[0], self.TESTFILE[1], wipe_projects=True, wipe_ballots=True)
        self.assertEqual(len(response.context['projects']),Project.objects.count())
        self.assertEqual(len(response.context['ballots']),Ballot.objects.count())
        self.assertEqual(len(response.context['reports']),MeetingReport.objects.count())
        self.assertEqual(len(response.context['errors']),0)
        self.assertEqual(Project.objects.count(),37)
        self.assertEqual(Ballot.objects.count(),269)
        self.assertEqual(MeetingReport.objects.count(),141)
        
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

class UtilPagesTest(LoginBasedTest):
    fixtures = ['site.json','projects.json','ballots.json']
    
    def test_util_index(self):
        url = reverse('system.views.main_page')
        self._check_page(url)
        
    def test_update_page(self):
        url = reverse('system.views.update_page')
        bulk_delete(DenormalizedProjectBallots)
        bulk_delete(DenormalizedBallot)
        bulk_delete(DenormalizedProject)
        timeout = 2*Project.objects.count() + Ballot.objects.count()
        response = self._check_page(url)
        self.failUnlessEqual(DenormalizedProject.objects.count(),0)
        self.failUnlessEqual(DenormalizedBallot.objects.count(),0)
        self.failUnlessEqual(DenormalizedProjectBallots.objects.count(), 0)
        response.context['form']
        data = {
                'confirm': 'on',
                'yes' : "Yes, I'm sure",
                }
        response = self.client.post(url, data, follow=True)
        self.wait_for_backlog_completion([DenormalizedProject,DenormalizedBallot,DenormalizedProjectBallots], 2*timeout)
        projects={}
        for b in Ballot.objects.all():
            projects[b.project.pk]=True
        projects = projects.keys()
        self.failUnlessEqual(DenormalizedProject.objects.count(),Project.objects.count())
        self.failUnlessEqual(DenormalizedBallot.objects.count(),Ballot.objects.count())
        self.failUnlessEqual(DenormalizedProjectBallots.objects.count(), len(projects))

class JsonProxy(dict):
    def __init__(self, src):
        self.update(src)
    def group(self):
        return json.dumps(self)
    
class ExportDatabaseTest(LoginBasedTest):
    fixtures = ['site.json','projects.json', 'ballots.json', 'timelines.json', 'reports.json']
    
    def test_export(self):
        self.assertGreater(Project.objects.count(), 0)
        self.assertGreater(Ballot.objects.count(), 0)
        self.assertGreater(MeetingReport.objects.count(), 0)
        #self._check_export(ballots=False, projects=True, reports=False, format='csv')
        #self._check_export(ballots=True, projects=False, reports=False, format='csv')
        #self._check_export(ballots=False, projects=False, reports=True, format='csv')
        #self._check_export(ballots=True, projects=True, reports=True, format='csv')
        self._check_export(ballots=True, projects=True, reports=True, format='json')
        
    def _check_export(self,ballots=False, projects=False, reports=False, format='csv'):
        def find_project(proj):
            for p in response_json['projects']:
                if p['key']==proj.key:
                    return JsonProxy(p)
            return None
        def find_ballot(bal):
            for p in response_json['ballots']:
                if p['number']==bal.number:
                    return JsonProxy(p)
            return None
        def find_report(rep):
            for p in response_json['reports']:
                if p['id']==rep.id:
                    return JsonProxy(p)
            return None
        
        def check_instance(instance, name):
            for field in instance._meta.fields:
                value = getattr(instance,field.attname)
                if value and not field.primary_key:
                    if isinstance(value,(decimal.Decimal)):
                        value = float(value)
                    if format=='csv':
                        self.assertTrue(str(value) in search.group(),msg='Could not find %s.%s value %s in %s'%(name,field.attname,str(value),search.group()))
                    else:
                        jval = to_python(field,search[field.attname])
                        #print value.__class__,value,jval
                        if isinstance(value,(float)):
                            self.assertAlmostEqual(jval,value,msg='Incorrect %s.%s value %s of %s'%(name,field.attname,str(value),str(jval)))
                        else:
                            self.assertEqual(jval,value,msg='Incorrect %s.%s value %s of %s'%(name,field.attname,str(value),str(jval)))
        
        url = reverse('system.views.export_db',args=[])        
        response = self._check_page(url)
        data = {
                'format' : format,
                'submit' : 'submit'
                }
        if ballots:
            data['ballots'] = 'on'
        if projects:
            data['projects'] = 'on'
        if reports:
            data['reports'] = 'on'
        response = self.client.post(url, data) #, follow=True)
        response_str = str(response.content).replace('\r','')
        if format=='json':
            response_json = json.loads(response_str)
        for proj in Project.objects.all():
            if format=='csv':
                pattern = '^\w+,'+re.escape(proj.name)+'.+'+proj.slug+'$'
                search = re.search(pattern,response_str,re.MULTILINE)
            else:
                search = find_project(proj)
            if projects:
                self.assertNotEqual(search, None)
                #print search.group()
                check_instance(proj,'Project')
            else:
                #if search:
                #    print pattern
                #    print search.group()
                self.assertEqual(search, None)
        for ballot in Ballot.objects.all():
            if format=='csv':
                pattern = '^'+str(ballot.number)+'.+'+ballot.project.task_group+'$'
                search = re.search(pattern,response_str,re.MULTILINE)
            else:
                search = find_ballot(ballot)
            if ballots:
                self.assertNotEqual(search, None)
                check_instance(ballot,'Ballot')
            else:
                self.assertEqual(search, None)
        for report in MeetingReport.objects.all():
            if format=='csv':
                pattern = '^\w+,'+str(report.session)+'.+'+report.meeting_type+'$'
                search = re.search(pattern,response_str,re.MULTILINE)
            else:
                search = find_report(report)
            if reports:
                self.assertNotEqual(search, None)
                check_instance(report,'Report')
            else:
                self.assertEqual(search, None)
