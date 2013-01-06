'''
Created on Jan 5, 2013

@author: nathan
'''

import bottle
import jsonschema
from bson import ObjectId

import sign_interactor

app = bottle.Bottle()

defaults = {'name': '',
            'text': '',
            'mode': 'ROTATE',
            'fields': {}}

field_schema = {'type': [{'type': 'object',
                             'properties':
                                {'text': {'type': 'string',
                                          'required': True}}},
                            {'type': 'object',
                             'properties':
                                {'rows': {'type': 'array',
                                          'required': True,
                                          'items':
                                            {'type': 'string',
                                             'pattern': '[0-8]*'}}}}
                            ]}

clump_schema = {'type': 'object',
                'properties':
                    {'name': {'type': 'string'},
                     'text': {'type': 'string'},
                     'mode': {'type': 'string'},
                     'fields': {'type': 'object',
                                'patternProperties':
                                    {'[a-zA-Z0-9]+': field_schema}}}}

def check(data, schema):
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise bottle.HTTPError(400, e.message)
            
@app.route('/', method = ('GET', 'POST', 'DELETE'))
def handle_all_clumps(db):
    method = bottle.request.method
    
    if method == 'GET':
        query = bottle.request.query
        spec = {}
        if query:
            spec.update(query)
        return {'clumps': [{'ID': str(clump['_id']), 'name': clump.get('name', '')}
                           for clump in db.clumps.find(spec, {'name': True})]}
        
    elif method == 'DELETE':
        db.clumps.remove()
        sign_interactor.request_clear_active()
        return bottle.HTTPResponse(status=204)
    
    elif method == 'POST':
        data = bottle.request.json
        check(data, clump_schema)
        
        updated_data = dict(defaults)
        updated_data.update(data)
        
        new_clump = db.clumps.insert(updated_data)
        return bottle.HTTPResponse(str(new_clump), 201)

@app.route('/<ID>', method=('GET', 'PUT', 'PATCH', 'DELETE'))
def handle_clump(db, ID):
    method = bottle.request.method
    ID = ObjectId(ID)
    
    if method == 'GET':
        result = db.clumps.find_one(ID, {'_id': False, 'last_displayed': False, 'expire_at': False})
        if result is None:
            raise bottle.HTTPError(404)
        return result
    
    elif method == 'DELETE':
        result = db.clumps.find_and_modify({'_id': ID}, remove=True)
        if result is None:
            raise bottle.HTTPError(404)
        sign_interactor.request_previous_active(ID)
        return bottle.HTTPResponse(status=204)
    
    elif method == 'PATCH':
        data = bottle.request.json
        check(data, field_schema)
        
        result = db.clumps.find_and_modify({'_id': ID}, {'$set': data})
        if result is None:
            raise bottle.HTTPError(404)
        sign_interactor.request_update_active(ID)
        return bottle.HTTPResponse(status=204)
    
    elif method == 'PUT':
        data = bottle.request.json
        check(data, field_schema)
        
        updated_data = dict(defaults)
        updated_data.update(data)
        updated_data['_id'] = ID
        
        result = db.clumps.save(updated_data)
        return bottle.HTTPResponse(status=204)
        
@app.route('/<ID>/fields/')
def get_field_list(db, ID):
    clump = db.clumps.find_one(ObjectId(ID))
    if clump is None:
        raise bottle.HTTPError(404)
    
    return {'fields': list(clump['fields'].iterkeys())}

@app.route('/<ID>/fields/<fieldname>', method=('GET', 'PUT', 'DELETE'))
def handle_field(db, ID, fieldname):
    if not fieldname.isalnum():
        raise bottle.HTTPError(404, '%s: Error: Field name must be alphanumeric' % fieldname)
   
    ID = ObjectId(ID)
    method = bottle.request.method
    
    if method == 'GET':
        clump = db.clumps.find_one({'_id': ID, 'fields.%s' % fieldname: {'$exists': True}})
        if clump is None:
            raise bottle.HTTPError(404)
        return clump['fields'][fieldname]
    
    elif method == 'DELETE':
        result = db.clumps.update({'_id': ID, 'fields.%s' % fieldname: {'$exists': True}},
                                  {'$unset': {'fields.%s' % fieldname: ''}})
        if result['n'] == 0:
            raise bottle.HTTPError(404)
        sign_interactor.request_update_active(ID)
        return bottle.HTTPResponse(status=204)
    
    elif method == 'PUT':
        data = bottle.request.json
        check(data, field_schema)
        
        result = db.clumps.find_and_modify({'_id': ID}, {'$set': {'fields.%s' % fieldname: data}})
        if result is None:
            raise bottle.HTTPError(404)
        sign_interactor.request_update_active(ID)
        return bottle.HTTPResponse(status=204)