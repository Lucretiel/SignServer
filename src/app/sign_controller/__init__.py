'''
Created on Dec 18, 2012

@author: nathan
'''

import bottle
import bottle_mongo

app = bottle.Bottle()

mongo = bottle_mongo.MongoPlugin('localhost:27017', 'signcontroller', 'db')

import clumps
import active_clump

app.mount('/clumps', clumps.app)
#app.mount('/active-clump', active_clump.app)
app.route('/active-clump', ('GET', 'PUT', 'DELETE'), active_clump.handle_active, apply=mongo)