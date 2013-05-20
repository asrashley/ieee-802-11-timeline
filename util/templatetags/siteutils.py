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

from django.template import Library
from django.template.defaultfilters import stringfilter
#from django.utils.translation import ugettext, ungettext

from urlparse import urlsplit
from xml.sax.saxutils import unescape
import re

register = Library()

@register.filter(name='basename')
@stringfilter
def basename(value):
    if not value:
        return ''
    url = urlsplit(value)
    rv = [ r for r in url.path.split('/') if r!='']
    return unescape(rv[-1], {'%20':' '})

pad_re = re.compile(r'.+[^ ]\/[^ ]')

@register.filter(name='padslash')
@stringfilter
def padslash(value):
    if not value:
        return ''
    if pad_re.match(value):
        return value.replace('/', ' / ')
    return value

@register.simple_tag
def get_staticfiles_prefix():
    """
    Returns the string contained in the setting STATICFILES_URL
    """
    try:
        from django.conf import settings
    except ImportError:
        return ''
    return settings.STATICFILES_URL
