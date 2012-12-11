'''
Created on Dec 11, 2012

@author: nathan
'''

from handler import Handler
from BaseHTTPServer import HTTPServer

def main():
    
    server = HTTPServer(('localhost', 8888), Handler)
    server.serve_forever()

if __name__ == '__main__':
    main()