'''
Created on Dec 12, 2012

@author: nathan
'''

from time import time

class Cached(object):
    def __init__(self, func, timeout):
        self.func = func
        self.value = None
        self.value_time = 0
        self.timeout = timeout
        
    def __call__(self, *args, **kwargs):
        if time() - self.value_time > self.timeout or self.value == None:
            self.value = self.func(*args)
        self.value_time = time()
        return self.value
    def clear_cache(self):
        self.value = None
            
def cached(timeout = 0):
    def _cached(func):
        return Cached(func, timeout)
    return _cached
