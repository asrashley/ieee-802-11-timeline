
from util.cache import CacheControl

def site_context(request):
    return dict(cache=CacheControl())