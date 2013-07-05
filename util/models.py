#############################################################################
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#############################################################################
#
#  Project Name        :    IEEE 802.11 Timeline Tool#                                                                            *
#
#  Author              :    Alex Ashley
#
#############################################################################

from django.db import models
#from django.core.cache import cache
from django.utils.translation import ugettext

import re #, traceback, sys

email_re = re.compile(r'(?P<name>[\w ]+)\s+<(?P<address>[\w._-]+@[\w.-_]+)>')
            
class SiteURLs(models.Model):
    timeline_history = models.URLField('Historical Timeline',  default='https://mentor.ieee.org/802.11/dcn/07/11-07-1952-19-0000-non-procedural-letter-ballot-results.xls')
    wg_meeting_plan = models.URLField('WG Meeting Plan',  default='http://grouper.ieee.org/groups/802/11/Meetings/Meeting_Plan.html')   
    ec_meeting_plan = models.URLField('EC Meeting Plan',  default='http://grouper.ieee.org/groups/802/11/Meetings/Meeting_Plan.html')   
    ieee_sa_calendar = models.URLField('Current IEEE-SA Calendar',  default='http://standards.ieee.org/board/index.html')
    wg_letter_ballots = models.URLField('WG Letter Ballots',  default='http://grouper.ieee.org/groups/802/11/LetterBallots.shtml')
    sponsor_ballots = models.URLField('IEEE-SA Sponsor Ballots',  default='http://grouper.ieee.org/groups/802/11/SponsorBallots.html')
    old_wg_ballots = models.URLField('Letter ballot results up to LB100',  default='http://www.ieee802.org/11/LetterBallots0to100.shtml')
    copyright = models.URLField( default='http://www.ieee.org/about/documentation/copyright/')
    staff_email = models.URLField('E-mail IEEE Staff',  default='http://standards.ieee.org/cgi-bin/staffmail')
    search = models.URLField( default='http://standards.ieee.org/search.html')
    standards = models.URLField('IEEE Standards Home Page',  default='http://standards.ieee.org/index.html')
    ieee_home_page = models.URLField('IEEE Corporate Home Page',  default='http://www.ieee.org/')
    lb_ballot_maintainers = models.CharField('Letter ballot page maintainers', max_length=200, default='Adrian Stephens <adrian.p.stephens@intel.com>',
                                             help_text='Enter email addresses as Name <email@domain> separated by commas')
    sb_ballot_maintainers = models.CharField('Sponsor ballot page maintainers', max_length=200,default='Adrian Stephens <adrian.p.stephens@intel.com>',
                                             help_text='Enter email addresses as Name <email@domain> separated by commas')
    timeline_maintainers = models.CharField('Timeline page maintainers', max_length=200, default='Stephen McCann <stephen.mccann@ieee.org>, Alex Ashley <aashley@nds.com>',
                                            help_text='Enter email addresses as Name <email@domain> separated by commas')
    example_agenda = models.CharField('Example Plenary and Interim Session Agenda', max_length=200, default='http://grouper.ieee.org/groups/802/11/Meetings/Typical_Meeting_Agenda.htm')
    last_modified = models.DateTimeField(auto_now=True, editable=False)
    
    def __unicode__(self):
        return ugettext('Site URLs')

    def timeline_maintainers_list(self):
        return self._parse_email_list(self.timeline_maintainers)        
        
    def lb_ballot_maintainers_list(self):
        return self._parse_email_list(self.lb_ballot_maintainers)
        
    def sb_ballot_maintainers_list(self):
        return self._parse_email_list(self.sb_ballot_maintainers)
        
    def _parse_email_list(self, email_str):
        rv = []
        for e in email_str.split(','):
            m = email_re.match(e)
            if m is not None:
                g = m.groupdict()
            else:
                g=dict(name=e,address=e)
            rv.append(g)
        return rv
    
    @classmethod
    def get_urls(cls):
        try:
            return cls.objects.get(pk=1)
        except cls.DoesNotExist:
            return SiteURLs(pk=1)
