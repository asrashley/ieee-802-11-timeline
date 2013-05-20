from django.db import models
from django.utils.translation import ugettext_lazy as _

class Status(object):
    def __init__(self,id,str):
        self.id = id
        self._str = str
    def __unicode__(self):
        return self._str
    def __str__(self):
        return '%s'%self._str
        
InProgress = Status(1,_('In Progress'))
Published = Status(2, _('Published'))
Withdrawn = Status(3, _('Withdrawn'))
  
class Project(models.Model):
    _PROJECT_TYPES = ( ( 'A', 'Amendment'),
                       ( 'STD', 'Standard'),
                       ( 'RP', 'Recommended Practice'),
                       ( 'COR' , 'Corrigendum') )
    name = models.CharField(max_length=30, help_text=_('Name of standard/amendment'))
    description = models.CharField(max_length=100, help_text=_('Project Description'))
    doc_type = models.CharField(max_length=4, choices=_PROJECT_TYPES)
    par = models.URLField(verify_exists=False, null=False, blank=True, 
                          help_text=_('URL pointing to PAR document'))
    task_group = models.CharField(max_length=10, help_text=_('Name of task group (TG..)'))
    task_group_url = models.URLField(verify_exists=False, null=True, blank=True,
                                    help_text=_('URL pointing to TG status page'))
    doc_format = models.CharField(max_length=20, blank=True, null=True)
    doc_version = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text=_('Version number of current draft'))
    #baselines = models.ManyToManyRel('Project')
    baseline = models.IntegerField(help_text=_('Baseline standard. (NOTE-Amendment ordering will be automatically calculated via ordering)'),blank=True,null=True)
    order = models.IntegerField(help_text=_('Used to set amendment ordering, with lowest number first. For a revision standard, order must be larger than any included amendment'))
    par_date = models.DateField('PAR Approval',help_text=_('Date that PAR was first approved'))
    par_expiry = models.DateField('PAR Expiry',help_text=_('Date that PAR will expire'), blank=True, null=True)
    history = models.CharField('PAR History',max_length=60,help_text=_('Dates when PAR was renewed (Must be in the form YYYY-MM-DD, YYYY-MM-DD, ..)'), blank=True, null=True)
    initial_wg_ballot = models.DateField(help_text=_('Estimated Date of initial WG ballot'), blank=True, null=True)
    recirc_wg_ballot = models.DateField(help_text=_('Estimated Date of recirculation WG ballot'), blank=True, null=True)
    sb_form_date = models.DateField(help_text=_('Date that sponsor ballot will be formed or was formed'), blank=True, null=True)
    sb_formed = models.BooleanField(blank=True, help_text=_('Sponsor pool has been formed'))
    initial_sb_ballot = models.DateField(help_text=_('Estimated Date of initial SB ballot'), blank=True, null=True)
    recirc_sb_ballot = models.DateField(help_text=_('Estimated Date of recirculation SB ballot'), blank=True, null=True)
    mec_date = models.DateField(help_text=_('Estimated/Actual date of mandatory editorial co-ordination'), blank=True, null=True)
    mec_completed = models.BooleanField(blank=True, help_text=_('MEC has been performed'))
    wg_approval_date = models.DateField(blank=True, null=True)
    wg_approved = models.BooleanField(blank=True)
    ec_approval_date = models.DateField(blank=True, null=True)
    ec_approved = models.BooleanField(blank=True)
    revcom_approval_date = models.DateField(blank=True, null=True)
    published = models.BooleanField(blank=True)
    ansi_approval_date = models.DateField(blank=True, null=True)
    withdrawn_date = models.DateField(blank=True, null=True)
    withdrawn = models.BooleanField(blank=True, help_text=_('Standard/Amendment has been withdrawn'))
    z_denormalized_baselines = models.CharField(max_length=200, blank=True, null=True, editable=False)
    z_denormalized_initial_wg = models.CharField(max_length=200, blank=True, null=True, editable=False)
    z_denormalized_recirc_wg = models.CharField(max_length=200, blank=True, null=True, editable=False)
    z_denormalized_initial_sb = models.CharField(max_length=200, blank=True, null=True, editable=False)
    z_denormalized_recirc_sb = models.CharField(max_length=200, blank=True, null=True, editable=False)
    
    def __unicode__(self):
        return self.name
    
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
        if self.z_denormalized_baselines is None:
            return self._calc_baselines()
        return Project.objects.filter(pk__in=self.z_denormalized_baselines.split(','))
    
    @property
    def denormalized(self):
        return self.z_denormalized_baselines is not None and self.z_denormalized_initial_wg is not None and \
            self.z_denormalized_recirc_wg is not None and self.z_denormalized_initial_sb is not None and \
            self.z_denormalized_recirc_sb is not None
    
    def denormalize(self, commit=True):
        self.z_denormalized_baselines = ','.join(['%d'%proj.pk for proj in self._calc_baselines()])
        wi = self.ballot_set.filter(ballot_type='WI').order_by('draft').values_list('pk',flat=True)
        self.z_denormalized_initial_wg = ','.join(['%d'%pk for pk in wi])
        wr = self.ballot_set.filter(ballot_type='WR').order_by('draft').values_list('pk',flat=True)
        self.z_denormalized_recirc_wg = ','.join(['%d'%pk for pk in wr])
        si = self.ballot_set.filter(ballot_type='SI').order_by('draft').values_list('pk',flat=True)
        self.z_denormalized_initial_sb = ','.join(['%d'%pk for pk in si])
        sr = self.ballot_set.filter(ballot_type='SR').order_by('draft').values_list('pk',flat=True)
        self.z_denormalized_recirc_sb = ','.join(['%d'%pk for pk in sr])
        if commit:
            self.save()
        
    def invalidate_denormalization(self, commit=True):
        self.denormalized_baselines = None
        self.z_denormalized_initial_wg_ballots = None
        if commit:
            self.save()
        
    def _calc_baselines(self):
        if self.baseline is None:
            return []
        rv = [Project.objects.get(pk=self.baseline)]
        rv += [p for p in Project.objects.filter(baseline=self.baseline).order_by('order') if p.pk!=self.pk and p.order<self.order]
        return rv
    
    @property    
    def initial_wg_ballots(self):
        return self._get_ballots(self.z_denormalized_initial_wg,'WI')
    
    @property    
    def recirc_wg_ballots(self):
        return self._get_ballots(self.z_denormalized_recirc_wg,'WR')
    
    @property    
    def initial_sb_ballots(self):
        return self._get_ballots(self.z_denormalized_initial_sb,'SI')
    
    @property    
    def recirc_sb_ballots(self):
        return self._get_ballots(self.z_denormalized_recirc_sb,'SR')
                                 
                                 
    def _get_ballots(self,dfield,type):
        if dfield is not None:
            if not dfield:
                return []
            return Ballot.objects.filter(pk__in=dfield.split(','))
        return self.ballot_set.filter(ballot_type=type).order_by('draft')
            
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
    
class Ballot(models.Model):
    _BALLOT_TYPES = ( ('WI', 'WG Initial'),
                      ('WR', 'WG Recirc'),
                      ('SI', 'SB Initial'),
                      ('SR', 'SB Recirc')
                    )
    project = models.ForeignKey(Project)
    number = models.IntegerField()
    draft = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField()
    ballot_type = models.CharField(max_length=3, choices=_BALLOT_TYPES)
    result = models.IntegerField()
    result_for = models.IntegerField(null=True, blank=True) 
    result_against = models.IntegerField(null=True, blank=True) 
    result_abstain = models.IntegerField(null=True, blank=True) 
    
    def __unicode__(self):
        if self.draft:
            return 'LB%03d (%s D%d)'%(self.number,self.project.task_group,self.draft)
        if self.project:
            return 'LB%03d (%s)'%(self.number,self.project.task_group)
        return 'LB%03d'%(self.number)
        