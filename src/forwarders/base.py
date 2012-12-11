'''
Created on Dec 10, 2012

@author: nathan
'''

import errors

class BaseForwarder(object):
    '''This is the base class for all forwarders'''
    def __init__(self, sign):
        self.sign = sign
        
    def handle_get(self):
        raise errors.BadMethod
    
    def handle_delete(self):
        raise errors.BadMethod
    
    def handle_put(self, data):
        raise errors.BadMethod
    
    def handle_method(self, method, data):
        if method == 'GET':
            return self.handle_get()
        elif method == 'PUT':
            return self.handle_put(data)
        elif method == 'DELETE':
            return self.handle_delete()
        