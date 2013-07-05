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

from project.models import InProgress, Published, Withdrawn, DenormalizedProject
from timeline.models import DenormalizedProjectBallots
from util.cache import CacheControl
#from util.db import bulk_delete
#from util.backlog import BacklogPoll
#from util.tasks import poll_task_queue

from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms,http
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

import datetime, logging
from operator import attrgetter

@login_required
def main_page(request, export=None):
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
    needs_update = DenormalizedProject.backlog_poll().idle and DenormalizedProjectBallots.backlog_poll().idle
    needs_update = not needs_update
    #logging.info('needs_update %s'%str(needs_update))
    for pd in DenormalizedProject.objects.all():
        try:
            pd.ballots = DenormalizedProjectBallots.objects.get(pk=pd.pk)
        except DenormalizedProjectBallots.DoesNotExist:
            pd.ballots = DenormalizedProjectBallots(pk=pd.pk)
            #sys.stderr.write('Unable to find DenormalizedProjectBallots for project %s\n'%str(pd.pk))
            DenormalizedProjectBallots.request_update(pd)
        if pd.withdrawn:
            withdrawn.append(pd)
        elif pd.published:
            published.append(pd)
        else:
            in_process.append(pd)
    #check_project_ballot_backlog()
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

#class TimelineBacklogPoll(BacklogPoll):
#    backlog = ProjectBallotsBacklog
#    denormalized = DenormalizedProjectBallots
#    check_backlog = check_project_ballot_backlog

@login_required
def backlog_poll(request):
    stats = DenormalizedProjectBallots.backlog_poll()
    #done = 'true' if stats.idle else 'false'
    return HttpResponse(content='{"backlog":%d, "count":%d}'%(stats.waiting+stats.active,DenormalizedProject.objects.count()), mimetype='application/json')
    #return TimelineBacklogPoll().poll(request)

@csrf_exempt
def backlog_worker(request):
    try:
        dn = DenormalizedProjectBallots.denormalize(project_pk=request.POST['project'], commit=True)
        return HttpResponse(content='DenormalizedProjectBallots %s'%(dn.project_task_group), mimetype='text/plain')
    except DenormalizedProject.DoesNotExist:
        return HttpResponse(content='DenormalizedProjectBallots %s does not exist'%str(request.POST['project']), mimetype='text/plain')
    
#def old_backlog_worker(request):
#    done=[]
#    try:
#        sys.stderr.write('%s\n'%str(request.POST.backlog))
#        sys.stderr.write('bw%d '%ProjectBallotsBacklog.objects.count())
#        #sys.stderr.write('backlog_worker\n')
#        for backlog in ProjectBallotsBacklog.objects.all():
#            done.append(backlog.pk)
#            #sys.stderr.write('backlog_worker %s\n'%str(backlog.pk))
#            DenormalizedProjectBallots.denormalize(backlog)
#        #message='Timeline backlog complete'
#        return HttpResponse(content='Timeline backlog complete', mimetype='text/plain')
#        #return render_to_response('done.html',locals(),context_instance=RequestContext(request))
#    except:
#        raise
#    finally:
#        bulk_delete(ProjectBallotsBacklog, ProjectBallotsBacklog.objects.filter(pk__in=done))
#        sys.stderr.write('timeline backlog %d\n'%ProjectBallotsBacklog.objects.count())
#        #sys.stderr.write('backlog_worker done=%d\n'%ProjectBallotsBacklog.objects.count())

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
