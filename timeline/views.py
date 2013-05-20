
from project.models import Project, InProgress, Published, Withdrawn
from timeline.models import DenormalizedProject, ProjectBacklog, check_backlog

from util.cache import CacheControl

from django.template import RequestContext
from django.shortcuts import render_to_response,  get_object_or_404
from django import forms,http
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.views.generic import create_update
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from django.contrib.auth.decorators import login_required

import datetime
from operator import attrgetter

class ProjectForm(forms.ModelForm):
    curstat = forms.IntegerField(widget=forms.HiddenInput)
    base = forms.ModelChoiceField(label='Baseline',queryset=Project.objects.filter(doc_type='STD'),
                                  required=False,
                                  help_text='Baseline standard. (NOTE-Amendment ordering will be automatically calculated via ordering)')
    class Meta:
        model = Project
        exclude=('baseline',)
        
@login_required
def main_page(request, export=None):
    if request.GET.get('refresh'):
        for p in Project.objects.all():
            ProjectBacklog(project=p).save()
        return http.HttpResponseRedirect(reverse('timeline.views.main_page'))
    if request.GET.get('redraw',None) is not None:
        try:
            redraw = int(request.GET.get('redraw',0))
        except ValueError:
            redraw = 0
        cc = CacheControl()
        if redraw==0:
            cc.in_progress_ver = cc.in_progress_ver+1
        elif redraw==1:
            cc.published_ver = cc.published_ver+1
        elif redraw==2:
            cc.withdrawn_ver = cc.withdrawn_ver+1
        return http.HttpResponseRedirect(reverse('timeline.views.main_page'))
    now = datetime.datetime.utcnow()
    in_process = []
    published = []
    withdrawn = []
    needs_update = check_backlog()
    for pd in DenormalizedProject.objects.all(): #order_by('-sort_key'):
        if pd.withdrawn:
            withdrawn.append(pd)
        elif pd.published:
            published.append(pd)
        else:
            in_process.append(pd)
    in_process.sort(key=attrgetter('sortkey'), reverse=True)
    published.sort(key=attrgetter('sortkey'), reverse=True)
    withdrawn.sort(key=attrgetter('sortkey'), reverse=True)
    context = dict(now=now, in_process=in_process, published=published, withdrawn=withdrawn)
    context['export'] = export
    context['cache'] = CacheControl()
    context['next_page'] = reverse('timeline.views.main_page')
    context['needs_update'] = needs_update
    return render_to_response('timeline/index.html', context, context_instance=RequestContext(request))

@login_required
def add_project(request):
    return edit_project(request,proj=None)

@login_required
def edit_project(request,proj):
    context = {}
    context.update(csrf(request))
    check_backlog()
    next_page = request.GET.get('next','/')
    if proj is None:
        project = Project()
    else:
        project = get_object_or_404(Project,pk=proj)
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(next_page)
        if request.POST.has_key('delete'):
            return http.HttpResponseRedirect(reverse('timeline.views.del_project',args=[proj])+'?next='+next_page)
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            data = form.cleaned_data
            p = form.save(commit=False)
            if data['base'] is None:
                p.baseline = None
            else:
                p.baseline = data['base'].pk
            
            p.save()
            if data['curstat']!=project.status.id:
                cc = CacheControl()
                if InProgress.id==data['curstat']:
                    cc.in_progress_ver = cc.in_progress_ver+1
                if Published.id==data['curstat']:
                    cc.published_ver = cc.published_ver+1
                if Withdrawn.id==data['curstat']:
                    cc.withdrawn_ver = cc.withdrawn_ver+1
            return http.HttpResponseRedirect(next_page)
    else:
        form = ProjectForm(instance=project, initial={'base':project.baseline,'curstat':project.status.id})
    context['form'] = form
    context['object'] = project
    return render_to_response('edit-object.html',context, context_instance=RequestContext(request))

@login_required
def del_project(request,proj):
    return create_update.delete_object(request, model=Project, object_id=proj,
                                       post_delete_redirect=request.GET.get('next','/'))


@csrf_exempt
def backlog_worker(request):
    for backlog in ProjectBacklog.objects.all():
        pd = DenormalizedProject(project=backlog.project)
        pd.denormalize()
        backlog.delete()
    message='Timeline backlog complete'
    return render_to_response('done.html',locals(),context_instance=RequestContext(request))

@receiver(post_save, sender=DenormalizedProject)
def update_cache(sender, instance, **kwargs):
    # instance is a DenormalizedProject object
    cc = CacheControl()
    if InProgress.id==instance.status.id:
        cc.in_progress_ver = cc.in_progress_ver+1
    if Published.id==instance.status.id:
        cc.published_ver = cc.published_ver+1
    if Withdrawn.id==instance.status.id:
        cc.withdrawn_ver = cc.withdrawn_ver+1

@receiver(pre_delete, sender=DenormalizedProject)
def update_cache2(sender, instance, **kwargs):
    cc = CacheControl()
    if InProgress.id==instance.status.id:
        cc.in_progress_ver = cc.in_progress_ver+1
    if Published.id==instance.status.id:
        cc.published_ver = cc.published_ver+1
    if Withdrawn.id==instance.status.id:
        cc.withdrawn_ver = cc.withdrawn_ver+1
