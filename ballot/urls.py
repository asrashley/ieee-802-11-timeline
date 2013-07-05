from django.conf.urls import patterns, url
from ballot.views import BallotDelete

urlpatterns = patterns('ballot.views',
                       (r'^edit_ballot/(?P<bal>\d+)$', 'edit_ballot'),
                       url(r'delete_ballot/(?P<pk>\d+)$', BallotDelete.as_view(), name='del_ballot'),
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