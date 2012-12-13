'''
Created on Dec 12, 2012

@author: nathan
'''

import argparse

import bottle

import app

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', default='39999', type=int)
    parser.add_argument('--live', action='store_true', help='Autoupdate the server with code changes')
    parser.add_argument('--debug', action='store_true', help='Print tracebacks on errors')
    
    options = parser.parse_args()
    bottle.debug(options.debug)
    bottle.run(app.app, host=options.host, port=options.port, reloader=options.live, )

if __name__ == '__main__':
    main()