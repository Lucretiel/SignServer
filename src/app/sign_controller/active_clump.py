'''
Created on Jan 5, 2013

@author: nathan
'''

import bottle
from bson import ObjectId
import sign_interactor
from . import mongo

app = bottle.Bottle()
app.install(mongo)

@app.route('', ('GET', 'PUT', 'DELETE'))
def handle_active(db):
    method = bottle.request.method
    
    if method == 'GET':
        active = db.active.find_one()
        if active is None:
            raise bottle.HTTPError(404)
        return {'ID': str(active['clump_id'])}
        
    elif method == 'PUT':
        '''The current implementation wipes the sign every time
        '''
        data = bottle.request.json
        
        if 'ID' not in data:
            raise bottle.HTTPError(400, 'Need ID to show')
        if data['ID'] == 'previous':
            sign_interactor.request_previous_active()
        else:
            clump = db.clumps.find_one(ObjectId(data['ID']))
            if clump is None:
                raise bottle.HTTPError(400, 'No clump with that ID')
            sign_interactor.request_new_active(clump['_id'])
        return bottle.HTTPResponse(status=204)
        
    elif method == 'DELETE':
        sign_interactor.request_clear_active()
        return bottle.HTTPResponse(status=204)