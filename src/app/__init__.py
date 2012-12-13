'''
Created on Dec 12, 2012

@author: nathan

This file manages miscellaneous stuff for the Bottle object 
'''

import bottle

import sign_direct
import dead_simple

app = bottle.Bottle()

app.mount('/sign-direct', sign_direct.app)
app.mount('/dead-simple', dead_simple.app)