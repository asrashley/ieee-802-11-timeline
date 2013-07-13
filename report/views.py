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

from util.cache import CacheControl
from report.models import MeetingReport
from util.forms import DateModelForm

from django.template import RequestContext
from django.shortcuts import render_to_response,  get_object_or_404
from django import http
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.views.generic.edit import DeleteView
from django.core.urlresolvers import reverse_lazy

from django.contrib.auth.decorators import login_required

#@login_required
class ReportDelete(DeleteView):
    model = MeetingReport
    success_url = reverse_lazy('report.views.main_page')
    

class ReportForm(DateModelForm):
    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)    

    class Meta:
        model = MeetingReport

@login_required
def main_page(request, export=None):
    context = dict(reports=MeetingReport.objects.all().order_by('-session'))
    context['export'] = export
    context['title'] = 'SUMMARY REPORTS & MINUTES OF 802.11 WG SESSIONS'
    context['next_page'] = reverse('report.views.main_page')
    context['needs_update'] = False
    context['export_page'] = 'meeting-reports' 
    context_instance=RequestContext(request)
    context_instance['cache'].export = export
    return render_to_response('report/reports.html', context, context_instance=context_instance)

@login_required
def add_report(request):
    return edit_report(request,rep=None)

@login_required
def edit_report(request,rep):
    context = {}
    context.update(csrf(request))
    next_page = request.GET.get('next',reverse('report.views.main_page'))
    if rep is None:
        report = MeetingReport()
    else:
        report = get_object_or_404(MeetingReport,pk=rep)
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(next_page)
        if request.POST.has_key('delete'):
            return http.HttpResponseRedirect(reverse('report.views.del_report',args=[rep]))
        form = ReportForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            data = form.cleaned_data
            report = form.save()
            cc = CacheControl()
            return http.HttpResponseRedirect(next_page)
    else:
        #initial={'curstat':ballot.project.status.id, 'curpk':ballot.pk} if bal is not None else {'curstat':0}
        form = ReportForm(instance=report) #, initial=initial)
    context['form'] = form
    context['object'] = report
    context['no_delete'] = rep is None
    return render_to_response('report/edit-report.html',context, context_instance=RequestContext(request))

#@login_required
#def del_report(request,rep):
#    next_page = request.GET.get('next',reverse('report.views.main_page'))
#    return create_update.delete_object(request, model=MeetingReport, object_id=rep,
#                                       post_delete_redirect=next_page)
    
