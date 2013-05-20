from django.conf.urls.defaults import *

urlpatterns = patterns('timeline.views',
                       (r'^import/$', 'import_page'),
                       (r'^export/$', 'export_page'),
                       (r'^edit_project/(?P<proj>\d+)$', 'edit_project'),
                       (r'^delete_project/(?P<proj>\d+)$', 'del_project'),
                       (r'^new_project/$', 'add_project'),
                       (r'^edit_ballot/(?P<bal>\d+)$', 'edit_ballot'),
                       (r'^delete_ballot/(?P<bal>\d+)$', 'del_ballot'),
                       (r'^new_ballot/$', 'add_ballot'),
                       (r'^timeline.html$', 'main_page', {'export':'html'}),
                       (r'^$', 'main_page')
)