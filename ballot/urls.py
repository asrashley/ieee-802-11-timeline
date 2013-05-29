from django.conf.urls import patterns

urlpatterns = patterns('ballot.views',
                       (r'^edit_ballot/(?P<bal>\d+)$', 'edit_ballot'),
                       (r'^delete_ballot/(?P<bal>\d+)$', 'del_ballot'),
                       (r'^new_ballot/$', 'add_ballot'),
                       (r'^LetterBallots.html$', 'wg_page', {'export':'html'}),
                       (r'^LetterBallots.shtml$', 'wg_page', {'export':'shtml'}),
                       (r'^working_group/$', 'wg_page'),
                       (r'^SponsorBallots.html$', 'sponsor_page', {'export':'html'}),
                       (r'^SponsorBallots.shtml$', 'sponsor_page', {'export':'shtml'}),
                       (r'^sponsor/$', 'sponsor_page'),
                       (r'^dn/status.json', 'backlog_poll'),
                       (r'^dn/$', 'backlog_worker'),
                       (r'^$', 'main_page')
)