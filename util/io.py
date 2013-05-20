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

from project.models import Project
from ballot.models import Ballot
from util.models import ImportProgress, ImportLine 
from util.tasks import add_task
from util.htmlparser import clean, TableHTMLParser

from django.db import models
from django.http import HttpResponse
from django.db.models.fields import URLField
from django.core.urlresolvers import reverse

import datetime, decimal, csv, time, re

project_fields = ['pk', 'name', 'description', 'doc_type','par', 'task_group',
                  'task_group_url', 'doc_format',  'doc_version', 'baseline',
                  'order',  'par_date', 'par_expiry', 'initial_wg_ballot',
                  'recirc_wg_ballot', 'sb_form_date', 'sb_formed',
                  'initial_sb_ballot', 'recirc_sb_ballot', 'mec_date',
                  'mec_completed', 'wg_approval_date', 'ec_approval_date',
                  'revcom_approval_date','ansi_approval_date', 'withdrawn_date', 
                  'withdrawn', 'history', 'wg_approved', 'ec_approved', 'published', 'slug']
#project_fields = [ field.attname for field in Project._meta.fields]

html_project_fields = ['name', 'doc_type','description', 'task_group',
                  'doc_format', 'baseline', 'actual', 'par_date',
                  'initial_wg_ballot_ver','initial_wg_ballot_date',
                  'recirc_wg_ballot_ver', 'recirc_wg_ballot_date',
                  'sb_form_date', 'mec_date',
                  'initial_sb_ballot_ver', 'initial_sb_ballot_date',
                  'recirc_sb_ballot_ver', 'recirc_sb_ballot_date',
                  'wg_approval_date', 'ec_approval_date',
                  'revcom_approval_date','ansi_approval_date', 'withdrawn_date']

html_ballot_fields = [ 'number', 'task_group', 'comments', 'instructions', 'draft',
                      'documents', 'opened', 'closed', 'days', 'result_type', 'result']

html_sponsor_ballot_fields = [ 'Group','Draft','Opened','Closed','Days','Ballot Type','Pool','Approve','Approve_pct',
                              'Disapprove','comments','Disapprove_pct','Abstain','Abstain_pct','Return', 'Return_pct', 'Cmnt' ]

ballot_v1_fields = ['id','project_id','number','draft','date','ballot_type','result','result_for','result_against','result_abstain']

ballot_fields = [ field.attname for field in Ballot._meta.fields]
ballot_fields.append('project.task_group')


class LastObject(object):
    def __init__(self, progress):
        self._object = None
        self._progress = progress
        
    def set(self,value):
        if self._object is not None:
            self._object.save()
            pos = 0
            for line in self._lines:
                pos = max(pos,line.line)
                line.delete()
            if pos>self._progress.current_line:
                self._progress.current_line = pos
                self._progress.save()
        self._lines = []
        self._object = value
    
    def get(self):
        return self._object

    def add(self,line):
        if self._object is not None:
            self._lines.append(line)
         
class Cache(object):
    def __init__(self):
        self._pdict = {}
        #self._bdict = {}
        self._misc = {}
        
    def get(self,key):
        return self._misc[key]
    
    def set(self,key,value):
        self._misc[key] = value
        
    def get_project(self, pk=None, task_group=None, name=None):
        if task_group is not None:
            return self._pdict['task_group-%s'%task_group]
        elif name is not None:
            return self._pdict['name-%s'%name]
        return self._pdict['pk-%d'%pk]
        
    def put_project(self,project):
        self._pdict['pk-%d'%project.pk] = project
        self._pdict['task_group-%s'%project.task_group] = project
        self._pdict['name-%s'%project.name] = project
        
    def get_next_lb_number(self):
        try:
            lbnum = self.get('lbnum')
        except KeyError:
            lbnum = Ballot.FIRST_SPONSOR_LBNUM
            for b in Ballot.objects.all():
                lbnum = max(lbnum,b.number+1)
            self.set('lbnum',lbnum)
        return lbnum
    
    def set_next_lb_number(self,number):
        self.set('lbnum',number)
        
    #def get_ballot(self,pk):
    #    return self._bdict['pk-%d'%pk]
        
    #def put_ballot(self,ballot):
    #    self._bdict['pk-%d'%ballot.pk] = ballot

                
