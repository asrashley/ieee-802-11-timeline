from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       (r'^timeline/', include('timeline.urls')),
                       (r'^admin/', include(admin.site.urls)),
                       (r'^login/$', 'django.contrib.auth.views.login'),
                       (r'^logout/$', 'django.contrib.auth.views.logout'),
                       (r'^password_change/$', 'django.contrib.auth.views.password_change'),
                       (r'^password_change/done$', 'django.contrib.auth.views.password_change_done'),
                       ('^ah/$','django.views.generic.simple.redirect_to',{'url':'/_ah/admin/'}),
                       ('^$', 'django.views.generic.simple.direct_to_template', {'template': 'home.html'}),
)
