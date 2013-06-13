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

from project.models import Project, InProgress, Published, Withdrawn, \
    DenormalizedProject, ProjectBacklog, check_project_backlog
from timeline.models import ProjectBallotsBacklog, DenormalizedProjectBallots, \
    check_project_ballot_backlog 
from util.cache import CacheControl
from util.db import bulk_delete

from django.template import RequestContext
from django.shortcuts import render_to_response,  get_object_or_404
from django import forms,http
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

import datetime, sys
from operator import attrgetter

@login_required
def main_page(request, export=None):
    if request.GET.get('refresh'):
        for p in Project.objects.all().iterator():
            ProjectBacklog(project_pk=p.pk).save()
            ProjectBallotsBacklog.request_update(p.pk)
        check_project_backlog(True)
        check_project_ballot_backlog(True)
        return http.HttpResponseRedirect(reverse('timeline.views.main_page'))
    if request.GET.get('redraw',None) is not None:
        try:
            redraw = int(request.GET.get('redraw',-1))
        except ValueError:
            redraw = -1
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
    needs_update = check_project_backlog()
    for pd in DenormalizedProject.objects.all().iterator():
        try:
            pd.ballots = DenormalizedProjectBallots.objects.get(project_pk=pd.pk)
        except DenormalizedProjectBallots.DoesNotExist:
            pd.ballots = DenormalizedProjectBallots(project_pk=pd.pk)
            sys.stderr.write('Unable to find DenormalizedProjectBallots for project %d\n'%pd.pk)
            try:
                pbb = ProjectBallotsBacklog.objects.get(project_pk=pd.pk)
            except ProjectBallotsBacklog.DoesNotExist:
                pbb = ProjectBallotsBacklog(project_pk=pd.pk)
                pbb.save()
            check_project_ballot_backlog()
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
    context['next_page'] = reverse('timeline.views.main_page')
    context['needs_update'] = needs_update
    context['export_page'] = 'timeline'
    context_instance=RequestContext(request)
    context_instance['cache'].export = export
    return render_to_response('timeline/index.html', context, context_instance=context_instance)

@login_required
def backlog_poll(request):
    status = 'true' if ProjectBallotsBacklog.objects.exists() else 'false'
    denormalized_count = DenormalizedProjectBallots.objects.count()
    return HttpResponse(content='{"backlog":%s, "count":%d}'%(status,denormalized_count), mimetype='application/json')

@csrf_exempt
def backlog_worker(request):
    done=[]
    for backlog in ProjectBallotsBacklog.objects.all().iterator():
        done.append(backlog.project_pk)
        try:
            b = DenormalizedProjectBallots.objects.get(project_pk=backlog.project_pk)
        except DenormalizedProjectBallots.DoesNotExist:
            b = DenormalizedProjectBallots(project_pk=backlog.project_pk)
        try:
            b.denormalize(backlog)
        except Project.DoesNotExist:
            pass
    message='Timeline backlog complete'
    bulk_delete(ProjectBallotsBacklog, ProjectBallotsBacklog.objects.filter(pk__in=done))
    return render_to_response('done.html',locals(),context_instance=RequestContext(request))

@receiver(post_save, sender=DenormalizedProject)
@receiver(pre_delete, sender=DenormalizedProject)
def update_cache(sender, instance, **kwargs):
    # instance is a DenormalizedProject object
    cc = CacheControl()
    if InProgress.id==instance.status.id:
        cc.in_progress_ver = cc.in_progress_ver+1
    if Published.id==instance.status.id:
        cc.published_ver = cc.published_ver+1
    if Withdrawn.id==instance.status.id:
        cc.withdrawn_ver = cc.withdrawn_ver+1
        
@receiver(post_save, sender=DenormalizedProjectBallots)
@receiver(pre_delete, sender=DenormalizedProjectBallots)
def update_cache_ballots(sender, instance, **kwargs):
    # assume that any voting is on an in-progress project
    cc = CacheControl()
    cc.in_progress_ver = cc.in_progress_ver+1
