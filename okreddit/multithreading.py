"""
multithreading
~~~~~~~~~~~~~~

"""
from threading import Thread, Lock
from queue import Queue


class Worker(Thread):
    def __init__(self, tasks):
        """
        :param tasks: A queue containing the tasks for the worker instance.
        :type tasks: queue.Queue instance

        """
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kwargs = self.tasks.get()
            while True:
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print("Error: {}".format(e))
                    continue
                else:
                    self.tasks.task_done()
                    break


class ThreadPool:
    def __init__(self, thread_count):
        self.tasks = Queue(thread_count)
        for _ in range(thread_count): Worker(self.tasks)

    def add_task(self, func, *args, **kwargs):
        """ Add a new task to the queue. """
        self.tasks.put((func, args, kwargs))

    def wait_completion(self):
        """ Blocks until all tasks in queue have been processed. """
        self.tasks.join()
