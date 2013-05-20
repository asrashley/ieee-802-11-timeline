
from timeline.models import *
from timeline.io import import_projects_and_ballots, export_projects_and_ballots

from django.template import RequestContext
from django.shortcuts import render_to_response,  get_object_or_404
from django import forms,http
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.views.generic import create_update

from django.contrib.auth.decorators import login_required
#
# To use Google authentication rather than Django, comment out the above line
# and uncomment the following code.
#

#from google.appengine.api import users
#def login_required(func):
#    def do_login_check(request, *args, **kwargs):
#        user = users.get_current_user()
#        if not user:
#            return http.HttpResponseRedirect(users.create_login_url(reverse('timeline.views.main_page')))
#        else:
#            setattr(user,'logout',users.create_logout_url(reverse('timeline.views.main_page')))
#            setattr(user,'is_staff',users.is_current_user_admin())
#            setattr(user,'username',users.nickname())
#        setattr(request,'user',user)
#        return func(request,*args,**kwargs)
#    return do_login_check
    

import datetime

class CacheControl(object):
    def __init__(self):
        self.timeout = 30*60*60
    
    def _get_in_progress_ver(self):
        try:
            return int(cache.get('in_progress_ver','1'))
        except ValueError:
            cache.set('published_ver',1)
            return 1
        
    def _set_in_progress_ver(self,value):
        cache.set('in_progress_ver',value)
    
    in_progress_ver = property(_get_in_progress_ver,_set_in_progress_ver)
    
    def _get_published_ver(self):
        try:
            return int(cache.get('published_ver','1'))
        except ValueError:
            cache.set('published_ver',1)
            return 1
            
    def _set_published_ver(self,value):
        cache.set('published_ver',value)
        
    published_ver = property(_get_published_ver,_set_published_ver)

    def _get_withdrawn_ver(self):
        try:
            return int(cache.get('withdrawn_ver','1'))
        except ValueError:
            cache.set('withdrawn_ver',1)
            return 1
            
    def _set_withdrawn_ver(self,value):
        cache.set('withdrawn_ver',value)
        
    withdrawn_ver = property(_get_withdrawn_ver,_set_withdrawn_ver)
    
class ImportForm(forms.Form):
    file = forms.FileField()
    wipe_projects = forms.BooleanField(required=False,help_text='Remove existing projects')
    wipe_ballots = forms.BooleanField(required=False,help_text='Remove existing ballots')

class ProjectForm(forms.ModelForm):
    curstat = forms.IntegerField(widget=forms.HiddenInput)
    base = forms.ModelChoiceField(label='Baseline',queryset=Project.objects.filter(doc_type='STD'),
                                  required=False,
                                  help_text='Baseline standard. (NOTE-Amendment ordering will be automatically calculated via ordering)')
    class Meta:
        model = Project
        exclude=('baseline',)
        
class BallotForm(forms.ModelForm):
    curstat = forms.IntegerField(widget=forms.HiddenInput)
    class Meta:
        model = Ballot
        
@login_required
def main_page(request, export=None):
    now = datetime.datetime.utcnow()
    in_process = []
    published = []
    withdrawn = []
    for s in Project.objects.all().order_by('-par_date'):
        if not s.denormalized:
            s.denormalize()
        if s.withdrawn:
            withdrawn.append(s)
        elif s.published:
            published.append(s)
        else:
            in_process.append(s)
    context = dict(now=now, in_process=in_process, published=published, withdrawn=withdrawn)
    context['export'] = export
    context['cache'] = CacheControl()
    return render_to_response('timeline/index.html', context, context_instance=RequestContext(request))

@login_required
def add_project(request):
    return edit_project(request,proj=None)

