'''
Created on Dec 18, 2012

@author: nathan
'''

import re
import itertools

import bottle
import bottle_mongo

from bson import ObjectId

from sign import sign, read_raw_memory_table
import alphasign

import constants
import general

app = bottle.Bottle()

app.install(bottle_mongo.MongoPlugin('localhost:27017', 'signcontroller', 'db', ))

fields = {'name': basestring,
          'text': basestring,
          'mode': basestring,
          'fields': dict}

true_defaults = {'name': '',
                 'text': '',
                 'mode': 'ROTATE',
                 'fields': {}}

def check_field(data, fieldname = 'field'):
    if not fieldname.isalnum():
        raise bottle.HTTPError(400, 'Error in %s: field name must be alphanumeric', )
    if 'text' in data and 'rows' in data:
        raise bottle.HTTPError(400, "Error in %s: Can't have text AND rows in field" % fieldname)
    elif 'text' not in data and 'rows' not in data:
        raise bottle.HTTPError(400, 'Error in %s: must have either text of rows in field' % fieldname)
    elif 'text' in data:
        if not isinstance(data['text'], basestring):
            raise bottle.HTTPError(400, 'Error in %s: text must be a string' % fieldname)
    elif 'rows' in data:
        if not isinstance(data['rows'], list):
            raise bottle.HTTPError(400, 'Error in %s: rows must be a list' % fieldname)
        for row in data['rows']:
            if not isinstance(row, basestring):
                raise bottle.HTTPError(400, 'Error in %s: each row must be a string' % fieldname)
            elif re.match('[0-8]*', row) is None:
                raise bottle.HTTPError(400, 'Error in %s: each row must only have digits 0-8' % fieldname)
        
def check_data(data):
    for key, value in data.iteritems():
        if key not in fields:
            raise bottle.HTTPError(400, 'Unrecognized field %s' % key)
        if not isinstance(value, fields[key]):
            raise bottle.HTTPError(400, 'Type mismatch. Field %s should be type %s. Got %s' % (key, str(fields[key]), str(type(value))))
        
    if 'fields' in data:
        for fieldname, field in data['fields'].iteritems():
            check_field(field, fieldname)
            
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
        db.clumps.remove(safe=True)
        return bottle.HTTPResponse(status=204)
    
    elif method == 'POST':
        data = bottle.request.json
        check_data(data)
        
        updated_data = db.default.find_one()
        if updated_data is None:
            db.default.insert(true_defaults)
            updated_data = db.default.find_one(fields={'_id': False})
            if updated_data is None:
                raise bottle.HTTPError(500, 'Failed to read defaults')
        
        updated_data.update(data)
        
        id = db.clumps.insert(updated_data, safe=True)
        return bottle.HTTPResponse(str(id), 201)

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
        result = db.clumps.find_and_modify(ID, remove=True, safe=True)
        if result is None:
            raise bottle.HTTPError(404)
        return bottle.HTTPResponse(status=204)
    
    elif method == 'PUT':
        data = bottle.request.json
        check_data(data)
        
        result = db.clumps.update(ID, {'$set': data}, safe=True)
        if result['n'] == 0:
            raise bottle.HTTPError(404)
        return bottle.HTTPResponse(status=204)
        
@app.get('/clumps/<ID>/fields/')
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
                                  {'$unset': {'fields.%s' % fieldname: ''}},
                                  safe=True)
        if result['n'] == 0:
            raise bottle.HTTPError(404)
        return bottle.HTTPResponse(status=204)
    
    elif method == 'PUT':
        data = bottle.request.json
        check_field(data)
        
        result = db.clumps.update({'_id': ID, 'fields.%s' % fieldname: {'$exists': True}},
                                  {'$set': {'fields.%s' % fieldname: data}},
                                  safe=True)
        if result['n'] == 0:
            raise bottle.HTTPError(404)
        return bottle.HTTPResponse(status=204)
    
################################################################################
# Methods pertaining to interacting with the sign
################################################################################

