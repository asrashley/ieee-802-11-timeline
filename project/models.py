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

from util.tasks import add_task

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.urlresolvers import reverse

import random, re

def generate_slug(model,object,field, max_length):
    """Generates a slug that is unique within the specified model.
    """
    title = getattr(object,field)
    if title is None:
        raise Exception("Unable to find name/title of object")
    newSlug = slugify(title[:max_length])
    if object.pk is not None:
        counter=int(object.pk)
    else:
        counter=random.randint(0,99)
    while model.objects.filter(slug=newSlug).exists():
        newSlug = slugify(u"%s %d"%(title[:max_length-5],counter))
        counter += 1
    return newSlug

class Status(object):
    def __init__(self,id,str):
        self.id = id
        self._str = str
    def __unicode__(self):
        return self._str
    def __str__(self):
        return '%s'%self._str
        
class ProjectProxy(object):
    def __init__(self,name,slug):
        self.name = name
        self.fullname = name
        self.slug = slug
                
InProgress = Status(1,_('In Progress'))
Published = Status(2, _('Published'))
Withdrawn = Status(3, _('Withdrawn'))
  
class AbstractProject(models.Model):
    _PROJECT_TYPES = ( ( 'A', 'Amendment'),
                       ( 'STD', 'Standard'),
                       ( 'RP', 'Recommended Practice'),
                       ( 'COR' , 'Corrigendum') )
    MAX_AMENDMENTS = 20
    name = models.CharField(max_length=20, help_text=_('Name of standard/amendment (e.g. 802.11aa), WITHOUT year designation'))
    slug = models.SlugField(max_length=15, unique=True, editable=False, null=True, blank=True)
    description = models.CharField(max_length=100, help_text=_('Project Description'))
    doc_type = models.CharField(max_length=4, choices=_PROJECT_TYPES, help_text='Amendment, Standard, Recommended Practice or Corrigendum')
    par = models.URLField(null=False, blank=True, help_text=_('URL pointing to PAR document'))
    task_group = models.CharField(max_length=10, help_text=_('Name of task group (TG..)'))
    task_group_url = models.URLField(null=True, blank=True, help_text=_('URL pointing to TG status page'))
    doc_format = models.CharField(max_length=20, blank=True, null=True, help_text=_('Word/PDF, Frame/PDF, etc'))
    doc_version = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text=_('Version number of current draft'))
    baseline = models.IntegerField(help_text=_('Baseline standard. (NOTE-Amendment ordering will be automatically calculated via ordering)'),blank=True,null=True)
    order = models.IntegerField(help_text=_('Used to set amendment ordering, with lowest number first. For a revision standard, order must be larger than any included amendment'))
    par_date = models.DateField('PAR Approval',help_text=_('Date that PAR was first approved'))
    par_expiry = models.DateField('PAR Expiry',help_text=_('Date that PAR will expire'), blank=True, null=True)
    history = models.CharField('PAR History',max_length=60,help_text=_('Dates when PAR was renewed (Must be in the form YYYY-MM-DD, YYYY-MM-DD, ..)'), blank=True, null=True)
    initial_wg_ballot = models.DateField(help_text=_('Estimated Date of initial WG ballot'), blank=True, null=True)
    recirc_wg_ballot = models.DateField(help_text=_('Estimated Date of recirculation WG ballot'), blank=True, null=True)
    sb_form_date = models.DateField(help_text=_('Date that sponsor ballot will be formed or was formed'), blank=True, null=True)
    sb_formed = models.BooleanField(blank=True, help_text=_('Sponsor pool has been formed?'))
    initial_sb_ballot = models.DateField(help_text=_('Estimated Date of initial SB ballot'), blank=True, null=True)
    recirc_sb_ballot = models.DateField(help_text=_('Estimated Date of recirculation SB ballot'), blank=True, null=True)
    mec_date = models.DateField(help_text=_('Estimated/Actual date of mandatory editorial co-ordination'), blank=True, null=True)
    mec_completed = models.BooleanField(blank=True, help_text=_('MEC has been performed?'))
    wg_approval_date = models.DateField(blank=True, null=True, help_text=_('Estimated/Actual date of final WG approval'))
    wg_approved = models.BooleanField(blank=True, help_text=_('WG has given final approval?'))
    ec_approval_date = models.DateField(blank=True, null=True, help_text=_('Estimated/Actual date of EC approval'))
    ec_approved = models.BooleanField(blank=True, help_text=_('EC has given approval for publication?'))
    revcom_approval_date = models.DateField(blank=True, null=True, help_text=_('Estimated/Actual date of REVCOM approval'))
    published = models.BooleanField(blank=True, help_text=_('Standard/Amendment has been published?'))
    ansi_approval_date = models.DateField(blank=True, null=True)
    withdrawn_date = models.DateField(blank=True, null=True, help_text=_('Date when standard/amendment was withdrawn'))
    withdrawn = models.BooleanField(blank=True, help_text=_('Standard/Amendment has been withdrawn?'))
    
    class Meta:
        abstract = True
        
    def par_history(self):
        if self.history:
            rv = [h for h in self.history.split(',') if h!=self.par_date.strftime('%Y-%m-%d')]
            rv.sort()
            return rv
        return []
    
    @property    
    def status(self):
        if self.withdrawn:
            return Withdrawn
        if self.published:
            return Published
        return InProgress
    
