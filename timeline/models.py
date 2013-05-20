from project.models import Project, AbstractProject
from ballot.models import DenormalizedBallot, Ballot
from util.tasks import add_task

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.urlresolvers import reverse

class ProjectProxy(object):
    def __init__(self,name,slug):
        self.name = name
        self.fullname = name
        self.slug = slug
        
class DenormalizedProject(AbstractProject):
    project = models.OneToOneField(Project, primary_key=True)
    fullname = models.CharField(max_length=30, help_text=_('Name of standard/amendment, WITH year designation'))
    sortkey = models.CharField(max_length=25, editable=False, db_index=True)
    #denormalized_baselines = models.CharField(max_length=200, blank=True, null=True, editable=False)
    denormalized_initial_wg = models.CharField(max_length=200, blank=True, null=True, editable=False)
    denormalized_recirc_wg = models.CharField(max_length=200, blank=True, null=True, editable=False)
    denormalized_initial_sb = models.CharField(max_length=200, blank=True, null=True, editable=False)
    denormalized_recirc_sb = models.CharField(max_length=200, blank=True, null=True, editable=False)
    denormalized_baselines_slug = models.CharField(max_length=16*AbstractProject.MAX_AMENDMENTS, blank=True, null=True, editable=False)
    denormalized_baselines_name = models.CharField(max_length=30*AbstractProject.MAX_AMENDMENTS, blank=True, null=True, editable=False)
    
    @property
    def baselines(self):
        if not self.denormalized_baselines_name:
            return []
        #return Project.objects.filter(pk__in=self.denormalized_baselines.split(',')).only('task_group','name')
        rv = [ProjectProxy(name,slug) for name,slug in zip(self.denormalized_baselines_name.split(','),
                                                           self.denormalized_baselines_slug.split(','))]
        return rv
      
    def denormalize(self, commit=True):
        for field in self.project._meta.fields:
            setattr(self,field.attname,getattr(self.project,field.attname))
        self.fullname = self.project.fullname
        bsl = self.project.baselines
        self.denormalized_baselines_name = ','.join([proj.fullname for proj in bsl])
        self.denormalized_baselines_slug = ','.join([proj.slug for proj in bsl])
        wi = self.project.ballot_set.filter(ballot_type='WI').order_by('draft').values_list('pk',flat=True)
        self.denormalized_initial_wg = ','.join(['%d'%pk for pk in wi])
        wr = self.project.ballot_set.filter(ballot_type='WR').order_by('draft').values_list('pk',flat=True)
        self.denormalized_recirc_wg = ','.join(['%d'%pk for pk in wr])
        si = self.project.ballot_set.filter(ballot_type='SI').order_by('draft').values_list('pk',flat=True)
        self.denormalized_initial_sb = ','.join(['%d'%pk for pk in si])
        sr = self.project.ballot_set.filter(ballot_type='SR').order_by('draft').values_list('pk',flat=True)
        self.denormalized_recirc_sb = ','.join(['%d'%pk for pk in sr])
        a = self.project.withdrawn_date.strftime('%Y%m%d') if self.project.withdrawn_date is not None else '00000000'
        b = self.project.revcom_approval_date.strftime('%Y%m%d') if self.project.revcom_approval_date is not None else '00000000'
        c = self.project.par_date.strftime('%Y%m%d')
        self.sortkey = ''.join([a,b,c])
        if commit:
            self.save()
        
    @property    
    def initial_wg_ballots(self):
        return self._get_ballots(self.denormalized_initial_wg)
    
    @property    
    def recirc_wg_ballots(self):
        return self._get_ballots(self.denormalized_recirc_wg)
    
    @property    
    def initial_sb_ballots(self):
        return self._get_ballots(self.denormalized_initial_sb)
    
    @property    
    def recirc_sb_ballots(self):
        return self._get_ballots(self.denormalized_recirc_sb)
                                 
    def _get_ballots(self,dfield):
        if not dfield:
            return []
        return list(DenormalizedBallot.objects.filter(pk__in=dfield.split(',')).only('number','draft','result','closed'))
    
    def __unicode__(self):
        return self.fullname
    
class ProjectBacklog(models.Model):
    project = models.OneToOneField(Project, primary_key=True)
    
@receiver(post_save, sender=Project)
def add_to_backlog(sender, instance, **kwargs):
    # instance is a Project object
    b = ProjectBacklog(project=instance)
    b.save()
    for dproj in DenormalizedProject.objects.filter(baseline=instance.baseline):
        if dproj.pk!=instance.pk:
            b = ProjectBacklog(project=dproj.project)
            b.save()
    check_backlog()
    
@receiver(post_save, sender=Ballot)
def post_ballot_save(sender, instance, **kwargs):
    # instance is a Ballot object
    b = ProjectBacklog(project=instance.project)
    b.save()
    check_backlog()
    
@receiver(pre_delete, sender=Ballot)
def pre_ballot_delete(sender, instance, **kwargs):
    # instance is a Ballot object
    try:
        b = ProjectBacklog(project=instance.project)
        b.save()
        check_backlog()
    except Project.DoesNotExist:
        pass
        
def check_backlog():
    needs_update = ProjectBacklog.objects.exists()
    if needs_update:
        add_task(url=reverse('timeline.views.backlog_worker'), name='timeline-backlog')
    return needs_update
