from django.conf.urls.defaults import *

urlpatterns = patterns('project.views',
                       (r'^dn/$', 'backlog_worker'),
)