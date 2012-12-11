'''
Created on Dec 10, 2012

@author: nathan
'''
import urlparse
from os import path
from BaseHTTPServer import BaseHTTPRequestHandler

import alphasign

import forwarders
import errors
 
class Handler(BaseHTTPRequestHandler):
    sign = alphasign.Serial()
    sign.connect()
    
    def __init__(self, *args, **kwargs):
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
        
    def discover_forwarder(self):
        '''
        Parse the path of the URL to determine what forwarding class should be
        used.
        '''
        parsed_url = urlparse.urlparse(self.path)
        layer, resource = path.split(parsed_url.path)
        if resource == '':
            layer, resource = path.split(resource)
            
        try:
            layer_module = forwarders.layers[layer[1:]] #strip out the opening /
            forwarder_class = layer_module.resources[resource]
            return forwarder_class(self.sign)
        except KeyError:
            raise errors.BadResource
        
    def handle_method(self, method, data=None):
        try:
            result = self.discover_forwarder().handle_method(method, data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.wfile.write(result)
        except errors.HandlingError as e:
            message = '\n'.join(map(str, e.args))
            self.send_error(e.code, message)
        
    def do_GET(self):
        self.handle_method('GET')
            
    def do_DELETE(self):
        self.handle_method('DELETE')
            
    def do_PUT(self):
        self.handle_method('PUT', self.rfile)
            
            