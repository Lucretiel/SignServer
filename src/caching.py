'''
Created on Dec 12, 2012

@author: nathan
'''

from time import time

class cached(object):
    def __init__(self, timeout = 10):
        self.value = None
        self.value_time = 0
        self.timeout = timeout
        
    def __call__(self, func):
        def func_wrapper(*args):
            if time() - self.value_time > self.timeout or self.value == None:
                self.value = func(*args)
            self.value_time = time()
            return self.value
        return func_wrapper