'''
Created on Dec 12, 2012

@author: nathan

This file manages miscellaneous stuff for the Bottle object 
'''

import bottle

import sign_direct

app = bottle.Bottle()

app.mount('/sign-direct/', sign_direct.app)