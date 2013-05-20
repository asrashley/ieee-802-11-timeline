from django.conf.urls.defaults import *

urlpatterns = patterns('util.views',
                       url(r'^import/$', 'import_page', {'next':'/'}),
                       url(r'^export/$', 'export_page'),
                       url(r'^update/$', 'update_page'),
)
