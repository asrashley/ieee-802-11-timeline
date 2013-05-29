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
from util.tasks import add_task
from project.models import Project
from ballot.models import Ballot, DenormalizedBallot

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.urlresolvers import reverse

class DenormalizedProjectBallots(models.Model):
    project_pk = models.IntegerField(primary_key=True)
    denormalized_initial_wg = models.CharField(max_length=200, blank=True, null=True, editable=False, db_index=False)
    denormalized_recirc_wg = models.CharField(max_length=200, blank=True, null=True, editable=False, db_index=False)
    denormalized_initial_sb = models.CharField(max_length=200, blank=True, null=True, editable=False, db_index=False)
    denormalized_recirc_sb = models.CharField(max_length=200, blank=True, null=True, editable=False, db_index=False)
    
    def denormalize(self, backlog, commit=True):
        project= Project.objects.get(pk=self.project_pk)
        if self.denormalized_initial_wg is None or backlog.update_initial_wg==True:
            wi = project.ballot_set.filter(ballot_type='WI').order_by('draft').values_list('pk',flat=True)
            self.denormalized_initial_wg = ','.join(['%d'%pk for pk in wi])
        if self.denormalized_recirc_wg is None or backlog.update_recirc_wg==True:
            wr = project.ballot_set.filter(ballot_type='WR').order_by('draft').values_list('pk',flat=True)
            self.denormalized_recirc_wg = ','.join(['%d'%pk for pk in wr])
        if self.denormalized_initial_sb is None or backlog.update_initial_sb==True:
            si = project.ballot_set.filter(ballot_type='SI').order_by('draft').values_list('pk',flat=True)
            self.denormalized_initial_sb = ','.join(['%d'%pk for pk in si])
        if self.denormalized_recirc_sb is None or backlog.update_recirc_sb==True:
            sr = project.ballot_set.filter(ballot_type='SR').order_by('draft').values_list('pk',flat=True)
            self.denormalized_recirc_sb = ','.join(['%d'%pk for pk in sr])
        if commit:
            self.save()
    
    @property    
    def wg_ballots(self):
        rv = self._get_ballots(self.denormalized_initial_wg)
        rv += self._get_ballots(self.denormalized_recirc_wg)
        return rv
    
    @property    
    def initial_wg_ballots(self):
        return self._get_ballots(self.denormalized_initial_wg)
    
    @property    
    def recirc_wg_ballots(self):
        return self._get_ballots(self.denormalized_recirc_wg)
    
    @property    
    def sb_ballots(self):
        return self._get_ballots(self.denormalized_initial_sb)+self._get_ballots(self.denormalized_recirc_sb)
    
    @property    
    def initial_sb_ballots(self):
        return self._get_ballots(self.denormalized_initial_sb)
    
    @property    
    def recirc_sb_ballots(self):
        return self._get_ballots(self.denormalized_recirc_sb)
                                 
    def _get_ballots(self,dfield):
        if not dfield:
            return []
        dfield = [pk for pk in dfield.split(',') if pk!='']
        return list(DenormalizedBallot.objects.filter(pk__in=dfield).only('number','draft','result','closed'))

class ProjectBallotsBacklog(models.Model):
    project_pk = models.IntegerField(primary_key=True)
    update_initial_wg = models.BooleanField(default=False)
    update_recirc_wg = models.BooleanField(default=False)
    update_initial_sb = models.BooleanField(default=False)
    update_recirc_sb = models.BooleanField(default=False)

def check_project_ballot_backlog(needs_update=False):
    if not needs_update:
        needs_update = ProjectBallotsBacklog.objects.exists()
    if needs_update:
        add_task(url=reverse('timeline.views.backlog_worker'), name='timeline-backlog')
    return needs_update

@receiver(pre_delete, sender=Ballot)
@receiver(post_save, sender=Ballot)
def post_ballot_save(sender, instance, **kwargs):
    # instance is a Ballot object
    try:
        b = ProjectBallotsBacklog.objects.get(project_pk=instance.project.pk)
    except ProjectBallotsBacklog.DoesNotExist:
        b = ProjectBallotsBacklog(project_pk=instance.project.pk)
    if instance.ballot_type==Ballot.WGInitial.code:
        b.update_initial_wg=True
    elif instance.ballot_type==Ballot.WGRecirc.code:
        b.update_recirc_wg=True
    elif instance.ballot_type==Ballot.SBInitial.code:
        b.update_initial_sb=True
    else: # or instance.ballot_type==Ballot.SBRecirc.code
        b.update_recirc_sb=True
    b.save()
    check_project_ballot_backlog(True)
