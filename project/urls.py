from django.conf.urls import patterns, url
from project.views import ProjectDelete

urlpatterns = patterns('project.views',
                       #(r'^edit_project/(?P<proj>\d+)$', 'edit_project'),
                       (r'^(?P<slug>[\w-]+)/edit$', 'edit_project'),
                       url(r'^(?P<slug>[\w-]+)/delete$', ProjectDelete.as_view(), name='del_project'),
                       #url(r'delete_project/(?P<pk>\d+)$', ProjectDelete.as_view(), name='del_project'),
                       (r'^new-project$', 'add_project'),
                       (r'^dn/$', 'backlog_worker'),
                       (r'^dn/status.json', 'backlog_poll'),
                       (r'^$', 'main_page')
)