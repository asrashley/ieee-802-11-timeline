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
from google.appengine.ext import deferred, testbed

from djangoappengine.db.stubs import stub_manager
 
import time, base64, logging

queue_cache = {}

def get_queue(queue_name):
    global queue_cache
    try:
        queue = queue_cache[queue_name]
    except KeyError:
        queue = queue_cache[queue_name] = taskqueue.Queue(queue_name)
    return queue
    
def add_task(name, url, queue_name='background-processing', countdown=0, params={}):
    if not isinstance(name,basestring):
        name = str(name)
    #sys.stderr.write('a'.join([name,' - ',url,'\n']))
    queue = get_queue(queue_name)
    try:
        name = '%s%d'%(name,int(time.time()/2))
        #headers = {'content-type':'multipart/form-data; boundary="-=-=-=-=-=-=-=-=-=-=-"'}
        task = taskqueue.Task(url=url, name=name, method='POST', countdown=countdown, params=params) #, headers=headers)
        queue.add(task)
        #sys.stderr.write('a %s\n'%str(poll_task_queue(queue_name)))
        return True
    except taskqueue.TaskAlreadyExistsError:
        return False
    except taskqueue.TombstonedTaskError:
        taskqueue.add(url=url, method='POST', queue_name=queue_name, countdown=countdown, params=params) #, headers=headers)
        return True
    
def delete_task(queue_name, task_name):    
    queue = get_queue(queue_name)
    queue.delete_tasks_by_name_async(task_name)

def defer_function(func, *args, **kwargs):
    deferred.defer(func,*args,**kwargs)
    
class QueueStats(object):
    def __init__(self, name, active, waiting):
        self.name = name
        self.active = active if active is not None else 0
        self.waiting = waiting if waiting is not None else 0
        self.idle = self.active==0 and self.waiting==0
    def __str__(self, *args, **kwargs):
        return self.__unicode__()
    def __unicode__(self):
        return u'{"name":%s,"active":%s,"waiting":%d,"idle":%s}'%(self.name,self.active,self.waiting,str(self.idle))
        
def poll_task_queue(queue_name):
    if stub_manager.testbed and stub_manager.testbed._activated:
        test_task_stub = stub_manager.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        rv = QueueStats(queue_name,0,0)
        tasks = test_task_stub.GetTasks(queue_name)
        rv.waiting += len(tasks)
        rv.idle = rv.waiting==0
        return rv
    queue = get_queue(queue_name)
    stats = queue.fetch_statistics()
    return QueueStats(queue.name, stats.in_flight, stats.tasks)
    
def run_test_task_queue(client):
    test_task_stub = stub_manager.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
    #stub = stub_manager.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
    for queue in test_task_stub.GetQueues():
        tasks = test_task_stub.GetTasks(queue['name'])
        for task in tasks:
            #logging.info('queue %s %s %s'%(queue['name'],task['method'],task['url']))
            if task['method'].upper()=='POST':
                content_type = 'multipart/form-data; boundary="-=-=-=-=-=-"'
                data = {}
                for k,v in task['headers']:
                    if k.lower()=='content-type':
                        content_type = v
                if task['body']:
                    data = base64.b64decode(task['body'])
                if task['url']=='/_ah/queue/deferred': 
                    #content_type=='application/octet-stream' and queue['name']=='default':
                    deferred.run(data)
                else:
                    #logging.info(' '.join(['post',task['name'],' - ',task['url']]))
                    client.post(task['url'],data=data, content_type=content_type)
            else:
                #logging.info(' '.join(['get',task['name'],' - ',task['url']]))
                client.get(task['url'])
            #logging.info(' '.join(['done',task['name'],' - ',task['url']]))
        test_task_stub.FlushQueue(queue['name'])
        
