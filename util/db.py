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
#  Project Name        :    IEEE 802.11 Timeline Tool
#
#  Author              :    Alex Ashley
#
#############################################################################

import sys, math
from django.db import models
from django.core import exceptions, validators
from django import forms

''' Delete all objects from a model, or all objects from a query
'''
def bulk_delete(model, query=None):
    if query is None:
        query = model.objects.all()
    #for q in query:
    #    q.delete()
    pks = list(query.values_list('pk',flat=True))
    #sys.stderr.write('pks %s\n'%str(pks))
    while pks:
        batch = pks[:30]
        pks = pks[30:]
        model.objects.filter(pk__in=batch).delete()

class KeyField(models.Field):
    empty_strings_allowed = False
    default_error_messages = {
        'invalid': "'%s' value must be an integer.",
    }
    description = "Key"

    def __init__(self, verbose_name=None, name=None, **kwargs):
        #kwargs['max_length'] = kwargs.get('max_length', 128)
        kwargs['null'] = kwargs.get('null', False)
        kwargs['blank'] = kwargs.get('blank', False)
        kwargs['editable'] = kwargs.get('editable', False)
        models.Field.__init__(self, verbose_name, name, **kwargs)

    def get_prep_value(self, value):
        if value is None:
            return None
        return long(value)

    def get_prep_lookup(self, lookup_type, value):
        if ((lookup_type == 'gte' or lookup_type == 'lt') and isinstance(value, float)):
            value = math.ceil(value)
        elif isinstance(value,list):
            value = [ long(v) for v in value]
        else:
            value = long(value)
        return super(KeyField, self).get_prep_lookup(lookup_type, value)

    def get_internal_type(self):
        return "IntegerField"
        #return "CharField"

    def to_python(self, value):
        if value is None:
            return value
        try:
            return long(value)
        except (TypeError, ValueError):
            msg = self.error_messages['invalid'] % str(value)
            raise exceptions.ValidationError(msg)

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.CharField}
        defaults.update(kwargs)
        return super(KeyField, self).formfield(**defaults)
