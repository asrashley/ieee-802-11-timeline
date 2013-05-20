from django.conf.urls.defaults import *

urlpatterns = patterns('timeline.views',
                       (r'^edit_project/(?P<proj>\d+)$', 'edit_project'),
                       (r'^delete_project/(?P<proj>\d+)$', 'del_project'),
                       (r'^new_project/$', 'add_project'),
                       (r'^dn/$', 'backlog_worker'),
                       (r'^timeline.html$', 'main_page', {'export':'html'}),
                       (r'^timeline.shtml$', 'main_page', {'export':'shtml'}),
                       (r'^$', 'main_page'),
)