from timeline.models import Project, Ballot

from django.db import models
from django.http import HttpResponse

import datetime, decimal, csv, time

project_fields = ['pk', 'name', 'description', 'doc_type','par', 'task_group',
                  'task_group_url', 'doc_format',  'doc_version', 'baseline',
                  'order',  'par_date', 'par_expiry', 'initial_wg_ballot',
                  'recirc_wg_ballot', 'sb_form_date', 'sb_formed',
                  'initial_sb_ballot', 'recirc_sb_ballot', 'mec_date',
                  'mec_completed', 'wg_approval_date', 'ec_approval_date',
                  'revcom_approval_date','ansi_approval_date', 'withdrawn_date', 
                  'withdrawn', 'history', 'wg_approved', 'ec_approved', 'published']

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

ballot_fields = [ field.attname for field in Ballot._meta.fields]
#ballot_fields.append('project.task_group')

def import_projects_and_ballots(source):
    reader = csv.reader(source,delimiter=',',skipinitialspace=True)
    handler = None
    model = None
    projects = []
    ballots = []
    cache = {}
    last = None
    for line in reader:
        if is_section_header(line,project_fields[:20]):
            model = Project
            handler = import_project
            last = None
            continue
        elif is_section_header(line,ballot_fields):
            model = Ballot
            handler = import_ballot
            last = None
            continue
        elif len(line)>1 and line[0]=='IEEE Project and Final Document':
            model = Project
            handler = import_html_project
            last = None
            continue
        elif is_section_header(line, ['LB','Group(s)','Comment(s)','Instructions','Document(s)']): #,'','Opened','Closed','Days','Ballot Results']):
            model = Ballot
            handler = import_html_letter_ballot
            last = None
            continue
        elif is_section_header(line, html_sponsor_ballot_fields[:5]):
            model = Ballot
            handler = import_html_sponsor_ballot
            last = None
            continue
        if handler is None or model is None:
            continue
        o = handler(line,last,cache)
        if o is not None:
            if model==Project:
                projects.append(o)
            else:
                ballots.append(o)
            last = o                
    return dict(projects=projects,ballots=ballots)

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
    return item[:len(section)]==section
    
def import_html_project(item,last_project,cache):
    entry = make_entries(html_project_fields,item)
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
        if p.par_date:
            p.save()
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
        p.save()
    return None

def import_html_letter_ballot(item,last_ballot,cache):
    entry = make_entries(html_ballot_fields, item)
    if entry['number'] and entry['task_group']:
        lbnum = int(entry['number'])
        try:
            b = Ballot.objects.get(number=lbnum)
        except Ballot.DoesNotExist:
            b = Ballot(number=lbnum)
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
                return None
        try:
            entry['closed'] = entry['closed'][:entry['closed'].index('-')].strip()
        except ValueError:
            pass
        set_date(b,'date', entry['closed'])
        if b.date is None:
            raise Exception("debug") 
        if entry['comments'].lower().find('recirculation')>=0:
            b.ballot_type = 'WR'
        else:
            b.ballot_type = 'WI'
        return b
    if last_ballot is None:
        return None
    if item[-2].lower()=='approve%':
        last_ballot.result  = int(item[-1])
        #if last_ballot.result_for and last_ballot.result_against and last_ballot.result_abstain and last_ballot.result:
        last_ballot.save()
    elif entry['result_type'].lower()=='approve':
        last_ballot.result_for  = int(entry['result'])
    elif entry['result_type'].lower()=='disapprove':
        last_ballot.result_against = int(entry['result'])
    elif entry['result_type'].lower()=='abstain':
        last_ballot.result_abstain = int(entry['result'])
    return None

def import_html_sponsor_ballot(item, last_ballot,cache):
    class Container(object):
        pass
    
    entry = make_entries(html_sponsor_ballot_fields, item)
    tg = entry['Group'].strip()
    if not tg:
        return None
    if entry['Draft'][0]=='D':
        entry['Draft'] = entry['Draft'][1:]
    try:
        float(entry['Draft'])
    except ValueError:
        return None
    if tg.lower().startswith('std. '):
        std = tg[5:]
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
            project = Project.objects.get(task_group=tg)
        except Project.DoesNotExist:
            return None
    obj = Container()
    set_date(obj,'date',entry['Closed'], format='%d/%m/%Y')
    try:
        b = Ballot.objects.get(project=project, draft=entry['Draft'], date=obj.date)
    except Ballot.DoesNotExist:
        lbnum = 10000
        for b in Ballot.objects.all():
            lbnum = max(lbnum,b.number+1)
        b = Ballot(project=project, draft=entry['Draft'], number=lbnum, date=obj.date)
    if 'recirc' in entry['Ballot Type'].lower():
        b.ballot_type = 'SR'
    else:
        b.ballot_type = 'SI'
    b.result = int(entry['Approve_pct'])
    b.result_for = int(entry['Approve'])
    b.result_against = int(entry['Disapprove'])
    b.result_abstain = int(entry['Abstain'])
    b.save()
    return b
    
def import_project(item, last_project,cache):
    entry = make_entries(project_fields, item)
    if entry['pk'] is None:
        return None
    try:
        pk = int(entry['pk'])
    except ValueError:
        return None
    try:
        p = Project.objects.get(pk=int(entry['pk']))
    except Project.DoesNotExist:
        try:
            p = Project.objects.get(name=entry['name'])
        except Project.DoesNotExist:
            p = Project(pk=pk)
    for field in p._meta.fields:
        if not field.primary_key:
            try:
                value = to_python(field, entry[field.attname])
                setattr(p,field.attname,value)
            except KeyError:
                pass
    p.save()
    cache['project%d'%p.pk] = p
    return p

def import_ballot(item, last_ballot,cache):
    entry = make_entries(ballot_fields, item)
    if entry['id'] is None:
        return None
    try:
        pk = int(entry['id'])
    except ValueError:
        return None
    try:
        number = int(entry['number'])
    except ValueError:
        return None
    b = None
    for bt in Ballot.objects.filter(number=number):
        if bt.pk==pk or b is None:
            b = bt
    if b is None:
        b = Ballot(number=number)        
    for field in b._meta.fields:
        if not field.primary_key:
            try:
                value = to_python(field, entry[field.attname])
                setattr(b,field.attname,value)
            except KeyError:
                pass
    try:
        b.project = cache['project%d'%int(entry['project_id'])]
    except KeyError:
        b.project = Project.objects.get(pk=entry['project_id'])
        cache['project%d'%b.project.pk] = b.project 
    b.save()
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
    if value=='' and field.null:
        value = None
    return value
    

def from_isodatetime(date_time):
    if not date_time:
        return None
    if not 'Z' in date_time:
        try:
            return datetime.datetime.strptime(date_time, "%Y-%m-%d")
        except ValueError:
            return datetime.datetime.strptime(date_time, "%d/%m/%Y")
    if 'T' in date_time:
        return datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%SZ")
    return datetime.datetime.strptime(date_time, "%H:%M:%SZ").time()

def set_date(obj,dest,date, format=None):
    formats = ["%m/%d/%y", "%m/%d/%Y", "%b-%y", "%m/xx/%y", "%a %b %d %Y", "%B %d %Y", "%b %d %Y"]
    if format is not None:
        formats.insert(0,format)
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
    
def clean(string):
    okchars=' /.-_:?='
    return ''.join([s for s in string if s.isalnum() or s in okchars])

def make_entries(fields,item):
    entry = {}
    for i,v in enumerate(fields):
        try:
            entry[v] = clean(item[i])
        except IndexError:
            entry[v] = None
    return entry

        