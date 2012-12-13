'''
Created on Dec 13, 2012

@author: nathan
'''

import alphasign

from caching import cached

sign = alphasign.Serial()
sign.connect()
sign_memory_timeout = 60 * 10 #How long until the memory cache dies
sign_retries = 3 #Number of times 

@cached
def read_raw_memory_table(retries=None):
    if retries is None:
        retries = sign_retries
        
    for _ in xrange(retries):
        table = sign.read_raw_memory_table()
        if table is not False:
            return table
    return None

read_raw_memory_table.timeout = sign_memory_timeout