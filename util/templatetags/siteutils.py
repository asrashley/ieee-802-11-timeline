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
from util.cache import CacheControl
from util.models import SiteURLs

from django.template import Library, Node, TemplateSyntaxError
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

@register.simple_tag
def version():
    """
    Returns the string contained in the setting APP_VERSION
    """
    try:
        from django.conf import settings
    except ImportError:
        return ''
    return settings.APP_VERSION
    
@register.filter(name='field_type')
def field_type(field, ftype):
    try:
        t = field.field.widget.__class__.__name__
        return t.lower() == ftype
    except:
        pass
    return False


class SiteURLsNode(Node):
    def __init__(self, var_name):
        self.var_name = var_name
    def render(self, context):
        context[self.var_name] = SiteURLs.get_urls() 
        return ''

@register.tag
def site_urls(parser, token):
    var_name = 'urls'
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
        m = re.search(r' as (\w+)', arg)
        if m:
            var_name = m.groups()[0]
    except ValueError:
        #raise TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
        pass
    return SiteURLsNode(var_name)
