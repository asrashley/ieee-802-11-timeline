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
from django.core.cache import cache
from django.utils.translation import ugettext

import re, traceback, sys
#import cStringIO as StringIO

class AnchorString(object):
    """ AnchorString provides an interface that is similar to String, but has as .anchor property.
    """
    def __init__(self, value=None, anchor=None):
        self.value = value if value is not None else ''
        self.anchor = anchor
        
    def __eq__(self,val):
        return self.value==val
    
    def __ne__(self,val):
        return self.value!=val
    
    def lower(self):
        return self.value.lower()
    
    def strip(self):
        return self.value.strip()
    
    def split(self,delim):
        return self.value.split(delim)
    
    def index(self,s):
        return self.value.index(s)
    
    def endswith(self,s):
        return self.value.endswith(s)
    
    def replace(self,a,b):
        return self.value.replace(a,b)
    
    def as_int(self):
        if self.value is None or self.value=='':
            raise ValueError('Value is None')
        if self.value[-1]=='%':
            return int(self.value[:-1])
        return int(self.value)
    
    def __getitem__(self,key):
        return self.value[key]
    
    def __getslice__(self,i,j):
        return self.value[i:j]
    
    def __nonzero__(self):
        return self.value!=''
    
    def __str__(self):
        return self.value
    
    def __unicode__(self):
        return self.value
    
    def __repr__(self):
        if self.anchor and self.value:
            return 'AnchorString(%s,%s)'%(self.value,self.anchor)
        return self.value

class DBImportLine(models.Model):
    """ Container for one line from an imported file, using the database as a temporary store for the file."""
    line = models.IntegerField(primary_key=True)
    text_str = models.TextField()
    anchors_str  = models.TextField(blank=True, null=True)
    
    def __init__(self, *args, **kwargs):
        self._text = None
        self._anchors = None
        super(DBImportLine,self).__init__(*args, **kwargs)
        
    @property
    def text(self):
        if self._text is None:
            self._text = self.text_str.split('|') if self.text_str!='' else None
        return self._text
    
    @property
    def anchors(self):
        if self._anchors is None:
            self._anchors = self.anchors_str.split('|') if self.anchors_str!='' else None
        return self._anchors
    
    def as_dict(self,fields):
        entry = {}
        anc = self.anchors
        for i,v in enumerate(fields):
            try:
                a = anc[i] if anc is not None else None
                entry[v] = AnchorString(self.text[i],a)
            except IndexError:
                entry[v] = None
        return entry

class CacheImportLine(object):
    """ Container for one line from an imported file, using the Django cache as the temporary store for the file."""
    def __init__(self, line, text=None, anchors=None):
        self.line = line
        self.text = text
        self.anchors = anchors

    def __str__(self):
        return ':'.join([self.line,self.text])
    
    def __repr__(self):
        rv = [`self.line`]
        if self.text is not None:
            rv.append('text="'+self.text_str+'"')
        if self.anchors is not None:
            rv.append('anchors="'+self.anchors_str+'"')
        rv = ','.join(rv)
        return ''.join(['CacheImportLine(',rv,')'])
    
    def __len__(self):
        return 0 if self.text is None else len(self.text)
        
    @classmethod
    def get(cls,line):
        key = 'imp%04d'%line
        text_str=cache.get(key+'l','')
        anchors_str=cache.get(key+'a','')
        text = text_str.split('|') if text_str!='' else None
        anchors = anchors_str.split('|') if anchors_str!='' else None
        return ImportLine(line, text, anchors) 

    @property
    def text_str(self):
        return '|'.join(self.text) if self.text is not None else ''
    
    @property
    def anchors_str(self):
        return '|'.join(self.anchors) if self.anchors is not None else ''
    
    def as_dict(self,fields):
        entry = {}
        for i,v in enumerate(fields):
            try:
                a = self.anchors[i] if self.anchors is not None else None
                entry[v] = AnchorString(self.text[i],a)
            except IndexError:
                entry[v] = None
        return entry
    
    def save(self, *args, **kwargs):
        key = 'imp%04d'%self.line
        cache.set(key+'l',self.text_str)
        cache.set(key+'a',self.anchors_str)
        
    def delete(self):
        key = 'imp%04d'%self.line
        cache.delete(key+'l')
        cache.delete(key+'a')
CacheImportLine.objects = CacheImportLine

ImportLine = CacheImportLine

class ImportProgress(models.Model):
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)
    linecount = models.IntegerField()
    current_line = models.IntegerField()
    projects = models.TextField(blank=True)
    ballots = models.TextField(blank=True)
    reports = models.TextField(blank=True)
    errorstr = models.TextField(blank=True)
    
    def add_error(self,linenum,excp,linestr):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exc = [str(excp)+" exception"]
        for st in traceback.extract_tb(exc_traceback,2):
            filename, line_number, function, text = st
            exc.append('%s:%d in %s'%(filename, line_number, function))
        entry = '|'.join((str(linenum),'~'.join(exc),','.join(linestr.text)))
        if self.errorstr:
            self.errorstr = '\n'.join((self.errorstr,entry))
        else:
            self.errorstr = entry

    @property
    def errors(self):
        rv = []
        if self.errorstr:
            for entry in self.errorstr.split('\n'):
                line,excp,linestr = entry.split('|')
                rv.append(dict(line=line,exception=excp.split('~'),source=linestr))
        return rv
    
    def project_count(self):
        if self.projects:
            return self.projects.count(',')+1
        return 0
    
    def ballot_count(self):
        if self.ballots:
            return self.ballots.count(',')+1
        return 0
    
    def report_count(self):
        if self.reports:
            return self.reports.count(',')+1
        return 0

    @property
    def percent(self):
        return 100*self.current_line/self.linecount if self.linecount>0 else 0
    
    def add_project(self,project):
        if self.projects:
            s = set(self.projects.split(','))
            s.add('%d'%int(project.pk))
            self.projects = ','.join(s)
        else:
            self.projects = '%d'%int(project.pk)
        
    def add_ballot(self,ballot):
        if self.ballots:
            s = set(self.ballots.split(','))
            s.add('%d'%int(ballot.pk))
            self.ballots = ','.join(s)
        else:
            self.ballots = '%d'%int(ballot.pk)

    def add_report(self,report):
        if self.reports:
            s = set(self.reports.split(','))
            s.add('%d'%int(report.session))
            self.reports = ','.join(s)
        else:
            self.reports = '%d'%int(report.session)

