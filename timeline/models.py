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

import datetime, json

class BallotProxy(object):
    def __init__(self,data):
        self.pk = self.number = data['number']
        self.draft = data['draft']
        self.result = data['result']
        self.closed = datetime.date.fromordinal(data['closed']) 
        
class DenormalizedProjectBallots(models.Model):
    project_pk = models.IntegerField(primary_key=True)
    denormalized_initial_wg = models.TextField(blank=True, null=True, editable=False, db_index=False)
    denormalized_recirc_wg = models.TextField(blank=True, null=True, editable=False, db_index=False)
    denormalized_initial_sb = models.TextField(blank=True, null=True, editable=False, db_index=False)
    denormalized_recirc_sb = models.TextField(blank=True, null=True, editable=False, db_index=False)
    
    def denormalize(self, backlog, commit=True):
        project= Project.objects.get(pk=self.project_pk)
        if self.denormalized_initial_wg is None or backlog.update_initial_wg==True:
            self.denormalized_initial_wg = self._denormalize_ballot(project, Ballot.WGInitial)
        if self.denormalized_recirc_wg is None or backlog.update_recirc_wg==True:
            self.denormalized_recirc_wg = self._denormalize_ballot(project, Ballot.WGRecirc)
        if self.denormalized_initial_sb is None or backlog.update_initial_sb==True:
            self.denormalized_initial_sb = self._denormalize_ballot(project, Ballot.SBInitial)
        if self.denormalized_recirc_sb is None or backlog.update_recirc_sb==True:
            self.denormalized_recirc_sb= self._denormalize_ballot(project, Ballot.SBRecirc)
        if commit:
            self.save()
    
    def _denormalize_ballot(self,project,ballot_type):
        wi=[]
        for ballot in project.ballot_set.filter(ballot_type=ballot_type.code).order_by('draft'): #.only('number','draft','vote_for','vote_against','closed')
            wi.append({ 'number':ballot.number, 'draft':str(ballot.draft), 'result':ballot.result, 'closed':ballot.closed.toordinal()})
        return json.dumps(wi)
        
    @property    
    def wg_ballots(self):
        rv = self._get_ballots(Ballot.WGInitial,self.denormalized_initial_wg)
        rv += self._get_ballots(Ballot.WGRecirc,self.denormalized_recirc_wg)
        return rv
    
    @property    
    def initial_wg_ballots(self):
        return self._get_ballots(Ballot.WGInitial,self.denormalized_initial_wg)
    
    @property    
    def recirc_wg_ballots(self):
        return self._get_ballots(Ballot.WGRecirc,self.denormalized_recirc_wg)
    
    @property    
    def sb_ballots(self):
        return self._get_ballots(Ballot.SBInitial,self.denormalized_initial_sb)+self._get_ballots(Ballot.SBRecirc,self.denormalized_recirc_sb)
    
    @property    
    def initial_sb_ballots(self):
        return self._get_ballots(Ballot.SBInitial,self.denormalized_initial_sb)
    
    @property    
    def recirc_sb_ballots(self):
        return self._get_ballots(Ballot.SBRecirc,self.denormalized_recirc_sb)
                                 
    def _get_ballots(self,ballot_type, dfield):
        if not dfield:
            return []
        try:
            return [BallotProxy(i) for i in json.loads(dfield)]
        except ValueError:
            try:
                pbb = ProjectBallotsBacklog.objects.get(project_pk=self.project_pk)
            except ProjectBallotsBacklog.DoesNotExist:
                pbb = ProjectBallotsBacklog(project_pk=self.project_pk)
            if ballot_type==Ballot.WGInitial:
                pbb.update_initial_wg=True
            elif ballot_type==Ballot.WGRecirc:
                pbb.update_recirc_wg=True
            elif ballot_type==Ballot.SBInitial:
                pbb.update_initial_sb=True
            else:
                pbb.update_recirc_sb=True
            pbb.save()
            return []

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
