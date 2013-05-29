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

from project.models import Project
from util.tasks import add_task

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.urlresolvers import reverse

import datetime

class BallotType(object):
    def __init__(self,code,descr):
        self.code = code
        self.description = descr
        
    def __str__(self):
        return '%s'%self.description
    
    def __unicode__(self):
        return self.description
    
class AbstractBallot(models.Model):
    WGInitial = BallotType('WI', 'WG Initial')
    WGRecirc = BallotType('WR', 'WG Recirc')
    SBInitial = BallotType('SI', 'SB Initial')
    SBRecirc = BallotType('SR', 'SB Recirc')
    Procedural = BallotType('PROC', 'Procedural')

    _BALLOT_TYPES = [ (b.code,b.description) for b in WGInitial, WGRecirc, SBInitial, SBRecirc, Procedural] 
    number = models.IntegerField(primary_key=True, help_text=_('Number of this ballot. For sponsor ballots, you need to invent a number'))
    draft = models.DecimalField(max_digits=6, decimal_places=2, help_text=_('The version number of the balloted draft'))
    opened = models.DateField(help_text=_('Date that ballot opened'))
    closed = models.DateField(help_text=_('Date that ballot closed'))
    ballot_type = models.CharField(max_length=5, choices=_BALLOT_TYPES, help_text=_('Initial, recirc, procedural, etc'))
    #result = models.IntegerField(null=True, blank=True)
    pool = models.IntegerField(help_text=_('Number of voters in ballot pool'), null=True)
    vote_for = models.IntegerField(null=True, blank=True) 
    vote_against = models.IntegerField(null=True, blank=True) 
    vote_abstain = models.IntegerField(null=True, blank=True) 
    vote_invalid = models.IntegerField(null=True, blank=True, help_text=_('Number of NO votes without comments')) 
    comments = models.IntegerField(null=True, blank=True, help_text=_('Number of comments')) 
    instructions_url = models.URLField(null=True, blank=True,
                                    help_text=_('URL pointing to ballot instruction'))
    draft_url = models.URLField(null=True, blank=True,
                                    help_text=_('URL pointing to draft document'))
    redline_url = models.URLField(null=True, blank=True,
                                    help_text=_('URL pointing to redline version of draft'))
    resolution_url = models.URLField(null=True, blank=True,
                                    help_text=_('URL pointing to comment resolutions document'))
    template_url = models.URLField(null=True, blank=True,
                                    help_text=_('URL pointing to comment submission template'))
    pool_url = models.URLField(null=True, blank=True,
                                    help_text=_('URL pointing to voter pool'))

    class Meta:
        abstract = True
        
    def description(self):
        if self.ballot_type == self.WGRecirc.code or self.ballot_type == self.SBRecirc.code:
            return _('Recirculation')
        elif self.ballot_type == self.Procedural.code:
            return _('Procedural')
        return _('Technical')
    
    @property
    def return_percent(self):
        if self.pool:
            return int((100*float(self.return_count) / float(self.pool))+0.5)
        return 0
    
    @property
    def return_count(self):
        votes = self.vote_for if self.vote_for is not None else 0
        votes += self.vote_abstain if self.vote_abstain is not None else 0
        votes += self.vote_against if self.vote_against is not None else 0
        return votes
    
    @property
    def abstain_percent(self):
        if self.vote_abstain is None:
            return 0
        votes = self.return_count
        if votes>0:
            return int((100*float(self.vote_abstain) / float(votes))+0.5)
        return 0
    
    @property
    def against_percent(self):
        if self.vote_against is None:
            return 0
        votes = self.return_count
        if votes>0:
            return int((100*float(self.vote_against) / float(votes))+0.5)
        return 0
        
    @property
    def days(self):
        return (self.closed - self.opened).days
    
    @property
    def is_open(self):
        now = datetime.datetime.now()
        return now.toordinal()<=self.closed.toordinal()

    @property    
    def is_wg_ballot(self):
        return self.ballot_type==self.WGInitial.code or self.ballot_type==self.WGRecirc.code

    @property    
    def is_initial_ballot(self):
        return self.ballot_type==self.WGInitial.code or self.ballot_type==self.SBInitial.code
        
    
class Ballot(AbstractBallot):
    FIRST_SPONSOR_LBNUM = 10000
    
    project = models.ForeignKey(Project, help_text=_('The project that produced the balloted document'))
    
    def project_name(self):
        return self.project.name
    
    def __unicode__(self):
        if self.draft and self.project:
            return 'LB%03d (%s D%s)'%(self.number,self.project.task_group,self.draft)
        if self.project:
            return 'LB%03d (%s)'%(self.number,self.project.task_group)
        return 'LB%03d'%int(self.number)

    @property
    def result(self):
        f = self.vote_for if self.vote_for is not None else 0
        a = self.vote_against if self.vote_against is not None else 0
        v = f+a
        if v>0:
            return int(100*(float(f)/v)+0.5)
        return 0
    
        
class DenormalizedBallot(AbstractBallot):
    #ballot = models.OneToOneField(Ballot, primary_key=True)
    #ballot_pk = models.IntegerField(primary_key=True)
    result = models.IntegerField(null=True, blank=True)
    project_pk = models.IntegerField()
    project_name = models.CharField(max_length=30, help_text=_('Name of standard/amendment'))
    task_group = models.CharField(max_length=10, help_text=_('Name of task group (TG..)'))
    
    def denormalize(self, commit=True):
        ballot = Ballot.objects.get(pk=self.number)
        for field in ballot._meta.fields:
            if field.attname!='project' and field.attname!='project_id':
                setattr(self,field.attname,getattr(ballot,field.attname))
        #try:
        self.project_pk = ballot.project.pk
        self.project_name = ballot.project.fullname
        self.task_group = ballot.project.task_group
        #except Project.DoesNotExist:
        #    print 'Invalid project ',ballot.project_id
        if self.project_name.endswith('-xxxx'):
            self.project_name = self.project_name[:-5]
        self.result = ballot.result if self.vote_for is not None else None
        if commit:
            self.save()
    
    def __unicode__(self):
        return 'LB%03d'%int(self.number)
    
class BallotBacklog(models.Model):
    #ballot = models.OneToOneField(Ballot, primary_key=True)
    ballot_pk = models.IntegerField(primary_key=True)

    #def __getattribute__(self, *args, **kwargs):
    #    if args and args[0]=='ballot':
    #        return Ballot.objects.get(pk=self.ballot_pk)
    #    return models.Model.__getattribute__(self, *args, **kwargs)
    
    #def __setattr__(self, *args, **kwargs):
    #    if args and len(args)>1 and args[0]=='ballot':
    #        self.ballot_pk= args[1].pk
    #        return args[1]
    #    return models.Model.__setattr__(self, *args, **kwargs)
    
def check_backlog(force=False):
    needs_update = force
    if not force:
        needs_update = BallotBacklog.objects.exists()
    if needs_update:
        add_task(name = 'ballot-backlog', url=reverse('ballot.views.backlog_worker'))
    return needs_update
    
@receiver(post_save, sender=Ballot)
def add_to_backlog(sender, instance, **kwargs):
    b = BallotBacklog(ballot_pk=instance.pk)
    b.save()
    check_backlog(True)
    
@receiver(pre_delete, sender=Ballot)
def remove_ballot(sender, instance, **kwargs):
    BallotBacklog.objects.filter(ballot_pk=instance.pk).delete()
    DenormalizedBallot.objects.filter(pk=instance.pk).delete()
    
