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
#  Project Name        :    IEEE 802.11 Timeline Tool
#
#  Author              :    Alex Ashley
#
#############################################################################

from ballot.models import Ballot, DenormalizedBallot
from project.models import InProgress, Published, Withdrawn
from util.cache import CacheControl
from util.forms import DateModelForm
from util.io import export_html

from django.template import RequestContext
from django.shortcuts import render_to_response,  get_object_or_404
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django import forms,http
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from util.db import bulk_delete
import sys, logging

#@login_required
class BallotDelete(DeleteView):
    model = Ballot
    success_url = reverse_lazy('ballot.views.main_page')
    
class BallotForm(DateModelForm):
    curstat = forms.IntegerField(widget=forms.HiddenInput)
    curpk  = forms.IntegerField(widget=forms.HiddenInput, required=False)
    
    def __init__(self, *args, **kwargs):
        super(BallotForm, self).__init__(*args, **kwargs)    
        ordered_fields = ['number','project','draft']
        self.fields.keyOrder = ordered_fields + [ i for i in self.fields if i not in ordered_fields ]

    class Meta:
        model = Ballot

@login_required  
@cache_page(60 * 15)      
def main_page(request):
    next_page=reverse('ballot.views.main_page')
    if request.GET.get('refresh'):
        for b in Ballot.objects.all():
            DenormalizedBallot.request_update(ballot_pk=b.number)
        return http.HttpResponseRedirect(next_page)
    needs_update = not DenormalizedBallot.backlog_poll().idle 
    return render_to_response('ballot/index.html', locals(), context_instance=RequestContext(request))
    
@login_required        
def wg_page(request, export=None):
    if request.GET.get('refresh'):
        for b in Ballot.objects.filter(ballot_type=Ballot.WGInitial.code):
            DenormalizedBallot.request_update(ballot_pk=b.number)
        for b in Ballot.objects.filter(ballot_type=Ballot.WGRecirc.code):
            DenormalizedBallot.request_update(ballot_pk=b.number)
        return http.HttpResponseRedirect(reverse('ballot.views.wg_page'))
    next_page = reverse('ballot.views.wg_page')
    if request.GET.get('redraw',None) is not None:
        try:
            redraw = int(request.GET.get('redraw',0))
        except ValueError:
            redraw = 0
        cc = CacheControl()
        if redraw==0:
            cc.open_ver = cc.open_ver + 1
        elif redraw==1:
            cc.closed_ver = cc.closed_ver + 1
        return http.HttpResponseRedirect(next_page)    
    ballots = list(DenormalizedBallot.objects.filter(ballot_type=DenormalizedBallot.WGInitial.code))+list(DenormalizedBallot.objects.filter(ballot_type=DenormalizedBallot.WGRecirc.code))+list(DenormalizedBallot.objects.filter(ballot_type=DenormalizedBallot.Procedural.code))
    return ballot_page(request,ballots,export, sponsor=False, next=next_page, export_page='LetterBallots')

@login_required
def sponsor_page(request, export=None):
    if request.GET.get('refresh'):
        for b in Ballot.objects.filter(ballot_type=Ballot.SBInitial.code):
            DenormalizedBallot.request_update(ballot_pk=b.number)
        for b in Ballot.objects.filter(ballot_type=Ballot.SBRecirc.code):
            DenormalizedBallot.request_update(ballot_pk=b.number)
        return http.HttpResponseRedirect(reverse('ballot.views.sponsor_page'))
    next_page=reverse('ballot.views.sponsor_page')
    if request.GET.get('redraw',None) is not None:
        try:
            redraw = int(request.GET.get('redraw',0))
        except ValueError:
            redraw = 0
        cc = CacheControl()
        if redraw==0:
            cc.open_ver = cc.open_ver + 1
        elif redraw==1:
            cc.closed_ver = cc.closed_ver + 1
        return http.HttpResponseRedirect(next_page)
    ballots = list(DenormalizedBallot.objects.filter(ballot_type=DenormalizedBallot.SBInitial.code))+list(DenormalizedBallot.objects.filter(ballot_type=DenormalizedBallot.SBRecirc.code))
    return ballot_page(request,ballots,export, sponsor=True, next=next_page, export_page='SponsorBallots')
    
@login_required
def add_ballot(request):
    return edit_ballot(request,bal=None)

