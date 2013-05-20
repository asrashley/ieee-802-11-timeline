from django.template import Library
from django.template.defaultfilters import stringfilter
#from django.utils.translation import ugettext, ungettext
from urlparse import urlsplit
from xml.sax.saxutils import unescape

register = Library()

@register.filter(name='basename')
@stringfilter
def basename(value):
    if not value:
        return ''
    url = urlsplit(value)
    rv = [ r for r in url.path.split('/') if r!='']
    return unescape(rv[-1], {'%20':' '})

#@register.filter(name='')
#@stringfilter
#def basename(value):
