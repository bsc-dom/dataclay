
""" Class description goes here. """

'''
Created on 4 feb. 2018

@author: dgasull
'''
import logging
import traceback

LOGGING_FORMAT = '%(asctime)s [%(processName)s] [%(threadName)s] [%(name)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s'


class QueueHandler(logging.Handler):
    """
    This is a logging handler which sends events to a multiprocessing queue.
    """

    def __init__(self, queue):
        """
        Initialise an instance, using the passed queue.
        """
        logging.Handler.__init__(self)
        self.queue = queue
        
    def emit(self, record):
        """
        Emit a record.

        Writes the LogRecord to the queue.
        """
        try:
            ei = record.exc_info
            if ei:
                dummy = self.format(record)  # just to get traceback text into record.exc_text
                record.exc_info = None  # not needed any more
            self.queue.put_nowait(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            print("Uncaught exception - ignoring")
            traceback.print_exc()
            self.handleError(record)


#
# Because you'll want to define the logging configurations for listener and workers, the
# listener and worker process functions take a configurer parameter which is a callable
# for configuring logging for that process. These functions are also passed the queue,
# which they use for communication.
#
# In practice, you can configure the listener however you want, but note that in this
# simple example, the listener does not apply level or filter logic to received records.
# In practice, you would probably want to do ths logic in the worker processes, to avoid
# sending events which would be filtered out between processes.
#
# The size of the rotated files is made small so you can see the results easily.
def listener_configurer():
    
    root = logging.getLogger()
    for handler in root.handlers:
        handler.close()
    root.handlers = []  # Remove all previous handlers

    logFormatter = logging.Formatter(LOGGING_FORMAT)
    h = logging.StreamHandler()
    h.setFormatter(logFormatter)
    h.setLevel(logging.DEBUG)
    
    root.addHandler(h)
    root.setLevel(logging.DEBUG)  # send all messages, for demo; no other level or filter logic applied.


# This is the listener process top-level loop: wait for logging events
# (LogRecords)on the queue and handle them, quit when you get a None for a 
# LogRecord.
def listener_process(queue, configurer):
    configurer()
    while True:
        try:
            record = queue.get()
            if record is None:  # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)  # No level or filter logic applied - just do it!
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            traceback.print_exc()
            import sys
            print >> sys.stderr, 'Whoops! Exception while listening process logging. Cannot print traceback because it implies to have dataClay runtime!'


# The worker configuration is done at the start of the worker process run.
# Note that on Windows you can't rely on fork semantics, so each process
# will run the logging configuration code when it starts.
def worker_configurer(queue):
    root = logging.getLogger()
    for handler in root.handlers:
        handler.close()
    root.handlers = []  # Remove all previous handlers

    root.setLevel(logging.DEBUG)  # send all messages, for demo; no other level or filter logic applied.
    
