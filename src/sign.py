'''
Created on Dec 13, 2012

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

import alphasign

from decorators import cached, retrying

sign = alphasign.Serial()
sign.connect()
sign_memory_timeout = 60 * 60 #How long until the memory cache dies. -1 for never.
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