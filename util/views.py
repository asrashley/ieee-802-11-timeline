from util.cache import CacheControl
from project.models import Project
from timeline.models import DenormalizedProject, ProjectBacklog
from timeline.models import check_backlog as check_project_backlog 
from ballot.models import Ballot, DenormalizedBallot, BallotBacklog
from ballot.models import check_backlog as check_ballot_backlog 
from django.shortcuts import render_to_response

from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms,http
from util.io import import_projects_and_ballots, export_projects_and_ballots
from django.core.context_processors import csrf

import re

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
            context.update(import_projects_and_ballots(request.FILES['file']))
            cc = CacheControl()
            cc.in_progress_ver = cc.in_progress_ver+1
            cc.published_ver = cc.published_ver+1
            cc.withdrawn_ver = cc.withdrawn_ver+1
            return render_to_response('util/import-done.html', context,
                                      context_instance=RequestContext(request))
                
    else:
        form = ImportForm()
    context['form'] = form
    return render_to_response('util/import.html',context, context_instance=RequestContext(request))

@login_required
def update_page(request):
    name_re = re.compile('.+-[0-9x][0-9x][0-9x][0-9x]$')    
    update_list = ['Update completed ']
    for proj in Project.objects.all():
        changed = False
        if name_re.match(proj.name):
            proj.name = proj.name[:-5]
            changed = True
        if proj.slug is None:
            changed = True
        if changed:
            update_list.append(proj.name)
            proj.save()
        ProjectBacklog(project=proj).save()
    for ballot in Ballot.objects.all():
        BallotBacklog(ballot=ballot).save()
    check_project_backlog()
    check_ballot_backlog()
    message=' '.join(update_list)
    title='Update completed'
    return render_to_response('done.html', locals(), context_instance=RequestContext(request))