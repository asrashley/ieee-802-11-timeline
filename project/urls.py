from django.conf.urls import patterns

urlpatterns = patterns('project.views',
                       (r'^edit_project/(?P<proj>\d+)$', 'edit_project'),
                       (r'^delete_project/(?P<proj>\d+)$', 'del_project'),
                       (r'^new_project/$', 'add_project'),
                       (r'^dn/$', 'backlog_worker'),
                       (r'^dn/status.json', 'backlog_poll'),
                       (r'^$', 'main_page')
)