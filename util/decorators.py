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

#
# To use Google authentication rather than Django, use the following code rather than the
# Django login_required decorator
#
from django import http
from django.core.urlresolvers import reverse

from google.appengine.api import users
def login_required(func):
    def do_login_check(request, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            return http.HttpResponseRedirect(users.create_login_url(reverse('timeline.views.main_page')))
        else:
            setattr(user,'logout',users.create_logout_url(reverse('timeline.views.main_page')))
            setattr(user,'is_staff',users.is_current_user_admin())
            setattr(user,'username',users.nickname())
        setattr(request,'user',user)
        return func(request,*args,**kwargs)
    return do_login_check

