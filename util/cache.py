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

from django.core.cache import cache

import time

class CacheControl(object):
    def __init__(self, **args):
        self.timeout = 30*60*60
        self.export = None
        self.__dict__.update(args)

    def __rand_ver(self):
        return int(time.time()) & 0xFFFFF
    
    def _get_ver(self,name):
        try:
            return int(cache.get(name))
        except (TypeError,ValueError):
            rv = self.__rand_ver()
            cache.set(name,rv)
            return rv
        
    def _get_in_progress_ver(self):
        return self._get_ver('in_progress_ver')
        
    def _set_in_progress_ver(self,value):
        cache.set('in_progress_ver',value)
    
    in_progress_ver = property(_get_in_progress_ver,_set_in_progress_ver)
    
    def _get_published_ver(self):
        return self._get_ver('published_ver')
            
    def _set_published_ver(self,value):
        cache.set('published_ver',value)
        
    published_ver = property(_get_published_ver,_set_published_ver)

    def _get_withdrawn_ver(self):
        return self._get_ver('withdrawn_ver')
            
    def _set_withdrawn_ver(self,value):
        cache.set('withdrawn_ver',value)
        
    withdrawn_ver = property(_get_withdrawn_ver,_set_withdrawn_ver)

    def _get_open_ver(self):
        return self._get_ver('open_ver')
            
    def _set_open_ver(self,value):
        cache.set('open_ver',value)
        
    open_ver = property(_get_open_ver,_set_open_ver)

    def _get_closed_ver(self):
        return self._get_ver('closed_ver')
            
    def _set_closed_ver(self,value):
        cache.set('closed_ver',value)
        
    closed_ver = property(_get_closed_ver,_set_closed_ver)
