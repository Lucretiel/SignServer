'''
Created on Dec 13, 2012

@author: nathan
'''

import alphasign

from decorators import cached, retrying

sign = alphasign.Serial()
sign.connect()
sign_memory_timeout = 60 * 10 #How long until the memory cache dies
sign_retries = 3 #Default number of times to retry getting memory. 0 for forever.

@cached
@retrying(sign_retries)
def read_raw_memory_table():
    '''Caching, retrying version of sign.read_raw_memory_table. If the result is
    not None, preserves the result for `timeout` seconds. `timeout` is an
    instance variable of this function.
    '''
    
    table = sign.read_raw_memory_table()
    return table if table is not False else None

read_raw_memory_table.timeout = sign_memory_timeout