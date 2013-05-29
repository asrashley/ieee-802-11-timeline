from django.conf.urls.defaults import *
from django.contrib import admin
#import dbindexer

admin.autodiscover()

urlpatterns = patterns('util.views',
                       url(r'^import/work/(?P<prog>\d+)$', 'import_worker' ),
                       url(r'^import/progress/(?P<prog>\d+)$', 'import_progress' ),
                       url(r'^import/done/(?P<prog>\d+)$', 'import_done' ),
                       url(r'^import/$', 'import_page', {'next':'/'}),
                       url(r'^export/db$', 'export_db'),
                       url(r'^urls/$', 'edit_urls'),
                       url(r'^update/$', 'update_page'),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^^404/$', 'not_found'),
                       url(r'^$', 'main_page'),
)

#urlpatterns += patterns('',
#                       (r'^admin/', include(admin.site.urls)),
#                        )
