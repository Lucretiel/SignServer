'''
Created on Dec 12, 2012

@author: nathan

Copyright 2012, 2013 Nathan G. West

This file is part of SignServer.

SignServer is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SignServer is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with SignServer.  If not, see <http://www.gnu.org/licenses/>.
'''

from time import time
from functools import wraps

class cached(object):
    '''Decorator to make functions cache their value. Converts function into
    an object of type Cached, above. Set the timeout with timeout and reset
    the cache with clear_cache(). None is not cached.
    '''
    def __init__(self, func):
        self.func = func
        self.value = None
        self.value_time = 0
        self.timeout = 0
    def __call__(self, *args, **kwargs):
        if self.value is None or (self.timeout != -1 and time() - self.value_time > self.timeout):
            self.value = self.func(*args)
            self.value_time = time()
        return self.value
    def clear_cache(self):
        self.value = None

def retrying(default):
    '''Decorator to make functions retry a certain number of times before
    returning a value. returning None is considered a failure. The decorated
    function will use the retries kwarg to know how many times to retry,
    defaulting to default
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = kwargs.pop('retries', default)
            result = None
            if retries == 0:
                while result is None:
                    result = func(*args, **kwargs)
            else:
                for _ in xrange(retries):
                    result = func(*args, **kwargs)
                    if result is not None:
                        break
            return result
        return wrapper
    return decorator