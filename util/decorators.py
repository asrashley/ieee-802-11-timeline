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

