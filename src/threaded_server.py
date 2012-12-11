'''This module provides the ThreadedServer and ServerThread classes.

This modules provides a low-level wrapper for the HTTPServer class. It
allows a server to automatically run in its own thread, and for the caller to
stop the server.

@author: nathan
'''

from BaseHTTPServer import HTTPServer
from threading import Thread

class ThreadedServerException(Exception):
    pass

class ServerThread(Thread):
    '''Class to run an HTTPServer in its own thread
    
    ServerThread is a simple Thread overload that runs its server in
    serve_forever mode. It is used by ThreadedServer
    '''
    def __init__(self, server):
        '''Initialize the thread
        '''
        super(ServerThread, self).__init__()
        self.server = server
    def run(self):
        '''Run the thread
        '''
        self.server.serve_forever()
        

class ThreadedServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super(ThreadedServer, self).__init__(server_address, RequestHandlerClass)
        self.thread = None
        
    def start(self):
        if self.thread is not None:
            raise ThreadedServerException('Thread already started')
        
        self.thread = ServerThread(self)
        self.thread.start()
        
    def stop(self):
        if self.thread is None:
            raise ThreadedServerException('No thread exists')
        
        self.shutdown()
        self.thread.join()
        del self.thread
        self.thread = None
    
    #Methods for with construct
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, Type, value, traceback):
        self.stop()