@login_required
def edit_project(request,proj):
    context = {}
    context.update(csrf(request))
    if proj is None:
        project = Project()
    else:
        project = get_object_or_404(Project,pk=proj)
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(reverse('timeline.views.main_page'))
        if request.POST.has_key('delete'):
            return http.HttpResponseRedirect(reverse('timeline.views.del_project',args=[proj]))
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            data = form.cleaned_data
            p = form.save(commit=False)
            if data['base'] is None:
                p.baseline = None
            else:
                p.baseline = data['base'].pk
            p.denormalize(commit=False)
            p.save()
            for proj in Project.objects.filter(baseline=p.baseline):
                if proj.pk!=p.pk:
                    proj.denormalize()
            cc = CacheControl()
            if InProgress.id in [data['curstat'],project.status.id]:
                cc.in_progress_ver = cc.in_progress_ver+1
            if Published.id in [data['curstat'],project.status.id]:
                cc.published_ver = cc.published_ver+1
            if Withdrawn.id in [data['curstat'],project.status.id]:
                cc.withdrawn_ver = cc.withdrawn_ver+1
            return http.HttpResponseRedirect(reverse('timeline.views.main_page'))
    else:
        form = ProjectForm(instance=project, initial={'base':project.baseline,'curstat':project.status.id})
    context['form'] = form
    context['object'] = project
    return render_to_response('timeline/edit-object.html',context, context_instance=RequestContext(request))

@login_required
def del_project(request,proj):
    project = get_object_or_404(Project,pk=proj)
    cc = CacheControl()
    if InProgress.id==project.status.id:
        cc.in_progress_ver = cc.in_progress_ver+1
    elif Published.id==project.status.id:
        cc.published_ver = cc.published_ver+1
    elif Withdrawn.id==project.status.id:
        cc.withdrawn_ver = cc.withdrawn_ver+1
    return create_update.delete_object(request, model=Project, object_id=proj,
                                       post_delete_redirect=reverse('timeline.views.main_page'))

@login_required
def add_ballot(request):
    return edit_ballot(request,bal=None)

@login_required
def edit_ballot(request,bal):
    context = {}
    context.update(csrf(request))
    if bal is None:
        ballot = Ballot()
    else:
        ballot = get_object_or_404(Ballot,pk=bal)
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(reverse('timeline.views.main_page'))
        if request.POST.has_key('delete'):
            return http.HttpResponseRedirect(reverse('timeline.views.del_ballot',args=[bal]))
        form = BallotForm(request.POST, request.FILES, instance=ballot)
        if form.is_valid():
            data = form.cleaned_data
            ballot = form.save()
            ballot.project.denormalize()
            cc = CacheControl()
            if InProgress.id in [data['curstat'],ballot.project.status.id]:
                cc.in_progress_ver = cc.in_progress_ver+1
            if Published.id in [data['curstat'],ballot.project.status.id]:
                cc.published_ver = cc.published_ver+1
            if Withdrawn.id in [data['curstat'],ballot.project.status.id]:
                cc.withdrawn_ver = cc.withdrawn_ver+1
            return http.HttpResponseRedirect(reverse('timeline.views.main_page'))
    else:
        initial={'curstat':ballot.project.status.id} if bal is not None else {'curstat':0}
        form = BallotForm(instance=ballot, initial=initial)
    context['form'] = form
    context['object'] = ballot
    return render_to_response('timeline/edit-object.html',context, context_instance=RequestContext(request))

@login_required
def del_ballot(request,bal):
    ballot = get_object_or_404(Ballot,pk=bal)
    cc = CacheControl()
    if InProgress.id==ballot.project.status.id:
        cc.in_progress_ver = cc.in_progress_ver+1
    elif Published.id==ballot.project.status.id:
        cc.published_ver = cc.published_ver+1
    elif Withdrawn.id==ballot.project.status.id:
        cc.withdrawn_ver = cc.withdrawn_ver+1
    return create_update.delete_object(request, model=Ballot, object_id=bal,
                                       post_delete_redirect=reverse('timeline.views.main_page'))

@login_required
def export_page(request):    
    return export_projects_and_ballots()

@login_required
def import_page(request):
    context = {}
    context.update(csrf(request))
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(reverse('timeline.views.main_page'))
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            if data['wipe_projects']:
                Project.objects.all().delete()
            if data['wipe_ballots']:
                Ballot.objects.all().delete()
            context.update(import_projects_and_ballots(request.FILES['file']))
            cc = CacheControl()
            cc.in_progress_ver = cc.in_progress_ver+1
            cc.published_ver = cc.published_ver+1
            cc.withdrawn_ver = cc.withdrawn_ver+1
            return render_to_response('timeline/import-done.html', context,
                                      context_instance=RequestContext(request))
                
    else:
        form = ImportForm()
    context['form'] = form
    return render_to_response('timeline/import.html',context, context_instance=RequestContext(request))

