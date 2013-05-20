from django.core.cache import cache

class CacheControl(object):
    def __init__(self):
        self.timeout = 30*60*60
    
    def _get_in_progress_ver(self):
        try:
            return int(cache.get('in_progress_ver','1'))
        except ValueError:
            cache.set('published_ver',1)
            return 1
        
    def _set_in_progress_ver(self,value):
        cache.set('in_progress_ver',value)
    
    in_progress_ver = property(_get_in_progress_ver,_set_in_progress_ver)
    
    def _get_published_ver(self):
        try:
            return int(cache.get('published_ver','1'))
        except ValueError:
            cache.set('published_ver',1)
            return 1
            
    def _set_published_ver(self,value):
        cache.set('published_ver',value)
        
    published_ver = property(_get_published_ver,_set_published_ver)

    def _get_withdrawn_ver(self):
        try:
            return int(cache.get('withdrawn_ver','1'))
        except ValueError:
            cache.set('withdrawn_ver',1)
            return 1
            
    def _set_withdrawn_ver(self,value):
        cache.set('withdrawn_ver',value)
        
    withdrawn_ver = property(_get_withdrawn_ver,_set_withdrawn_ver)

    def _get_open_ver(self):
        try:
            return int(cache.get('open_ver','1'))
        except ValueError:
            cache.set('open_ver',1)
            return 1
            
    def _set_open_ver(self,value):
        cache.set('open_ver',value)
        
    open_ver = property(_get_open_ver,_set_open_ver)

    def _get_closed_ver(self):
        try:
            return int(cache.get('closed_ver','1'))
        except ValueError:
            cache.set('closed_ver',1)
            return 1
            
    def _set_closed_ver(self,value):
        cache.set('closed_ver',value)
        
    closed_ver = property(_get_closed_ver,_set_closed_ver)
