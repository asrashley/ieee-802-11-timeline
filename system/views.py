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

import logging, decimal

from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms,http
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.conf import settings

from system.io import parse_projects_and_ballots
from util.db import bulk_delete
from util.tasks import defer_function
from util.models import SiteURLs
from system.models import ImportProgress
from system.io import import_projects_and_ballots, export_csv, export_json
from report.models import MeetingReport
from project.models import Project, DenormalizedProject
from ballot.models import Ballot, DenormalizedBallot
from timeline.models import DenormalizedProjectBallots

class ImportForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs=dict(size=50)))
    wipe_projects = forms.BooleanField(required=False,help_text='Remove existing projects')
    wipe_ballots = forms.BooleanField(required=False,help_text='Remove existing ballots')
    wipe_reports = forms.BooleanField(required=False,help_text='Remove existing meeting reports')

class ExportForm(forms.Form):
    format = forms.ChoiceField(required=True, help_text='File format', 
                               choices=[('csv','CSV file'),('json','JSON file')])
    projects = forms.BooleanField(required=False,help_text='Export projects')
    ballots = forms.BooleanField(required=False,help_text='Export ballots')
    reports = forms.BooleanField(required=False,help_text='Export meeting reports')

class DebugImportForm(ImportForm):
    debug = forms.BooleanField(required=False,help_text='Debug')

class RebuildDatabaseForm(forms.Form):
    confirm = forms.BooleanField(required=True,help_text='Yes, I really want to rebuild the database')

class URLForm(forms.ModelForm):
    class Meta:
        model = SiteURLs
                

def index_page(request):
    return render_to_response('home.html', {}, context_instance=RequestContext(request))

def not_found(request):
    return render_to_response('404.html', {})
    
@login_required
def main_page(request):
    return render_to_response('system/index.html', {}, context_instance=RequestContext(request))
    
@login_required
def export_db(request):    
    context = {}
    context.update(csrf(request))
    next_page = request.GET.get('next','/')
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(next_page)
        form = ExportForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            if data['format']=='csv':
                del data['format']
                #logging.info(str(data))
                return export_csv(**data)
            else:
                del data['format']
                return export_json(**data)
    form = ExportForm()
    return render_to_response('system/export.html', dict(form=form), context_instance=RequestContext(request))
        
@login_required
def import_page(request, next):
    context = {}
    context.update(csrf(request))
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
                data['wipe_ballots']=True
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
            return http.HttpResponseRedirect(reverse('system.views.import_progress', args=[progress.pk]))
    else:
        if settings.DEBUG:
            form = DebugImportForm()
        else:
            form = ImportForm()
    context['form'] = form
    return render_to_response('system/import.html',context, context_instance=RequestContext(request))

@login_required
def import_progress(request,prog):
    progress = get_object_or_404(ImportProgress,pk=prog)
    return render_to_response('system/import-progress.html', locals(),
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
                sessions.append(decimal.Decimal(a))
            except ValueError:
                pass
        for r in MeetingReport.objects.order_by('session'):
            if r.session in sessions:
                reports.append(r)
    #reports = MeetingReport.objects.filter(session__in=progress.reports.split(',')) if progress.reports else []
    return render_to_response('system/import-done.html', locals(),
                              context_instance=RequestContext(request))
    
    
def refresh_ballots():
    logging.debug('refresh ballots')
    for ballot in Ballot.objects.all():
        DenormalizedBallot.request_update(ballot)
            
def refresh_projects():
    logging.debug('refresh projects')
    for proj in Project.objects.all():
        changed = False
        if Project.name_re.match(proj.name):
            changed = True
        if proj.slug is None:
            changed = True
        if changed:
            proj.save()
        DenormalizedProject.request_update(project=proj)

@login_required
def update_page(request):
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(reverse('system.views.index_page'))
        form = RebuildDatabaseForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            if data['confirm']==True:    
                bulk_delete(DenormalizedProjectBallots)
                bulk_delete(DenormalizedBallot)
                bulk_delete(DenormalizedProject)
                title='Updating denormalized data...'
                project_count = Project.objects.count()
                ballot_count = Ballot.objects.count()
                defer_function(refresh_projects)
                defer_function(refresh_ballots)        
                return render_to_response('system/update.html', locals(), context_instance=RequestContext(request))
    form = RebuildDatabaseForm()
    return render_to_response('system/update_confirm.html', locals(), context_instance=RequestContext(request))

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