def import_projects_and_ballots(source):
    """ Called by import_view to store a file on the server for later processing.
    """
    if 'html' in source.content_type:
        hr = TableHTMLParser()
        for line in source:
            hr.feed(line)
        reader = hr.buffer
    else:
        reader = csv.reader(source,delimiter=',',skipinitialspace=True)
    #ImportLine.objects.all().delete()
    for linenumber,line in enumerate(reader):
        try:
            il = ImportLine(line=linenumber+1,text=line.text, anchors = line.anchors)
        except AttributeError:
            il = ImportLine(line=linenumber+1,text=[clean(c) for c in line])
        il.save(force_insert=True)
    ip = ImportProgress( linecount = linenumber, current_line = 0)
    ip.save()
    add_task(name = 'import-worker', url=reverse('util.views.import_worker', args=[ip.pk]),countdown=10)
    return ip

def parse_projects_and_ballots(progress):
    """ Called by import worker to process a file that as been uploaded by the import_view
    """
    if progress.started is None:
        progress.started=datetime.datetime.now()
        progress.save()
    #source = ImportLine.objects.all().order_by('line')
    handler = None
    model = None
    cache = Cache()
    last = LastObject(progress)
    for linenum in range(1,progress.linecount+1):
    #for impline in source:
        impline = ImportLine.objects.get(line=linenum)
        if impline.text is None:
            continue
        text = impline.text #.split('|')
        #raise Exception("debug")
        if is_section_header(text,project_fields[:20]):
            model = Project
            handler = import_project
            last.set(None)
            continue
        elif is_section_header(text,ballot_fields):
            model = Ballot
            handler = import_ballot
            last.set(None)
            continue
        elif is_section_header(text,ballot_v1_fields):
            model = Ballot
            handler = import_ballot_v1
            last.set(None)
            continue
        elif len(text)>1 and text[0]=='IEEE Project and Final Document':
            model = Project
            handler = import_html_project
            last.set(None)
            continue
        elif is_section_header(text, ['LB','Group(s)','Comment(s)','Instructions','Document(s)']): #,'','Opened','Closed','Days','Ballot Results']):
            model = Ballot
            handler = import_html_letter_ballot
            last.set(None)
            continue
        elif is_section_header(text, html_sponsor_ballot_fields[:5]):
            model = Ballot
            handler = import_html_sponsor_ballot
            last.set(None)
            continue
        if handler is None or model is None:
            continue
        o = handler(impline, last.get(), cache)
        if o is not None:
            if model==Project:
                progress.add_project(o)
            else:
                progress.add_ballot(o)
            last.set(o)
        last.add(impline)                
    last.set(None)
    #ImportLine.objects.all().delete()
    progress.finished = datetime.datetime.now()
    progress.current_line = progress.linecount
    progress.save()

def export_projects_and_ballots():
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=timeline-'+datetime.datetime.now().strftime('%Y-%m-%d-%H%M.csv')
    writer = csv.writer(response,delimiter=',')
    writer.writerow(project_fields)
    for p in Project.objects.all().order_by('par_date'):
        writer.writerow(flatten([eval('p.'+f) for f in project_fields]))
    writer.writerow([])
    writer.writerow(ballot_fields)
    for b in Ballot.objects.all().order_by('number'):
        writer.writerow(flatten([eval('b.'+f) for f in ballot_fields]))
    writer.writerow([])
    return response


def is_section_header(item,section):
    for a,b in zip(section,item):
        if a!=b:
            #if item[0]=='LB' and section[0]=='LB':
            #    raise Exception("debug")
            return False
    #if item[0]=='LB':
    #    raise Exception("debug")
    return True
    #return item[:len(section)]==section
    