class Project(AbstractProject):
    name_re = re.compile('.+-[0-9x][0-9x][0-9x][0-9x]$')
        
    def __unicode__(self):
        return self.fullname
    
    def baseline_name(self):
        if self.baseline is None:
            return ''
        try:
            return Project.objects.get(pk=self.baseline).name
        except Project.DoesNotExist:
            return ''
        
    @property
    def baselines(self):
        if self.baseline is None:
            return []
        try:
            rv = [Project.objects.get(pk=self.baseline)]
            rv += [p for p in Project.objects.filter(baseline=self.baseline).order_by('order') if p.pk!=self.pk and p.order<self.order]
            return rv
        except Project.DoesNotExist:
            return []
    
    @property    
    def initial_wg_ballots(self):
        return self.ballot_set.filter(ballot_type='WI').order_by('draft')
    
    @property    
    def recirc_wg_ballots(self):
        return self.ballot_set.filter(ballot_type='WR').order_by('draft')
    
    @property    
    def initial_sb_ballots(self):
        return self.ballot_set.filter(ballot_type='SI').order_by('draft')
    
    @property    
    def recirc_sb_ballots(self):
        return self.ballot_set.filter(ballot_type='SR').order_by('draft')

    @property
    def fullname(self):
        if self.published:
            return '%s-%04d'%(self.name,self.revcom_approval_date.year)
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(Project,self,'task_group',10)
        if self.name_re.match(self.name):
            self.name = self.name[:-5]
        super(Project,self).save(*args, **kwargs)
    
class DenormalizedProject(AbstractProject):
    from ballot.models import DenormalizedBallot
    project_pk = models.IntegerField(primary_key=True)
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
        project= Project.objects.get(pk=self.project_pk)
        for field in project._meta.fields:
            setattr(self,field.attname,getattr(project,field.attname))
        self.fullname = project.fullname
        bsl = project.baselines
        self.denormalized_baselines_name = ','.join([proj.fullname for proj in bsl])
        self.denormalized_baselines_slug = ','.join([proj.slug for proj in bsl])
        wi = project.ballot_set.filter(ballot_type='WI').order_by('draft').values_list('pk',flat=True)
        self.denormalized_initial_wg = ','.join(['%d'%pk for pk in wi])
        wr = project.ballot_set.filter(ballot_type='WR').order_by('draft').values_list('pk',flat=True)
        self.denormalized_recirc_wg = ','.join(['%d'%pk for pk in wr])
        si = project.ballot_set.filter(ballot_type='SI').order_by('draft').values_list('pk',flat=True)
        self.denormalized_initial_sb = ','.join(['%d'%pk for pk in si])
        sr = project.ballot_set.filter(ballot_type='SR').order_by('draft').values_list('pk',flat=True)
        self.denormalized_recirc_sb = ','.join(['%d'%pk for pk in sr])
        a = project.withdrawn_date.strftime('%Y%m%d') if project.withdrawn_date is not None else '00000000'
        b = project.revcom_approval_date.strftime('%Y%m%d') if project.published and project.revcom_approval_date is not None else '00000000'
        c = project.par_date.strftime('%Y%m%d')
        self.sortkey = ''.join([a,b,c])
        if commit:
            self.save()
        
    @property    
    def wg_ballots(self):
        return self._get_ballots(self.denormalized_initial_wg)+self._get_ballots(self.denormalized_recirc_wg)
    
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
        return list(self.DenormalizedBallot.objects.filter(pk__in=dfield.split(',')).only('number','draft','result','closed'))
    
    def __unicode__(self):
        return self.fullname
    
class ProjectBacklog(models.Model):
    project_pk = models.IntegerField(primary_key=True)

def check_backlog(needs_update=False):
    if not needs_update:
        needs_update = ProjectBacklog.objects.exists()
    if needs_update:
        add_task(url=reverse('project.views.backlog_worker'), name='project-backlog')
    return needs_update
    
@receiver(post_save, sender=Project)
def add_to_backlog(sender, instance, **kwargs):
    # instance is a Project object
    b = ProjectBacklog(project_pk=instance.pk)
    b.save()
    if instance.baseline is not None:
        for dproj in DenormalizedProject.objects.filter(baseline=instance.baseline).exclude(pk=instance.pk).iterator():
            b = ProjectBacklog(project_pk=dproj.project.pk)
            b.save()
    check_backlog(True)

@receiver(pre_delete, sender=Project)
def remove_project(sender, instance, **kwargs):
    if instance.baseline is not None:
        for proj in Project.objects.filter(baseline=instance.baseline).iterator():
            if proj.pk!=instance.pk:
                proj.baseline = None
                proj.save()
    ProjectBacklog.objects.filter(project_pk=instance.pk).delete()
    DenormalizedProject.objects.filter(project_pk=instance.pk).delete()
    