def validate_allocation(allocation):
    memory = read_raw_memory_table()
    entry = sign.find_entry(memory, allocation['label'])
    if entry is None or entry['type'] != 'TEXT' or entry['size'] != allocation['size']:
        return False
    for field in allocation['fields']:
        entry = sign.find_entry(memory, field['label'])
        if entry is None or entry['type'] != field['type']:
            return False
        if entry['type'] == 'STRING':
            if entry['size'] != field['size']:
                return False
        elif entry['type'] == 'DOTS':
            if entry['rows'] != field['size'][0] or entry['columns'] != field['size'][1]:
                return False
    return True

def allocate(clump, labels=constants.sign_controller_labels):
    labels = iter(labels)
    try: text = alphasign.Text(label=next(labels), size=len(clump['text']))
    except StopIteration: return {}
    allocation = {'clump_id': clump['_id'],
                  'size': len(clump['text']),
                  'active': True,
                  'fields': []}
    allocation_fields = allocation['fields']
    objects = [text]
    for (name, obj), label in itertools.izip(clump['fields'].iteritems(), labels):
        if 'rows' in obj:
            #Sign stuff
            num_rows = len(object['rows'])
            num_columns = max(itertools.imap(lambda row: len(row), obj['rows']))
            obj = alphasign.Dots(num_rows, num_columns, label=label)
            objects.append(obj)
            
            #Database stuff
            field = {'name': name,
                     'type': 'DOTS',
                     'label': label,
                     'size': [num_rows, num_columns]}
            allocation_fields.append(field)
        elif 'text' in obj:
            #Sign stuff
            size = len(obj)
            obj = alphasign.String(label=label, size=size)
            objects.append(obj)
            
            #Database stuff
            field = {'name': name,
                     'type': 'STRING',
                     'label': label,
                     'size': size}
            allocation_fields.append(field)
        else:
            raise bottle.HTTPError(500, 'Bad field: %s\nin clump id %s' % (name, str(clump['_id'])))
            
    sign.allocate(objects)
    read_raw_memory_table.clear_cache()
    return allocation

def make_objects(clump, allocation, names=None):
    #If no names are given, make everything, including the text
    if names is None:
        text = clump['text']
        #parse colors
        text = general.parse_colors(text)
        def label_replacer(flag):
            #Find idiom. find the first item in allocation with the right name.
            field = next((field for field in allocation['fields'] if field['name'] == flag), None)
            if field is None:
                return None
            if field['type'] == 'STRING':
                return alphasign.String(label=field['label']).call()
            elif field['type'] == 'DOTS':
                return alphasign.Dots(label=field['label']).call()
        #parse labels.
        text = general.parse_generic(text, label_replacer)
        yield alphasign.Text(text, allocation['label'],
                             mode=constants.get_mode(clump['mode']))
    
    #Run through each named subfield
    for allocation_field in allocation['fields']:
        if names and allocation_field['name'] not in names:
            continue
        
        #get the associated clump subfield
        clump_field = clump['fields'][allocation_field['name']]
        
        if allocation_field['type'] == 'DOTS':
            rows, columns = allocation_field['size']
            dots = alphasign.Dots(rows, columns, label=allocation_field['label'])
            for i, row in enumerate(clump_field['row']):
                dots.set_row(i, row)
            yield dots
        elif allocation_field['type'] == 'STRING':
            text = clump_field['text']
            text = general.parse_colors(text)
            yield alphasign.String(text, label=allocation_field['label'])

def write_to_sign(clump, allocation, names=None):
    '''This is the do-work function. It assumes everything leading up to it is
    good.
    '''
    for obj in make_objects(clump, allocation, names):
        sign.write(obj)
    
@app.route('/sign-controller/active-clump', method=('GET', 'PUT'))
def handle_active(db):
    method = bottle.request.method
    
    if method == 'GET':
        active = db.allocations.find_one({'active': True}, {'clump_id': True, '_id': False})
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
        
        currently_allocated = db.allocations.find_one({'active': True})
        if (currently_allocated is None or
            currently_allocated['clump_id'] != clump['_id'] or
            not validate_allocation(currently_allocated)):
            
            new_allocation = allocate(clump)
            write_to_sign(clump, new_allocation)
            db.allocations.remove()
            db.allocations.insert(new_allocation)
            currently_allocated = new_allocation
        else:
            write_to_sign(clump, currently_allocated)
        sign.set_run_sequence([alphasign.Text(label=currently_allocated['label'])])
            