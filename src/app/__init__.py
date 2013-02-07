'''
Created on Dec 12, 2012

@author: nathan

This file manages miscellaneous stuff for the Bottle object

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

import bottle

import sign_direct
import dead_simple
import sign_controller

app = bottle.Bottle()

app.mount('/sign-direct', sign_direct.app)
app.mount('/dead-simple', dead_simple.app)

@app.route('/favicon.ico')
def get_icon():
    return bottle.static_file('favicon.ico', '.')

def start(**kwargs):
    sign_controller.sign_interactor.start()
    bottle.run(app, **kwargs)
