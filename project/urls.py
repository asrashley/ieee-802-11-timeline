from django.conf.urls import patterns

urlpatterns = patterns('project.views',
                       (r'^dn/$', 'backlog_worker'),
                       (r'^dn/status.json', 'backlog_poll'),
)