def import_html_project(item,last_project,cache):
    entry = item.as_dict(html_project_fields)
    if entry['actual'].lower()=='actual':
        # Start of a project line
        # remove the "IEEE Std" from in front of the name, and any text after the name
        entry['name'] = entry['name'].split(' ')[2]
        try:
            p = Project.objects.get(name=entry['name'])            
        except Project.DoesNotExist:
            p = Project(name=entry['name'], order=1)
        p.description = entry['description']
        p.doc_type = entry['doc_type']
        set_date(p,'par_date', entry['par_date'])
        p.task_group = entry['task_group']
        p.doc_format = entry['doc_format']
        if entry['mec_date']:
            set_date(p, 'mec_date',entry['mec_date'])
            p.mec_completed = True
        set_date(p,'initial_wg_ballot',entry['initial_wg_ballot_date'])
        set_date(p,'recirc_wg_ballot',entry['recirc_wg_ballot_date'])
        set_date(p,'sb_form_date',entry['sb_form_date'])
        set_date(p,'initial_sb_ballot', entry['initial_sb_ballot_date'])
        set_date(p,'recirc_sb_ballot', entry['recirc_sb_ballot_date'])
        set_date(p,'wg_approval_date', entry['wg_approval_date'])
        set_date(p,'ec_approval_date', entry['ec_approval_date'])
        set_date(p,'revcom_approval_date', entry['revcom_approval_date'])
        set_date(p,'ansi_approval_date','ansi_approval_date')
        set_date(p,'withdrawn_date','withdrawn_date')
        if p.withdrawn_date is not None and p.withdrawn_date.toordinal()<=datetime.datetime.utcnow().toordinal():
            p.withdrawn = True
        cache.put_project(p)
        return p
    if last_project is None:
        return None
    if entry['actual'].lower()=='predicted':
        p = last_project
        #p. = entry['initial_wg_ballot_ver']
        set_date(p,'initial_wg_ballot',entry['initial_wg_ballot_date'])
        #p. = entry['recirc_wg_ballot_ver']
        set_date(p,'recirc_wg_ballot',entry['recirc_wg_ballot_date'])
        set_date(p,'sb_form_date',entry['sb_form_date'])
        if not p.mec_completed:
            set_date(p,'mec_date',entry['mec_date'])
        #p. = entry['initial_sb_ballot_ver']
        set_date(p,'initial_sb_ballot', entry['initial_sb_ballot_date'])
        #p. = entry['recirc_sb_ballot_ver']
        set_date(p,'recirc_sb_ballot', entry['recirc_sb_ballot_date'])
        set_date(p,'wg_approval_date', entry['wg_approval_date'])
        set_date(p, 'ec_approval_date', entry['ec_approval_date'])
        set_date(p, 'revcom_approval_date', entry['revcom_approval_date'])
        #p.save()
    return None

def make_url(entry, prefix=''):
    if not entry or entry.lower()=='n/a':
        return None
    return '%s%s'%(prefix,entry)
    
def import_html_letter_ballot(item,last_ballot,cache):
    entry = item.as_dict(html_ballot_fields)
    if entry['number'] and entry['task_group']:
        lbnum = as_int(entry['number'])
        try:
            b = Ballot.objects.get(number=lbnum)
        except Ballot.DoesNotExist:
            b = Ballot(number=lbnum)
        if entry['task_group']=='TGm':
            # TODO: Find a better solution
            entry['task_group']='TGma'
        try:
            wg = cache.get_project(task_group=entry['task_group'])
        except KeyError:
            try:
                wg = Project.objects.get(task_group=entry['task_group'])
            except Project.DoesNotExist:
                entry['task_group'] = entry['task_group'][:-1] + entry['task_group'][-1].lower() 
                try:
                    wg = Project.objects.get(task_group=entry['task_group'])
                except Project.DoesNotExist:
                    return None
        b.project = wg
        try:
            index = entry['comments'].index('Draft ')
            b.draft = entry['comments'][index+6:]
        except ValueError:
            try:
                index = entry['documents'].index('_D')
                index2 = entry['documents'].index('.pdf')
                b.draft = entry['documents'][index+2:index2]
            except ValueError:
                b.draft = 0
        try:
            b.instructions_url = entry['instructions'].anchor
        except AttributeError:
            b.instructions_url = entry['instructions']
        try:
            b.draft_url = entry['documents'].anchor
        except AttributeError:
            b.draft_url = make_url(entry['documents'],'/11/private/Draft_Standards/11%s/'%(wg.task_group[2:]))
        b.pool  = as_int_or_none(entry['result'])
        set_date(b,'opened', entry['opened'])
        set_date(b,'closed', entry['closed'])
        if b.opened is None or b.closed is None:
            raise Exception("Failed to find date")
        comments = entry['comments'].lower() 
        if comments.find('recirculation')>=0:
            b.ballot_type = Ballot.WGRecirc.code
        elif comments.find('procedural')>=0:
            b.ballot_type = Ballot.Procedural.code
        else:
            b.ballot_type = Ballot.WGInitial.code
        return b
    if last_ballot is None:
        return None
    if entry['draft']:
        draft = entry['draft'].lower()
        if 'redline' in draft:
            try:
                last_ballot.redline_url = entry['documents'].anchor
            except AttributeError: 
                last_ballot.redline_url = None #make_url(entry['documents'],'/11/private/Draft_Standards/11%s/'%(last_ballot.project.task_group[2:]))
        elif 'resolution' in draft:
            try:
                last_ballot.resolution_url =entry['documents'].anchor  
            except AttributeError: 
                last_ballot.resolution_url = make_url(entry['documents'],'/11/private/Draft_Standards/11%s/'%(last_ballot.project.task_group[2:]))
        elif 'comment' in draft:
            try:
                last_ballot.template_url = entry['documents'].anchor 
            except AttributeError: 
                last_ballot.template_url = '/11/LetterBallots/LB%ds/LB%d_comment_form.xls'%(last_ballot.number,last_ballot.number)
        elif 'pool' in draft:
            try:
                last_ballot.pool_url = entry['documents'].anchor 
            except AttributeError: 
                last_ballot.pool_url = '/11/LetterBallots/LB%ds/LB%d_voters_list.xls'%(last_ballot.number,last_ballot.number)
    result_type = entry['result_type'].lower() if entry['result_type'] is not None else None
    #if result_type =='approve%':
    #    last_ballot.result  = as_int_or_none(item[-1])
    if result_type=='approve':
        last_ballot.vote_for  = as_int_or_none(entry['result'])
    elif result_type=='disapprove':
        last_ballot.vote_against = as_int_or_none(entry['result'])
    elif result_type=='abstain':
        last_ballot.vote_abstain = as_int_or_none(entry['result'])
    return None

