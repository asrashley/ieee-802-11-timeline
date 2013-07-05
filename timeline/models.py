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
from util.tasks import add_task, poll_task_queue
#from util.io import flatten_model
from project.models import Project
from ballot.models import Ballot, DenormalizedBallot

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.urlresolvers import reverse

import datetime, json, logging

class BallotProxy(object):
    def __init__(self,data):
        self.pk = self.number = long(data['number'])
        self.draft = float(data['draft'])
        self.result = int(data['result'])
        self.closed = datetime.date.fromordinal(data['closed'])
         
    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return u'{"pk":%d,"draft":%f,"result":%d,"closed":"%s"}'%(self.pk,self.draft,self.result,self.closed.isoformat())
    
    def __repr__(self):
        return u'BallotProxy(%d,%f,%d,"%s")'%(self.pk,self.draft,self.result,self.closed.isoformat())
        
class DenormalizedProjectBallots(models.Model):
    QUEUE_NAME='timeline-backlog'
    project_key = models.AutoField(primary_key=True)
    #project_pk = models.CharField(primary_key=True, blank=False, null=False, max_length=255)
    #project_pk = models.IntegerField(primary_key=True)
    #project = models.ForeignKey(DenormalizedProject, primary_key=True)
    project_task_group = models.CharField(max_length=20)
    denormalized_initial_wg = models.TextField(blank=True, null=True, editable=False, db_index=False)
    denormalized_recirc_wg = models.TextField(blank=True, null=True, editable=False, db_index=False)
    denormalized_initial_sb = models.TextField(blank=True, null=True, editable=False, db_index=False)
    denormalized_recirc_sb = models.TextField(blank=True, null=True, editable=False, db_index=False)
    
    @classmethod
    def denormalize(clz, project_pk=None, project=None, commit=True):
        if project is None and project_pk is not None:
            project = Project.objects.get(pk=project_pk)
        if project is None:
            raise ValueError('denormalize with no project')
        #logging.info('denormalize timeline %s'%project.name)
        try:
            dn = DenormalizedProjectBallots.objects.get(pk=project.pk)
        except DenormalizedProjectBallots.DoesNotExist:
            dn = DenormalizedProjectBallots(pk=project.pk)
        dn.project_key = project.key
        dn.project_task_group = project.task_group
        #if dn.denormalized_initial_wg is None or backlog.update_initial_wg==True:
        dn.denormalized_initial_wg = clz._denormalize_ballot(project, Ballot.WGInitial)
        #if dn.denormalized_recirc_wg is None or backlog.update_recirc_wg==True:
        dn.denormalized_recirc_wg = clz._denormalize_ballot(project, Ballot.WGRecirc)
        #if dn.denormalized_initial_sb is None or backlog.update_initial_sb==True:
        dn.denormalized_initial_sb = clz._denormalize_ballot(project, Ballot.SBInitial)
        #if dn.denormalized_recirc_sb is None or backlog.update_recirc_sb==True:
        dn.denormalized_recirc_sb= clz._denormalize_ballot(project, Ballot.SBRecirc)
        if commit:
            dn.save()
        return dn
    
    @classmethod    
    def request_update(clz,project=None, project_pk=None,ballot_type=None):
        if project is not None:
            project_pk = project.pk
        if project_pk is None:
            raise ValueError('request_update with no project')
        #payload = flatten_model(project)
        #print 'ru',project.task_group,
        add_task(url=reverse('timeline.views.backlog_worker'),
                 name = 'timeline'+str(project_pk), 
                 queue_name=clz.QUEUE_NAME,
                 params={'project':project_pk},
                 countdown=2)        
        #try:
        #    pbb = ProjectBallotsBacklog.objects.get(project=project)
        #except ProjectBallotsBacklog.DoesNotExist:
        #    pbb = ProjectBallotsBacklog(project=project)
        #if ballot_type==Ballot.WGInitial or ballot_type==Ballot.WGInitial.code:
        #    pbb.update_initial_wg=True
        #elif ballot_type==Ballot.WGRecirc or ballot_type==Ballot.WGRecirc.code:
        #    pbb.update_recirc_wg=True
        #elif ballot_type==Ballot.SBInitial or ballot_type==Ballot.SBInitial.code:
        #    pbb.update_initial_sb=True
        #elif ballot_type==Ballot.SBRecirc or ballot_type==Ballot.SBRecirc.code:
        #    pbb.update_recirc_sb=True
        #pbb.save()
        #sys.stderr.write('%s,%d '%(project.task_group,ProjectBallotsBacklog.objects.count()))

    @classmethod
    def backlog_poll(clz):
        rv= poll_task_queue(clz.QUEUE_NAME)
        #logging.info(str(rv))
        return rv

    @classmethod    
    def _denormalize_ballot(clz,project,ballot_type):
        wi=[]
        for ballot in Ballot.objects.filter(project=project).filter(ballot_type=ballot_type.code).order_by('draft'): #.only('number','draft','vote_for','vote_against','closed')
            wi.append({ 'number':ballot.number, 'draft':str(ballot.draft), 'result':ballot.result, 'closed':ballot.closed.toordinal()})
        #if project.task_group=='TGmb':
        #    print 'dn',project.task_group,ballot_type,wi
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
    
    def __unicode__(self):
        rv = [self.project_task_group, str(self.initial_wg_ballots), str(self.recirc_wg_ballots), str(self.initial_sb_ballots), str(self.recirc_sb_ballots)]
        return '\n'.join(rv)
    
    def _get_ballots(self,ballot_type, dfield):
        if not dfield:
            return []
        try:
            return [BallotProxy(i) for i in json.loads(dfield)]
        except ValueError:
            DenormalizedProjectBallots.request_update(self.project_pk, ballot_type)
            return []
        


#class ProjectBallotsBacklog(models.Model):
#    #project_pk = models.CharField(blank=False, null=False, max_length=128)
#    project = models.ForeignKey(DenormalizedProject)
#    #project_pk = models.IntegerField(primary_key=True)
#    update_initial_wg = models.BooleanField(default=False)
#    update_recirc_wg = models.BooleanField(default=False)
#    update_initial_sb = models.BooleanField(default=False)
#    update_recirc_sb = models.BooleanField(default=False)

#def check_project_ballot_backlog(needs_update=False):
#    if not needs_update:
#        needs_update = ProjectBallotsBacklog.objects.exists()
#    if needs_update:
#        sys.stderr.write('bw%d '%ProjectBallotsBacklog.objects.count())
#        add_task(url=reverse('timeline.views.backlog_worker'), name='timeline-backlog', \
#                 params={'backlog':str(ProjectBallotsBacklog.objects.values_list('pk',flat=True))})
#    return needs_update


@receiver(pre_delete, sender=DenormalizedBallot)
@receiver(post_save, sender=DenormalizedBallot)
def post_ballot_save(sender, instance, **kwargs):
    # instance is a Ballot object
    if kwargs.get('raw',False):
        #don't create a backlog when loading a fixture in a unit test
        return
    try:
        project = Project.objects.get(pk=instance.project_pk)
        DenormalizedProjectBallots.request_update(project=project, ballot_type=instance.ballot_type)
        #check_project_ballot_backlog(True)
    except Project.DoesNotExist:
        pass
