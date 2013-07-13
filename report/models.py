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
#  Project Name        :    IEEE 802.11 Timeline Tool                                                                            *
#
#  Author              :    Alex Ashley
#
#############################################################################

from django.db import models
from django.utils.translation import ugettext_lazy as _

class MeetingType(object):
    def __init__(self,code,descr):
        self.code = code
        self.description = descr
        
    def __str__(self):
        return '%s'%self.description
    
    def __unicode__(self):
        return self.description
    
class MeetingReport(models.Model):
    Plenary = MeetingType('P', 'Plenary')
    Interim = MeetingType('I', 'Interim')
    Special = MeetingType('S', 'Special')
    _MEETING_TYPES = [ (b.code,b.description) for b in Plenary, Interim, Special]
    
    id = models.AutoField(primary_key=True)
    session = models.DecimalField(unique=True, db_index=True, decimal_places=1, max_digits=5, help_text=_('Session number'))
    start = models.DateField(help_text=_('Session start date'))
    end = models.DateField(help_text=_('Session end date'))
    cancelled = models.BooleanField(default=False,help_text=_(u'Session was cancelled'))
    
    pending = models.BooleanField(default=True,help_text=_(u'Reports are in-progress and will be provided later'))
    #null=True, blank=True,
    report = models.URLField(null=True, blank=True, help_text=_('URL pointing to meeting report'))
    minutes_doc = models.URLField(null=True, blank=True,
                                  help_text=_('URL pointing to meeting minutes in Word format'))
    minutes_pdf = models.URLField(null=True, blank=True,
                                  help_text=_('URL pointing to meeting minutes in PDF format'))
    
    venue = models.CharField(max_length=100, help_text=_('Name of meeting venue'))
    location = models.CharField(max_length=100, help_text=_('Location of meeting venue'))
    meeting_type = models.CharField(max_length=2, choices=_MEETING_TYPES, help_text=_('Plenary or Interim'))

    @property
    def session_num(self):
        s = int(self.session)
        return s if s==self.session else self.session
    
    def __unicode__(self):
        try:
            return '%03.1f: %s'%(int(self.session),self.location)
        except (ValueError,TypeError):
            return self.location
