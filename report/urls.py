from django.conf.urls import patterns, url
from report.views import ReportDelete

urlpatterns = patterns('report.views',
                       (r'^edit_report/(?P<rep>\d+)$', 'edit_report'),
                       url(r'delete_report/(?P<pk>\d+)$', ReportDelete.as_view(), name='del_report'),
                       (r'^new_report/$', 'add_report'),
                       (r'^meeting-reports.html$', 'main_page', {'export':'html'}),
                       (r'^meeting-reports.shtml$', 'main_page', {'export':'shtml'}),
                       (r'^$', 'main_page'),
)