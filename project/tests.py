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

from project.models import Project, DenormalizedProject
from util.tasks import run_test_task_queue 

from django.test import TestCase

import datetime

class ProjectTest(TestCase):
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