def import_html_sponsor_ballot(item, last_ballot,cache):
    class Container(object):
        pass
    
    entry = item.as_dict(html_sponsor_ballot_fields)
    tg = entry['Group'].strip()
    if not tg:
        if entry['Disapprove'] and last_ballot is not None:
            try:
                last_ballot.vote_invalid = as_int(entry['Disapprove'])
            except ValueError:
                pass
        return None
    if entry['Draft'][0]=='D':
        entry['Draft'] = entry['Draft'][1:]
    try:
        float(entry['Draft'])
    except (ValueError,TypeError):
        entry['Draft'] = 0
    if tg.lower().startswith('std. '):
        std = tg[5:]
        try:
            project = cache.get_project(name=std)
        except KeyError:
            try:
                project = Project.objects.get(name=std)
            except Project.DoesNotExist:
                return None
    else:
        if tg.lower().startswith('p802.11-rev'):
            tg = 'TG'+tg[11:]
        elif tg.lower().startswith('p802.11'):
            tg = 'TG'+tg[7:]
        try:
            project = cache.get_project(task_group=tg)
        except KeyError:
            try:
                project = Project.objects.get(task_group=tg)
            except Project.DoesNotExist:
                return None
    obj = Container()
    if '/' in entry['Closed']:
        set_date(obj,'opened',entry['Opened'], format='%d/%m/%Y')
        set_date(obj,'closed',entry['Closed'], format='%d/%m/%Y')
    else:
        set_date(obj,'opened',entry['Opened'], format='%Y-%m-%d')
        set_date(obj,'closed',entry['Closed'], format='%Y-%m-%d')
    try:
        b = Ballot.objects.get(project=project, draft=entry['Draft'], closed=obj.closed)
    except Ballot.DoesNotExist:
        lbnum = cache.get_next_lb_number()
        b = Ballot(project=project, draft=entry['Draft'], number=lbnum, closed=obj.closed, opened=obj.opened)
        cache.set_next_lb_number(lbnum+1)
    if 'recirc' in entry['Ballot Type'].lower():
        b.ballot_type = 'SR'
    else:
        b.ballot_type = 'SI'
    #b.result = as_int(entry['Approve_pct'])
    b.vote_for = as_int(entry['Approve'])
    b.vote_against = as_int(entry['Disapprove'])
    b.vote_abstain = as_int(entry['Abstain'])
    if entry['Cmnt']:
        b.comments = as_int(entry['Cmnt'])
    b.pool = as_int(entry['Pool'])
    #b.save()
    return b
    
def import_project(item, last_project,cache):
    entry = item.as_dict(project_fields)
    if entry['pk'] is None:
        return None
    try:
        pk = entry['pk'].as_int()
    except ValueError:
        return None
    try:
        p = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        p = Project(pk=pk)
    for field in p._meta.fields:
        if not field.primary_key:
            try:
                value = to_python(field, entry[field.attname].value) if entry[field.attname] is not None else None
                setattr(p,field.attname,value)
            except KeyError:
                pass
    cache.put_project(p)
    return p

def import_ballot_v1(item, last_ballot,cache):
    return import_ballot(item, last_ballot, cache, fields=ballot_v1_fields)
    
