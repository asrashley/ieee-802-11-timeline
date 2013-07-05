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


from django.db import models, connection
from django.db.models.fields import URLField

import datetime, decimal, time, re
    
def flatten_model(item):
    """Converts an instance of a Django model in to a form suitable for storage.
    flatten_model will take an instance of a Django model and inspect each field
    in the object looking for items such as datetime.datetime objects that need
    to be converted to a canonical form before they can be processed for storage.
    """
    rv = {}
    for field in item._meta.fields:
        setattr(rv,field.attname,getattr(item,field.attname))
    return flatten(rv)

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
    db_type = field.db_type(connection=connection)
    if db_type =='date':
        value = from_isodatetime(value)
    elif db_type=='bool':
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
              (re.compile(r'(\w{3} \d{1,2},? \d{4})\s*-\s*(.*$)'), r'\1 \2' ), 
              (re.compile(r'(\w{3} \d{1,2}), (\d{4}\s*\d{1,2}:\d{2})'), r'\1 \2' ), 
              (re.compile(r'(\w{3})-(\d{2})$'), r'\1 \2' ), 
              (re.compile(r'(.+) ([PCE][SD]?T)$'),r'\1')
              ]

def parse_date(date, format=None):
    formats = ["%Y-%m-%d",  "%m/%d/%y", "%m/%d/%Y", "%b %Y", "%b %y", "%m/xx/%y",
               "%a %b %d %Y", "%B %d %Y %H:%M", "%b %d %Y %H:%M",
               "%B %d %Y", "%b %d %Y",'%a %b %d, %Y']
    if format is not None:
        formats.insert(0,format)
    if date.__class__!=str:
        date = str(date)
    d = date
    tz = datetime.timedelta(0)
    if re.match('.+\s+ES?T$',date):
        tz = datetime.timedelta(hours=5)
    elif re.match('.+\s+EDT$',date):
        tz = datetime.timedelta(hours=4)
    elif re.match('.+\s+PS?T$',date):
        tz = datetime.timedelta(hours=8)
    elif re.match('.+\s+PDT$',date):
        tz = datetime.timedelta(hours=7)
    for regex,sub in date_hacks:
        d = regex.sub(sub,d)
    for f in formats:
        try:
            rv = datetime.datetime.strptime(d, f)
            rv += tz;
            return rv
        except ValueError:
            pass
    try:
        return time.strptime(date)
    except ValueError:
        pass
    return None

def set_date(obj,dest,date, format=None):
    date = parse_date(date,format)
    if date is not None:
        setattr(obj, dest, date)
    
def set_date_if_none(obj,dest,date, format=None):
    if getattr(obj,dest) is None and date:
        set_date(obj,dest,date,format)
    
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
