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

from util.io import parse_projects_and_ballots
from util.db import bulk_delete
from util.models import ImportProgress, SiteURLs
from project.models import Project
from report.models import MeetingReport
from project.models import DenormalizedProject, ProjectBacklog, check_project_backlog 
from ballot.models import Ballot, DenormalizedBallot, BallotBacklog, check_ballot_backlog
from timeline.models import DenormalizedProjectBallots, ProjectBallotsBacklog, check_project_ballot_backlog

from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms,http
from django.core.urlresolvers import reverse
from util.io import import_projects_and_ballots, export_csv
from django.core.context_processors import csrf

class ImportForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs=dict(size=50)))
    wipe_projects = forms.BooleanField(required=False,help_text='Remove existing projects')
    wipe_ballots = forms.BooleanField(required=False,help_text='Remove existing ballots')
    wipe_reports = forms.BooleanField(required=False,help_text='Remove existing meeting reports')

class DebugImportForm(ImportForm):
    debug = forms.BooleanField(required=False,help_text='Debug')

class URLForm(forms.ModelForm):
    class Meta:
        model = SiteURLs
                

def index_page(request):
    return render_to_response('home.html', {}, context_instance=RequestContext(request))

def not_found(request):
    return render_to_response('404.html', {})
    
@login_required
def main_page(request):
    return render_to_response('util/index.html', {}, context_instance=RequestContext(request))
    
@login_required
def export_db(request):    
    return export_csv()
        
@login_required
def import_page(request, next):
    context = {}
    context.update(csrf(request))
    try:
        from django.conf import settings
    except ImportError:
        return ''
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(next)
        debug = False
        if settings.DEBUG:
            form = DebugImportForm(request.POST, request.FILES)
        else:
            form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            if settings.DEBUG:
                debug = data['debug']
            if data['wipe_projects']:
                #DenormalizedProject.objects.all().delete()
                #Project.objects.all().delete()
                bulk_delete(DenormalizedProjectBallots)
                bulk_delete(DenormalizedProject)
                bulk_delete(Project)
                #DenormalizedProject.objects.all().delete()
            if data['wipe_ballots']:
                bulk_delete(DenormalizedProjectBallots)
                bulk_delete(DenormalizedBallot)
                bulk_delete(Ballot)
                #DenormalizedBallot.objects.all().delete()
                #Ballot.objects.all().delete()
            if data['wipe_reports']:
                bulk_delete(MeetingReport)
            progress = import_projects_and_ballots(request.FILES['file'],debug=debug)
            return http.HttpResponseRedirect(reverse('util.views.import_progress', args=[progress.pk]))
    else:
        if settings.DEBUG:
            form = DebugImportForm()
        else:
            form = ImportForm()
    context['form'] = form
    return render_to_response('util/import.html',context, context_instance=RequestContext(request))

@login_required
def import_progress(request,prog):
    progress = get_object_or_404(ImportProgress,pk=prog)
    return render_to_response('util/import-progress.html', locals(),
                              context_instance=RequestContext(request))
    
@login_required
def import_done(request,prog):
    progress = get_object_or_404(ImportProgress,pk=prog)
    projects = Project.objects.filter(pk__in=progress.projects.split(',')) if progress.projects else []
    ballots = Ballot.objects.filter(pk__in=progress.ballots.split(',')) if progress.ballots else []
    errors = progress.errors
    reports = []
    sessions = []
    if progress.reports:
        #sessions = [ int(a) for a in progress.reports.split(',')]
        for a in progress.reports.split(','):
            try:
                sessions.append(int(a))
            except ValueError:
                pass
        for r in MeetingReport.objects.all():
            if r.session in sessions:
                reports.append(r)
    #reports = MeetingReport.objects.filter(session__in=progress.reports.split(',')) if progress.reports else []
    return render_to_response('util/import-done.html', locals(),
                              context_instance=RequestContext(request))
    
    
@login_required
def update_page(request):
    title='Updating denormalized data...'
    update_list = [title]
    for proj in Project.objects.all().iterator():
        changed = False
        if Project.name_re.match(proj.name):
            changed = True
        if proj.slug is None:
            changed = True
        if changed:
            update_list.append(proj.name)
            proj.save()
        else:
            ProjectBacklog(project_pk=proj.pk).save()
        pbb = ProjectBallotsBacklog(project_pk=proj.pk, update_initial_wg=True, update_recirc_wg=True, update_initial_sb=True, update_recirc_sb=True)
        pbb.save()
    for ballot in Ballot.objects.all().iterator():
        BallotBacklog(ballot_pk=ballot.pk).save()
    check_project_backlog()
    check_ballot_backlog()
    check_project_ballot_backlog()
    message=' '.join(update_list)
    project_count = Project.objects.count()
    ballot_count = Ballot.objects.count()
    return render_to_response('util/update.html', locals(), context_instance=RequestContext(request))

@login_required
def edit_urls(request):
    object = SiteURLs.get_urls()
    no_delete = True
    next_page = request.GET.get('next','/')
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(next_page)
        form = URLForm(request.POST, request.FILES, instance=object)
        if form.is_valid():
            form.save()
            return http.HttpResponseRedirect(next_page)
    else:
        form = URLForm(instance=object)
    title = 'Edit site URLs'
    return render_to_response('edit-object.html',locals(),context_instance=RequestContext(request))
    
@csrf_exempt
def import_worker(request, prog):
    progress = get_object_or_404(ImportProgress,pk=prog)
    parse_projects_and_ballots(progress)
    message = ' '.join(['Imported<br />Projects: ', progress.projects.replace(',',', '),
                        '<br />Ballots: ',progress.ballots.replace(',',', ')])
    return render_to_response('done.html', locals(), context_instance=RequestContext(request))
