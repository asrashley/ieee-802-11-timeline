from django.conf.urls.defaults import *
#import dbindexer

#dbindexer.autodiscover()

urlpatterns = patterns('',
                       (r'^timeline/', include('timeline.urls')),
                       (r'^ballot/', include('ballot.urls')),
                       (r'^util/', include('util.urls')),
                       (r'^report/', include('report.urls')),
                       (r'^login/$', 'django.contrib.auth.views.login'),
                       (r'^logout/$', 'django.contrib.auth.views.logout'),
                       (r'^password_change/$', 'django.contrib.auth.views.password_change'),
                       (r'^password_change/done$', 'django.contrib.auth.views.password_change_done'),
                       ('^ah/$','django.views.generic.simple.redirect_to',{'url':'/_ah/admin/'}),
                       ('^$', 'util.views.index_page'),
)
