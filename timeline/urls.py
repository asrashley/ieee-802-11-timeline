from django.conf.urls import patterns

urlpatterns = patterns('timeline.views',
                       (r'^timeline.html$', 'main_page', {'export':'html'}),
                       (r'^timeline.shtml$', 'main_page', {'export':'shtml'}),
                       (r'^dn/status.json', 'backlog_poll'),
                       (r'^dn/$', 'backlog_worker'),
                       (r'^$', 'main_page'),
)