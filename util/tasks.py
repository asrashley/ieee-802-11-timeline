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

from google.appengine.api import taskqueue 
from google.appengine.ext import testbed
from djangoappengine.db.stubs import stub_manager
 
import time, sys

class TaskProxy(object):
    def __init__(self,name,url):
        self.name = name
        self.url = url
    
def add_task(name, url, queue_name='background-processing', countdown=None):
    #sys.stderr.write('a'.join([name,' - ',url,'\n']))
    try:
        name = '%s%d'%(name,int(time.time()/2))
        taskqueue.add(url=url, name=name, method='POST', queue_name=queue_name, countdown=countdown)
        return True
    except taskqueue.TaskAlreadyExistsError:
        return False
    except taskqueue.TombstonedTaskError:
        taskqueue.add(url=url, method='POST', queue_name=queue_name, countdown=countdown)
        return True

def run_test_task_queue(client):
    test_task_stub = stub_manager.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
    #stub = stub_manager.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
    for queue in test_task_stub.GetQueues():
        tasks = test_task_stub.GetTasks(queue['name'])
        for task in tasks:
            if task['method'].upper()=='POST':
                content_type = 'multipart/form-data'
                data = {}
                for k,v in task['headers']:
                    if k=='Content-Type':
                        content_type = v
                if task['body']:
                    data = task['body']
                #sys.stderr.write('p'.join([task['name'],' - ',task['url'],'\n']))
                client.post(task['url'],data=data, content_type=content_type)
            else:
                #sys.stderr.write('g'.join([task['name'],' - ',task['url'],'\n']))
                client.get(task['url'])
            #sys.stderr.write('r'.join([task['name'],' - ',task['url'],'\n']))
        test_task_stub.FlushQueue(queue['name'])
        
