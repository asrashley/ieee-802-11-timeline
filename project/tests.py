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
#  Project Name        :    IEEE 802.11 Timeline Tool                                                                            *
#
#  Author              :    Alex Ashley
#
#############################################################################

import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse

from project.models import Project, DenormalizedProject
from project.views import ProjectForm
from util.tasks import run_test_task_queue 
from util.tests import LoginBasedTest

class ProjectTest(LoginBasedTest):
    fixtures = ['site.json']
                    
    def test_add_remove_project(self):
        self.failUnlessEqual(Project.objects.count(),0)
        proj = Project(name='test',order=0, doc_type='STD', description='', task_group='TGx', par_date=datetime.datetime.now())
        proj.save()
        self.failUnlessEqual(Project.objects.count(),1)
        run_test_task_queue(self.client)
        self.failUnlessEqual(Project.objects.count(),1)
        self.failUnlessEqual(DenormalizedProject.objects.count(),1)
        dn = DenormalizedProject.objects.get(project_pk=proj.pk)
        self.failIfEqual(dn,None)
        self.failUnlessEqual(Project.objects.count(),1)
        proj.delete()
        self.failUnlessEqual(Project.objects.count(),0)
        run_test_task_queue(self.client)
        self.failUnlessEqual(DenormalizedProject.objects.count(),0)
        
    def test_add_project(self):
        self.failUnlessEqual(Project.objects.count(),0)
        url = reverse('project.views.add_project',args=[])
        response = self._check_page(url)
        TGmc = {
                "sb_formed": False,
                "ec_approved": False,
                "task_group": "TGmc",
                "recirc_wg_ballot": "2013-07-01",
                "withdrawn": False,
                "wg_approved": False,
                "par": "",
                "baseline": "",
                "initial_wg_ballot": "2013-01-01",
                "ansi_approval_date": "2015-03-01",
                "recirc_sb_ballot": "2014-07-01",
                "revcom_approval_date": "2015-03-01",
                "mec_date": "2014-02-01",
                "description": "Maintenance",
                "par_expiry": '',
                "ec_approval_date": "2014-11-01",
                "initial_sb_ballot": "2014-04-01",
                "withdrawn_date": '',
                "wg_approval_date": "2014-11-01",
                "slug": "tgmc",
                "doc_type": Project.Standard.code,
                "name": "802.11",
                "doc_format": "PDF",
                "task_group_url": "http://grouper.ieee.org/groups/802/11/Reports/tgm_update.htm",
                "doc_version": 0.70,
                "published": False,
                "par_date": "2012-07-20",
                "sb_form_date": "2014-03-01",
                "order": 0,
                "mec_completed": False,
                'curstat': response.context['form'].initial['curstat'],
                'submit':'Save'
                }
        TGak = {
                'name':'802.11ak',
                'description':'General Link',
                'doc_type':Project.Amendment.code,
                'par':'https://development.standards.ieee.org/get-file/P802.11ak.pdf?t=77398400003',
                'task_group':'TGak',
                'task_group_url':'http://grouper.ieee.org/groups/802/11/Reports/tgak_update.htm',
                'doc_format':'',
                'doc_version':0.00,
                'order':9,
                'par_date':'2012-12-05',
                'par_expiry':'2016-12-31',
                'history':'',
                'initial_wg_ballot':'',
                'recirc_wg_ballot':'',
                'sb_form_date':'',
                'initial_sb_ballot':'',
                'recirc_sb_ballot':'',
                'mec_date':'',
                'wg_approval_date':'',
                'ec_approval_date':'',
                'revcom_approval_date':'',
                'ansi_approval_date':'',
                'withdrawn_date':'',
                'base':'',
                'curstat': response.context['form'].initial['curstat'],
                'submit':'Save'
                }
        # This should fail because the data is for an amendment without a baseline
        response = self.client.post(url, TGak, follow=True)      
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(Project.objects.count(),0)
        response = self.client.post(url, TGmc, follow=True)      
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(Project.objects.count(),1)
        mc = Project.objects.all()[0]
        TGak['base'] = mc.pk
        self.assertEqual(float(mc.doc_version),TGmc['doc_version'])
        response = self.client.post(url, TGmc, follow=True)      
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(Project.objects.count(),2)
        TGak['name']='cancel test'
        TGak['task_group']='TGt'
        del TGak['submit']
        TGak['cancel'] = 'Cancel' 
        response = self.client.post(url, TGak, follow=True)      
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(Project.objects.count(),2)
        
    def test_edit_project(self):
        proj = Project(name='test',order=0, doc_type=Project.Standard.code, description='test project', task_group='TGx', par_date=datetime.datetime.now())
        proj.save()
        url = reverse('project.views.edit_project',args=[proj.pk])
        response = self._check_page(url)
        data = response.context['form'].initial
        for key in data.keys():
            if data[key] is None:
                data[key] = ''
        data['name'] = 'newname'
        data['submit']='Save'
        form = ProjectForm(data, instance=proj)
        valid = form.is_valid()
        self.failUnless(valid)
        response = self.client.post(url,data)
        self.failIf(response.status_code!=302 and response.status_code!=303)
        self.failUnlessEqual(Project.objects.count(),1)
        proj = Project.objects.get(pk=proj.pk)
        self.failUnlessEqual(proj.name,'newname')
        
    def test_delete_project(self):
        proj = Project(pk=123, name='test',order=0, doc_type=Project.Standard.code, description='', task_group='TGx', par_date=datetime.datetime.now())
        proj.save()
        login = self.client.login(username='test', password='password')
        self.failUnless(login, 'Could not log in')
        url = reverse('project.views.main_page',args=[])
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(Project.objects.count(),1)
        run_test_task_queue(self.client)
        self.failUnlessEqual(Project.objects.count(),1)
        dn = DenormalizedProject.objects.get(pk=proj.pk)
        self.failIfEqual(dn,None)
        Project.objects.filter(pk=proj.pk).delete()
        run_test_task_queue(self.client)
        self.failUnlessRaises(DenormalizedProject.DoesNotExist, DenormalizedProject.objects.get, pk=123)
