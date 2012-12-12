'''
Created on Dec 12, 2012

@author: nathan

This file manages miscellaneous stuff for the Bottle object 
'''

from time import time
import bottle
import alphasign

from caching import cached

app = bottle.Bottle()
sign = alphasign.Serial()
sign.connect()
sign_memory = False
sign_memory_time = 0
sign_memory_timeout = 60 * 10
sign_retries = 3

@cached(sign_memory_timeout)
def read_raw_memory_table(retries=None):
    if retries is None:
        retries = sign_retries
        
    for _ in xrange(retries):
        table = sign.read_raw_memory_table()
        if table is not False:
            return table
    return None

import sign_direct