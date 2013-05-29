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

from project.models import Project, ProjectBacklog, DenormalizedProject

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@csrf_exempt
def backlog_worker(request):
    done=[]
    for backlog in ProjectBacklog.objects.all().iterator():
        done.append(backlog.pk)
        try:
            pd = DenormalizedProject(project_pk=backlog.pk)
            pd.denormalize()
            #backlog.delete()
        except (Project.DoesNotExist,TypeError):
            pass
    while done:
        batch = done[:30]
        done = done[30:]
        ProjectBacklog.objects.filter(pk__in=batch).delete()
    message='Project backlog complete'
    return render_to_response('done.html',locals(),context_instance=RequestContext(request))

@login_required
def backlog_poll(request):
    status = 'true' if ProjectBacklog.objects.exists() else 'false'
    denormalized_count = DenormalizedProject.objects.count()
    return HttpResponse(content='{"backlog":%s, "count":%d}'%(status,denormalized_count), mimetype='application/json')
