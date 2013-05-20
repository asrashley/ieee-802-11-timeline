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

from google.appengine.api.labs import taskqueue
from django.core.urlresolvers import resolve

import time,sys

class TaskProxy(object):
    def __init__(self,name,url):
        self.name = name
        self.url = url
    
_test_task_queue = []
_completed_tasks = []
        
def add_task(name, url, queue_name='background-processing', countdown=None):
    try:
        name = '%s%d'%(name,int(time.time()/2))
        taskqueue.add(url=url, name=name, method='POST', queue_name=queue_name, countdown=countdown)
        return True
    except taskqueue.TaskAlreadyExistsError:
        return False
    except taskqueue.UnknownQueueError:
        # Assume running in unit test mode
        _test_task_queue.append(TaskProxy(name,url))
        return True
    except taskqueue.TombstonedTaskError:
        taskqueue.add(url=url, method='POST', queue_name=queue_name, countdown=countdown)
        return True
        
def run_test_task_queue(request):
    global _completed_tasks
    for task in _completed_tasks:
        _test_task_queue.remove(task)
    _completed_tasks = []
    for task in _test_task_queue:
        res = resolve(task.url)
        a = [request]+list(res.args)
        #sys.stderr.write(''.join([task.name,' - ',task.url,'\n']))
        res.func(*a,**res.kwargs)
        _completed_tasks.append(task)
