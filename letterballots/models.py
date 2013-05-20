from django.db import models
from django.utils.translation import ugettext_lazy as _

class BallotType(object):
    def __init__(self,code,descr):
        self.code = code
        self.description = descr
        
    def __str__(self):
        return '%s'%self.description
    
    def __unicode__(self):
        return self.description
    
class Ballot(models.Model):
    WGInitial = BallotType('WI', 'WG Initial')
    WGRecirc = BallotType('WR', 'WG Recirc')
    SBInitial = BallotType('SI', 'SB Initial')
    SBRecirc = BallotType('SR', 'SB Recirc')
    Procedural = BallotType('PROC', 'Procedural')

    _BALLOT_TYPES = [ (b.code,b.description) for b in WGInitial, WGRecirc, SBInitial, SBRecirc, Procedural] 
    project = models.ForeignKey(Project)
    number = models.IntegerField()
    draft = models.DecimalField(max_digits=6, decimal_places=2)
    opened = models.DateField()
    closed = models.DateField()
    ballot_type = models.CharField(max_length=5, choices=_BALLOT_TYPES)
    result = models.IntegerField(null=True, blank=True)
    pool = models.IntegerField()
    result_for = models.IntegerField(null=True, blank=True) 
    result_against = models.IntegerField(null=True, blank=True) 
    result_abstain = models.IntegerField(null=True, blank=True) 
    instructions_url = models.URLField(verify_exists=False, null=True, blank=True,
                                    help_text=_('URL pointing to ballot instruction'))
    draft_url = models.URLField(verify_exists=False, null=True, blank=True,
                                    help_text=_('URL pointing to draft document'))
    redline_url = models.URLField(verify_exists=False, null=True, blank=True,
                                    help_text=_('URL pointing to redline version of draft'))
    resolution_url = models.URLField(verify_exists=False, null=True, blank=True,
                                    help_text=_('URL pointing to comment resolutions document'))
    template_url = models.URLField(verify_exists=False, null=True, blank=True,
                                    help_text=_('URL pointing to comment submission template'))
    pool_url = models.URLField(verify_exists=False, null=True, blank=True,
                                    help_text=_('URL pointing to voter pool'))

    def __unicode__(self):
        if self.draft:
            return 'LB%03d (%s D%d)'%(self.number,self.project.task_group,self.draft)
        if self.project:
            return 'LB%03d (%s)'%(self.number,self.project.task_group)
        return 'LB%03d'%(self.number)
        