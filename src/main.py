'''
Created on Dec 12, 2012

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