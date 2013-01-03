'''
Created on Dec 18, 2012

@author: nathan
'''

import sys
import multiprocessing
from datetime import datetime

#MongoDB stuff
from bson import ObjectId
from pymongo.errors import CollectionInvalid

#web stuff
import bottle
import bottle_mongo

#Sign stuff
from sign import sign
import alphasign

#Misc stuff
import jsonschema

#Local stuff
import constants
import general

app = bottle.Bottle()

mongo_plugin = bottle_mongo.MongoPlugin('localhost:27017', 'signcontroller', 'db')
app.install(mongo_plugin)

true_defaults = {'name': '',
                 'text': '',
                 'mode': 'ROTATE',
                 'fields': {}}

subfield_schema = {'type': [{'type': 'object',
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
                                    {'[a-zA-Z0-9]+': subfield_schema}}}}

def _check(data, schema):
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise bottle.HTTPError(400, e.message, e, sys.exc_traceback)

def check_data(data):
    _check(data, clump_schema)
    
def check_field(data):
    _check(data, subfield_schema)
            
@app.route('/clumps/', method = ('GET', 'POST', 'DELETE'))
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
        request_clear_active()
        return bottle.HTTPResponse(status=204)
    
    elif method == 'POST':
        data = bottle.request.json
        check_data(data)
        
        updated_data = dict(true_defaults)
        updated_data.update(data)
        
        new_clump = db.clumps.insert(updated_data)
        return bottle.HTTPResponse(str(new_clump), 201)

@app.route('/clumps/<ID>', method=('GET', 'PUT', 'DELETE'))
def handle_clump(db, ID):
    method = bottle.request.method
    ID = ObjectId(ID)
    
    if method == 'GET':
        result = db.clumps.find_one(ID, {'_id': False})
        if result is None:
            raise bottle.HTTPError(404)
        return result
    
    elif method == 'DELETE':
        result = db.clumps.find_and_modify({'_id': ID}, remove=True)
        if result is None:
            raise bottle.HTTPError(404)
        request_clear_active(ID)
        return bottle.HTTPResponse(status=204)
    
    elif method == 'PUT':
        data = bottle.request.json
        check_data(data)
        
        result = db.clumps.find_and_modify({'_id': ID}, {'$set': data})
        if result is None:
            raise bottle.HTTPError(404)
        request_update_active(ID)
        result['_id'] = str(result['_id'])
        return result
        
@app.route('/clumps/<ID>/fields/')
def get_field_list(db, ID):
    clump = db.clumps.find_one(ObjectId(ID))
    if clump is None:
        raise bottle.HTTPError(404)
    
    return {'fields': list(clump['fields'].iterkeys())}

@app.route('/clumps/<ID>/fields/<fieldname>', method=('GET', 'PUT', 'DELETE'))
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
        request_update_active(ID)
        return bottle.HTTPResponse(status=204)
    
    elif method == 'PUT':
        data = bottle.request.json
        check_field(data)
        
        result = db.clumps.find_and_modify({'_id': ID, 'fields.%s' % fieldname: {'$exists': True}},
                                           {'$set': {'fields.%s' % fieldname: data}}, new=True)
        if result is None:
            raise bottle.HTTPError(404)
        request_update_active(ID)
        return bottle.HTTPResponse(status=204)
    

################################################################################
# Methods pertaining to interacting with the sign
################################################################################

receive_message, send_message = multiprocessing.Pipe(False)

def send_request(command, clump_id):
    send_message.send({'command': command, 'id': clump_id})
    
def request_new_active(clump_id):
    send_request('SET', clump_id)
    
def request_update_active(clump_id):
    send_request('UPDATE', clump_id)
    
def request_clear_active(clump_id=None):
    send_request('CLEAR', clump_id)
                
