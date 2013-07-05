from django.conf.urls import patterns, include
from django.views.generic.base import RedirectView

urlpatterns = patterns('',
                       (r'^timeline/', include('timeline.urls')),
                       (r'^ballot/', include('ballot.urls')),
                       (r'^project/', include('project.urls')),
                       (r'^system/', include('system.urls')),
                       (r'^report/', include('report.urls')),
                       (r'^login/$', 'django.contrib.auth.views.login'),
                       (r'^logout/$', 'django.contrib.auth.views.logout'),
                       (r'^password_change/$', 'django.contrib.auth.views.password_change'),
                       (r'^password_change/done$', 'django.contrib.auth.views.password_change_done'),
                       ('^ah/$',RedirectView.as_view(url='/_ah/admin/')),
                       ('^$', 'system.views.index_page'),
)
