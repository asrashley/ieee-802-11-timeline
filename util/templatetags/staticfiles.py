from django.template import Library

register = Library()

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
