from google.appengine.api.labs import taskqueue

import time

def add_task(name, url, queue_name='background-processing'):
    try:
        try:
            name = '%s%d'%(name,int(time.time()/2))
            taskqueue.add(url=url, name=name, method='POST', queue_name=queue_name)
            return True
        except (taskqueue.TaskAlreadyExistsError, taskqueue.UnknownQueueError):
            return False
    except taskqueue.TombstonedTaskError:
        taskqueue.add(url=url, method='POST', queue_name=queue_name)
        return True
        
