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

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response,  get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django import forms, http
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_page
from django.views.generic.edit import DeleteView
from django.core.urlresolvers import reverse_lazy

from project.models import InProgress, Published, Withdrawn, Project, DenormalizedProject
from util.forms import DateModelForm
from util.cache import CacheControl
#from util.backlog import BacklogPoll
#from util.db import bulk_delete

#@login_required
class ProjectDelete(DeleteView):
    model = Project
    success_url = reverse_lazy('project.views.main_page')
    

class ProjectForm(DateModelForm):
    curstat = forms.IntegerField(widget=forms.HiddenInput)
    base = forms.ModelChoiceField(label='Baseline',queryset=Project.objects.filter(doc_type='STD'),
                                  required=False,
                                  help_text='Baseline standard. (NOTE-Amendment ordering will be automatically calculated via ordering)')
            
    class Meta:
        model = Project
        exclude=('baseline',)

    def clean(self):
        cleaned_data = super(DateModelForm,self).clean()
        doc_type = cleaned_data.get("doc_type")
        baseline = cleaned_data.get("base")
        if doc_type==Project.Amendment.code and not baseline:
            msg = u"An amendment must have a baseline standard."
            self._errors["base"] = self.error_class([msg])
            self._errors["doc_type"] = self.error_class([msg])
            del cleaned_data['base']
            del cleaned_data['doc_type']
            #raise forms.ValidationError(msg)
        return cleaned_data


@login_required  
@cache_page(60 * 15)      
def main_page(request):
    next_page=reverse('project.views.main_page')
    if request.GET.get('refresh'):
        for b in Project.objects.all():
            DenormalizedProject.request_update(project=b)
        return http.HttpResponseRedirect(next_page)
    needs_update = not DenormalizedProject.backlog_poll().idle 
    projects = Project.objects.all().order_by('-par_date')
    return render_to_response('project/index.html', locals(), context_instance=RequestContext(request))

@login_required
def add_project(request):
    return edit_project(request,slug=None)

@login_required
def edit_project(request,slug):
    context = {}
    context.update(csrf(request))
    next_page = request.GET.get('next',reverse_lazy('project.views.main_page'))
    if slug is None:
        project = Project()
    else:
        project = get_object_or_404(Project,slug=slug)
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(next_page)
        if request.POST.has_key('delete'):
            return http.HttpResponseRedirect(reverse('del_project',args=[slug])+'?next='+str(next_page))
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
    return render_to_response('project/edit_project.html',context, context_instance=RequestContext(request))

#@login_required
#def del_project(request,proj):
#    return create_update.delete_object(request, model=Project, object_id=proj,
#                                       post_delete_redirect=request.GET.get('next','/'))

@csrf_exempt
def backlog_worker(request):
    try:
        dn = DenormalizedProject.denormalize(project_pk=request.POST['project'], commit=True)
        return HttpResponse(content='DenormalizedProject %s'%(dn.task_group), mimetype='text/plain')
    except DenormalizedProject.DoesNotExist:
        return HttpResponse(content='DenormalizedProject %s does not exist'%str(request.POST['project']), mimetype='text/plain')
#    done=[]
#    try:
#        for backlog in ProjectBacklog.objects.all():
#            done.append(backlog.pk)
#            try:
#                #try:
#                #    pd = DenormalizedProject.objects.get(project_pk=long(backlog.pk))
#                #except DenormalizedProject.DoesNotExist:
#                proj = Project.objects.get(pk=backlog.pk)
#                DenormalizedProject.denormalize(proj)
#                #backlog.delete()
#            except (Project.DoesNotExist,TypeError):
#                print 'Unable to find project ',backlog.pk
#                pass
#        #message='Project backlog complete'
#        return HttpResponse(content='Project backlog complete', mimetype='text/plain')
#        #return render_to_response('done.html',locals(),context_instance=RequestContext(request))
#    except:
#        raise
#    finally:
#        bulk_delete(ProjectBacklog, ProjectBacklog.objects.filter(pk__in=done))
#        #ProjectBacklog.objects.filter(pk__in=batch).delete()
        

#class ProjectBacklogPoll(BacklogPoll):
#    backlog = ProjectBacklog
#    denormalized = DenormalizedProject
#    check_backlog = check_project_backlog
    
@login_required
def backlog_poll(request):
    stats = DenormalizedProject.backlog_poll()
    #done = 'true' if stats.idle else 'false'
    return HttpResponse(content='{"backlog":%d, "count":%d}'%(stats.waiting+stats.active,DenormalizedProject.objects.count()), mimetype='application/json')
