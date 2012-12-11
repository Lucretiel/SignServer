'''
Created on Dec 11, 2012

@author: nathan
'''

from time import sleep

from handler import Handler
from threaded_server import ThreadedServer

def main():
    
    try:
        with ThreadedServer(('localhost', 8888), Handler):
            while True:
                sleep(10)
    except KeyboardInterrupt as e:
        print "Server stopped due to keyboard interrupt:\n%s" % repr(e)

if __name__ == '__main__':
    main()