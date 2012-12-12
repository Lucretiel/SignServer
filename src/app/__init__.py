'''
Created on Dec 12, 2012

@author: nathan

This file manages miscellaneous stuff for the Bottle object 
'''

import bottle
import alphasign

app = bottle.Bottle()
sign = alphasign.Serial()
sign.connect()

import sign_direct