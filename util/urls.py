from django.conf.urls.defaults import *

urlpatterns = patterns('util.views',
                       url(r'^import/work/(?P<prog>\d+)$', 'import_worker' ),
                       url(r'^import/progress/(?P<prog>\d+)$', 'import_progress' ),
                       url(r'^import/done/(?P<prog>\d+)$', 'import_done' ),
                       url(r'^import/$', 'import_page', {'next':'/'}),
                       url(r'^export/$', 'export_page'),
                       url(r'^update/$', 'update_page'),
)
