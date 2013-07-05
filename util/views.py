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

from util.models import SiteURLs

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms,http

class URLForm(forms.ModelForm):
    class Meta:
        model = SiteURLs
                
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
