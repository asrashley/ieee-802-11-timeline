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
import re, os, logging, sys
from urlparse import urlsplit
from xml.sax.saxutils import unescape

from django.template import Library, Node, TemplateSyntaxError
from django.template.defaultfilters import stringfilter
#from django.utils.translation import ugettext, ungettext
from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured

from util.cache import CacheControl
from util.models import SiteURLs

# At compile time, cache the directories to search.
fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
app_css_dirs = []
for app in settings.INSTALLED_APPS:
    try:
        mod = import_module(app)
    except ImportError, e:
        raise ImproperlyConfigured('siteutils.py ImportError %s: %s' % (app, e.args[0]))
    template_dir = os.path.join(os.path.dirname(mod.__file__), 'static', 'css')
    if os.path.isdir(template_dir):
        app_css_dirs.append(template_dir.decode(fs_encoding))
app_css_dirs.append(os.path.join(settings.MEDIA_ROOT,'css'))
# It won't change, so convert it to a tuple to save memory.
app_css_dirs = tuple(app_css_dirs)

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
def version():
    """
    Returns the string contained in the setting APP_VERSION
    """
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

class CssIncludeNode(Node):
    def __init__(self,absfilename,filename):
        self.absfilename = absfilename
        self.filename = filename
    def render(self,context):
        rv = ''
        export = True
        #try:
        export = context['cache'].export is not None
        #except KeyError,e:
        #    logging.error(str(e))
        if export:
            cssfile = None
            try:
                cssfile = open(self.absfilename,'r')
                rv = '\n'.join(['<style type="text/css">','/* %s */'%self.filename,cssfile.read(),'</style>'])
            except Exception,e:
                logging.error(str(e))
            finally:
                if cssfile:
                    cssfile.close()
        else:
            #url = self.filename.replace('\\','/')
            rv = '<link rel="stylesheet" media="all" type="text/css" href="%scss/%s" />'%(settings.STATIC_URL,self.filename)
        return rv

@register.tag        
def include_css(parser,token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, filename = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    if not (filename[0] == filename[-1] and filename[0] in ('"', "'")):
        raise TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
    filename = filename[1:-1]
    for d in app_css_dirs:
        f = os.path.join(d,filename)
        if os.path.exists(f):
            return CssIncludeNode(f,filename)
    raise TemplateSyntaxError("Unable to find CSS file %s, checked %s"%(filename,str(app_css_dirs)))    