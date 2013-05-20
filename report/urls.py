from django.conf.urls.defaults import *

urlpatterns = patterns('report.views',
                       (r'^edit_report/(?P<rep>\d+)$', 'edit_report'),
                       (r'^delete_report/(?P<rep>\d+)$', 'del_report'),
                       (r'^new_report/$', 'add_report'),
                       (r'^meeting-reports.html$', 'main_page', {'export':'html'}),
                       (r'^meeting-reports.shtml$', 'main_page', {'export':'shtml'}),
                       (r'^$', 'main_page'),
)