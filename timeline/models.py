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

from project.models import Project, AbstractProject, ProjectBacklog
from project.models import check_backlog as check_project_backlog 
from ballot.models import DenormalizedBallot, Ballot
from util.tasks import add_task

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.urlresolvers import reverse

    
@receiver(post_save, sender=Ballot)
def post_ballot_save(sender, instance, **kwargs):
    # instance is a Ballot object
    b = ProjectBacklog(project_pk=instance.project.pk)
    b.save()
    check_project_backlog()
    
@receiver(pre_delete, sender=Ballot)
def pre_ballot_delete(sender, instance, **kwargs):
    # instance is a Ballot object
    try:
        b = ProjectBacklog(project_pk=instance.project.pk)
        b.save()
        check_project_backlog()
    except Project.DoesNotExist:
        pass
        
