'''
Created on Dec 18, 2012

@author: nathan
'''

import bottle
import bottle_mongo

app = bottle.Bottle()

mongo_plugin = bottle_mongo.MongoPlugin('localhost:27017', 'signcontroller', 'db')
app.install(mongo_plugin)

import clumps
import active_clump

app.mount('/clumps', clumps.app, skip=None)
app.mount('/active-clump', active_clump.app, skip=None)