def make_objects(clump, names=None):
    '''Given a clump, generate the objects to be written to the sign.
    '''
    labels = constants.sign_controller_labels
    text_label = next(labels)
    fields = clump['fields']
    
    label_map = {name: (next(labels), 'STRING' if 'text' in field else 'DOTS')
                 for name, field in sorted(fields.iteritems())}
    
    text = clump['text']
    #parse colors
    text = general.parse_colors(text)
    
    #parse labels
    def label_replacer(flag):
        if flag in label_map:
            label, type = label_map['flag']
            if type == 'STRING':
                return alphasign.String(label=label).call()
            elif type == 'DOTS':
                return alphasign.Dots(label=label).call()
        return None
    text = general.parse_generic(text, label_replacer)
    
    yield alphasign.Text(text, text_label,
                         mode=constants.get_mode(clump['mode']))
    
    if names is not None:
        label_map = {name: val for name, val in label_map if name in names}
        
    #Run through each named subfield
    for fieldname, (label, fieldtype) in label_map:
        field = fields[fieldname]
        
        if fieldtype == 'DOTS':
            rows = field['rows']
            num_rows = len(rows)
            num_columns = max(len(row) for row in rows)
            dots = alphasign.Dots(num_rows, num_columns, label=label)
            for i, row in enumerate(rows):
                dots.set_row(i, str(row))
            yield dots
        elif fieldtype == 'STRING':
            text = field['text']
            text = general.parse_colors(text)
            yield alphasign.String(text, label=label)
    
@app.route('/active-clump', method=('GET', 'PUT'))
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
        clump = db.clumps.find_one(ObjectId(data['ID']))
        if clump is None:
            raise bottle.HTTPError(400, 'No clump with that ID')
        request_new_active(clump['_id'])
        
################################################################################
# SignInteractor- a separate process for actually interacting with the sign
################################################################################

class SignInteractor(multiprocessing.Process):
    def __init__(self, queue):
        super(SignInteractor, self).__init__()
        self.daemon = True
        self.queue = queue #This is actually a Pipe endpoint. Consider renaming.
        self.db = mongo_plugin.get_mongo()
        try:
            self.db.create_collection('active', capped=True, max=1, size=1000)
        except CollectionInvalid: pass
        
    def run(self):
        try:
            while True:
                message = self.queue.recv()
                clump_id = message['id']
                if message['command'] == 'SET':
                    currently_active = self.db.active.find_one({'clump_id': clump_id})
                    if currently_active is None:
                        self.set_active(clump_id)
                
                elif message['command'] == 'UPDATE':
                    currently_active = self.db.active.find_one({'clump_id': clump_id})
                    if currently_active is not None:
                        self.set_active(clump_id)
                        
                elif message['command'] == 'CLEAR':
                    query = {'clump_id': clump_id} if clump_id is not None else {}
                    currently_active = self.db.active.find_one(query)
                    if currently_active is not None:
                        self.set_previous_active()
                        
        except EOFError:
            pass
        finally:
            self.queue.close()
            
    def set_active(self, clump_id):
        '''Locate the clump with the given id and set it's last displayed to
        now, set it to active, and display it. If it doesn't exist, try the last
        most recently displayed clump.
        '''
        clump = self.db.clumps.find_and_modify({'_id': clump_id},
                                               {'$set': {'last_displayed': datetime.now()}})
        if clump is None:
            self.set_previous_active()
        else:
            self.db.active.insert({'clump_id': clump_id})
            self.write_to_sign(clump)
            
    def set_previous_active(self):
        '''Finds the last most recently displayed clump and displays it.
        '''
        previous = self.db.clumps.find().sort('last_displayed', -1).limit(1)
        if previous.count(True) > 0: #count(True) counts WITH limit(1)
            previous = previous[0]
            self.set_active(previous['_id'])
        else:
            self.db.active.insert({'clump_id': None})
            empty_clump = {'name': '', 'text': '', 'mode': 'HOLD', 'fields': {}}
            self.write_to_sign(empty_clump)
        
    def write_to_sign(self, clump):
        objects = list(make_objects(clump))
        sign.allocate(objects)
        for obj in objects: sign.write(obj)
        sign.set_run_sequence([objects[0]])
        
sign_interactor_process = SignInteractor(receive_message)
sign_interactor_process.start()