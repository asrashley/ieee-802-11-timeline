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

from util.cache import CacheControl
from util.io import parse_projects_and_ballots
from util.models import ImportProgress
from project.models import Project
from timeline.models import DenormalizedProject, ProjectBacklog
from timeline.models import check_backlog as check_project_backlog 
from ballot.models import Ballot, DenormalizedBallot, BallotBacklog
from ballot.models import check_backlog as check_ballot_backlog 

from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms,http
from django.core.urlresolvers import reverse
from util.io import import_projects_and_ballots, export_projects_and_ballots
from django.core.context_processors import csrf

class ImportForm(forms.Form):
    file = forms.FileField()
    wipe_projects = forms.BooleanField(required=False,help_text='Remove existing projects')
    wipe_ballots = forms.BooleanField(required=False,help_text='Remove existing ballots')

def index_page(request):
    return render_to_response('home.html', {}, context_instance=RequestContext(request))

@login_required
def export_page(request):    
    return export_projects_and_ballots()

@login_required
def import_page(request, next):
    context = {}
    context.update(csrf(request))
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(next)
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            if data['wipe_projects']:
                DenormalizedProject.objects.all().delete()
                Project.objects.all().delete()
                #DenormalizedProject.objects.all().delete()
            if data['wipe_ballots']:
                DenormalizedBallot.objects.all().delete()
                Ballot.objects.all().delete()
            progress = import_projects_and_ballots(request.FILES['file'])
            return http.HttpResponseRedirect(reverse('util.views.import_progress', args=[progress.pk]))
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
    return render_to_response('util/import-done.html', locals(),
                              context_instance=RequestContext(request))
    
    
@login_required
def update_page(request):
    update_list = ['Update completed ']
    for proj in Project.objects.all():
        changed = False
        if Project.name_re.match(proj.name):
            changed = True
        if proj.slug is None:
            changed = True
        if changed:
            update_list.append(proj.name)
            proj.save()
        else:
            ProjectBacklog(project=proj).save()
    for ballot in Ballot.objects.all():
        BallotBacklog(ballot=ballot).save()
    check_project_backlog()
    check_ballot_backlog()
    message=' '.join(update_list)
    title='Update completed'
    return render_to_response('done.html', locals(), context_instance=RequestContext(request))

@csrf_exempt
def import_worker(request, prog):
    progress = get_object_or_404(ImportProgress,pk=prog)
    parse_projects_and_ballots(progress)
    message = ' '.join(['Imported<br />Projects: ', progress.projects.replace(',',', '),
                        '<br />Ballots: ',progress.ballots.replace(',',', ')])
    return render_to_response('done.html', locals(), context_instance=RequestContext(request))