@login_required
def edit_ballot(request,bal):
    context = {}
    context.update(csrf(request))
    next_page = request.GET.get('next','/')
    if bal is None:
        lbnum = Ballot.FIRST_SPONSOR_LBNUM
        for b in Ballot.objects.all():
            lbnum = max(lbnum,b.number+1)
        ballot = Ballot(number=lbnum)
    else:
        ballot = get_object_or_404(Ballot,pk=bal)
    if request.method == 'POST':
        if request.POST.has_key('cancel'):
            return http.HttpResponseRedirect(next_page)
        if request.POST.has_key('delete'):
            return http.HttpResponseRedirect(reverse('del_ballot',args=[bal]))
        form = BallotForm(request.POST, request.FILES, instance=ballot)
        if form.is_valid():
            data = form.cleaned_data
            ballot = form.save()
            if data['curpk'] and data['curpk']!=ballot.pk:
                try:
                    Ballot.objects.get(pk=data['curpk']).delete()
                except Ballot.DoesNotExist:
                    pass
            cc = CacheControl()
            if data['curstat'] != ballot.project.status.id:
                if InProgress.id==data['curstat']:
                    cc.in_progress_ver = cc.in_progress_ver+1
                if Published.id==data['curstat']:
                    cc.published_ver = cc.published_ver+1
                if Withdrawn.id==data['curstat']:
                    cc.withdrawn_ver = cc.withdrawn_ver+1
            return http.HttpResponseRedirect(next_page)
    else:
        initial={'curstat':ballot.project.status.id, 'curpk':ballot.pk} if bal is not None else {'curstat':0}
        form = BallotForm(instance=ballot, initial=initial)
    context['form'] = form
    context['object'] = ballot
    context['no_delete'] = bal is None
    return render_to_response('edit-object.html',context, context_instance=RequestContext(request))

#@login_required
#def del_ballot(request,bal):
#    next_page = request.GET.get('next','/')
#    return create_update.delete_object(request, model=Ballot, object_id=bal,
#                                       post_delete_redirect=next_page)

def ballot_page(request, ballots, export, sponsor, next, export_page):
    closed_ballots = []
    open_ballots = []
    needs_update = not DenormalizedBallot.backlog_poll().idle
    for b in ballots:
        if b.is_open:
            open_ballots.append(b)
        else:
            closed_ballots.append(b)
    if sponsor:
        open_ballots.sort(key=lambda x: x.closed, reverse=True)
        closed_ballots.sort(key=lambda x: x.closed, reverse=True)
    else:
        open_ballots.sort(key=lambda x: x.number, reverse=True)
        closed_ballots.sort(key=lambda x: x.number, reverse=True)
    context = dict(has_open=len(open_ballots)>0, open=open_ballots, \
                   closed=closed_ballots, next_page=next, export=export, \
                   sponsor=sponsor, needs_update=needs_update, \
                   export_page=reverse('ballot.views.main_page')+export_page)
    context_instance=RequestContext(request)
    context_instance['cache'].export = export
    if export:
        return export_html('ballot/ballots.html', context, context_instance=context_instance, filename='%s.%s'%(export_page,export))
    return render_to_response('ballot/ballots.html', context, context_instance=context_instance)

#class BallotBacklogPoll(BacklogPoll):
#    backlog = BallotBacklog
#    denormalized = DenormalizedBallot
#    check_backlog = check_ballot_backlog
    
@login_required
def backlog_poll(request):
    stats = DenormalizedBallot.backlog_poll()
    return HttpResponse(content='{"backlog":%d, "count":%d}'%(stats.waiting+stats.active,DenormalizedBallot.objects.count()), mimetype='application/json')
    #return BallotBacklogPoll().poll(request)
        
@csrf_exempt
def backlog_worker(request):
    try:
        dn = DenormalizedBallot.denormalize(ballot_pk=request.POST['ballot'], commit=True)
        return HttpResponse(content='DenormalizedBallot %s'%(dn.task_group), mimetype='text/plain')
    except DenormalizedBallot.DoesNotExist:
        return HttpResponse(content='DenormalizedBallot %s does not exist'%str(request.POST['ballot']), mimetype='text/plain')
#    done=[]
#    try:
#        for backlog in BallotBacklog.objects.all():
#            done.append(backlog.number)
#            try:
#                DenormalizedBallot.denormalize(backlog)
#            except Ballot.DoesNotExist:
#                sys.stderr.write('Unable to find ballot %d\n'%backlog.number)
#                pass
#        message='Timeline backlog complete'
#        return render_to_response('done.html',locals(),context_instance=RequestContext(request))
#    except:
#        raise
#    finally:
#        bulk_delete(BallotBacklog,BallotBacklog.objects.filter(pk__in=done))

@receiver(post_save, sender=DenormalizedBallot)
def update_cache(sender, instance, **kwargs):
    # instance is a DenormalizedBallot object
    cc = CacheControl()
    if instance.is_open:
        cc.open_ver = cc.open_ver+1
    else:
        cc.closed_ver = cc.closed_ver+1

@receiver(pre_delete, sender=DenormalizedBallot)
def update_cache2(sender, instance, **kwargs):
    cc = CacheControl()
    if instance.is_open:
        cc.open_ver = cc.open_ver+1
    else:
        cc.closed_ver = cc.closed_ver+1