def import_ballot(item, last_ballot,cache,fields=None):
    if fields is None:
        fields = ballot_fields
    entry = item.as_dict(fields)
    #if entry['number'] is None:
    #    return None
    try:
        number = entry['number'].as_int()
    except (ValueError,TypeError):
        return None
    if number==0:
        number = cache.get_next_lb_number()
        cache.set_next_lb_number(number+1)
    b = None
    try:
        b = Ballot.objects.get(number=number)
    except Ballot.DoesNotExist:
        b = Ballot(number=number)        
    for field in b._meta.fields:
        if not field.primary_key:
            try:
                value = to_python(field, entry[field.attname].value) if entry[field.attname] is not None else None
                setattr(b,field.attname,value)
            except KeyError:
                pass
    try:
        proj = entry['project_id'].as_int()
    except ValueError:
        proj = 0
    if proj==0:
        try:
            b.project = cache.get_project(task_group=entry['project.task_group'].value)
        except KeyError:            
            b.project = Project.objects.get(task_group=entry['project.task_group'].value)            
            cache.put_project(b.project)
    else:
        try:
            b.project = cache.get_project(pk=proj)
        except KeyError:
            b.project = Project.objects.get(pk=proj)
            cache.put_project(b.project)
    if b.opened is None:
        set_date(b, 'closed', entry['date'].value, format='%Y-%m-%d')
        b.opened = b.closed + datetime.timedelta(days=-15) 
    if b.pool is None:
        try:
            b.pool = int(b.vote_for) + int(b.vote_against) + int(b.vote_abstain)
        except TypeError:
            pass
    #b.save()
    return b

def flatten(items):
    """Converts an object in to a form suitable for storage.
    flatten will take a dictionary, list or tuple and inspect each item in the object looking for
    items such as datetime.datetime objects that need to be converted to a canonical form before
    they can be processed for storage.
    """
    if isinstance(items,dict):
        rv={}
    else:
        rv = []
    for item in items:
        key = None
        if isinstance(items,dict):
            key = item
            item = items[key]
        if isinstance(item,(datetime.datetime,datetime.time)):
            iso = item.isoformat()
            if not item.utcoffset():
                iso += 'Z'
            item = iso
        elif isinstance(item,(datetime.date)):
            item = item.isoformat()
        elif isinstance(item,long):
            item = '%d'%item
        elif isinstance(item,(unicode,str,decimal.Decimal)):
            item = str(item).replace("'","\'")
        elif isinstance(item,models.Model):
            item = item.pk
            if key:
                key += '_id'
        if key:
            rv[key]=item
        else:
            rv.append(item)
    if items.__class__ == tuple:
        return tuple(rv)
    return rv

def to_python(field,value):
    if field.db_type()=='date':
        value = from_isodatetime(value)
    elif field.db_type()=='bool':
        value = value.lower()=='true'
    elif isinstance(field,URLField):
        value = value.replace(' ','%20')
    if value=='' and field.null:
        value = None
    return value
    
def from_isodatetime(date_time):
    """
    Convert an ISO formated date string to a datetime.datetime object
    """
    if not date_time:
        return None
    if date_time[:2]=='PT':
        if 'M' in date_time:
            dt = datetime.datetime.strptime(date_time, "PT%HH%MM%SS")
        else:
            dt = datetime.datetime.strptime(date_time, "PT%H:%M:%S")
        secs = (dt.hour*60+dt.minute)*60 + dt.second
        return datetime.timedelta(seconds=secs)
    if 'T' in date_time:
        return datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%SZ")
    if not 'Z' in date_time:
        try:
            return datetime.datetime.strptime(date_time, "%Y-%m-%d")
        except ValueError:
            return datetime.datetime.strptime(date_time, "%d/%m/%Y")
    return datetime.datetime.strptime(date_time, "%H:%M:%SZ").time()


date_hacks = [(re.compile('Apri[^l]'),'Apr '), (re.compile('Sept[^e]'),'Sep '),
              (re.compile(r'(\w{3} \d{1,2} \d{4})\s*-\s*(.*$)'), r'\1 \2' ), 
              (re.compile(r'(.+) (CT|EDT|ET)$'),r'\1')
              ]

def set_date(obj,dest,date, format=None):
    formats = ["%m/%d/%y", "%m/%d/%Y", "%b-%y", "%m/xx/%y", "%a %b %d %Y",
               "%B %d %Y %H:%M", "%b %d %Y %H:%M", 
               "%B %d %Y", "%b %d %Y"]
    if format is not None:
        formats.insert(0,format)
    if date.__class__!=str:
        date = str(date)
    for regex,sub in date_hacks:
        date = regex.sub(sub,date)
    for format in formats:
        try:
            setattr(obj, dest, datetime.datetime.strptime(date, format))
            return
        except ValueError:
            pass
    try:
        setattr(obj, dest, time.strptime(date))
        return
    except ValueError:
        pass
    
def as_int(v):
    try:
        return v.as_int()
    except AttributeError:
        return int(v)
    
def as_int_or_none(v):
    try:
        try:
            return v.as_int()
        except AttributeError:
            return int(v)
    except (ValueError, TypeError):
        return None    
