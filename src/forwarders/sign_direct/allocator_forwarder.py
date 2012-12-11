'''
Created on Dec 10, 2012

@author: nathan
'''

import json

from sign_direct_forwarder import SignDirectForwarder
import errors
from .. import convertToJson

class AllocatorForwarder(SignDirectForwarder):
    def __init__(self, sign):
        super(AllocatorForwarder, self).__init__(sign)
    
    @convertToJson
    def handle_get(self):
        return self.sign_direct.get_table()
    
    @convertToJson
    def handle_delete(self):
        self.sign_direct.clear_table()
        return {'result': 'table cleared successfully'}
    
    @convertToJson
    def handle_put(self, data):
        try:
            data = json.load(data)
        except ValueError as e:
            raise errors.JSONParseError("Error parsing json", e.message)
        
        self.sign_direct.store_table(data)
        return {'result': 'table stored successfully'}