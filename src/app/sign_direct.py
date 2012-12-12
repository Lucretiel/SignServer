'''
Created on Dec 12, 2012

@author: nathan
'''
import sys
import re

from bottle import HTTPError
import bottle
import alphasign
from app import sign, app, read_raw_memory_table
import constants

def validate_label(label, type_name = None):
    if label not in constants.valid_labels:
        raise HTTPError(400, 'label %s is invalid' % label)
    if label in constants.counter_labels:
        raise HTTPError(400, 'label cannot be a counter (1-5)')
    if type_name is not None:
        memory_entry = self.sign.read_memory_table(label=label)
        if memory_entry is None:
            raise HTTPError(400, 'label %s not in memory table' % label)
        if memory_entry['type'] == type_name:
            raise HTTPError(400, 'label %s is of type %s, not %s' % (label, type_name, memory_entry['type']))

def parse_generic(text, replacer):
    '''This function scans the text for all flags of the form {stuff}, and
    replaces them according to the replacer function. The replacer function
    takes, as an argument, the content inside the flag. If it returns None,
    the flag is untouched.
    '''
    
    match_pattern = '\{([^}]*)\}'
    def _replacer(match):
        replacement = replacer(match.group(1))
        return replacement if replacement is not None else match.group()
    
    return re.sub(match_pattern, _replacer, text)

def parse_colors(text):
    '''This function scans the text for color flags (ie, {RED}) and replaces
    them with their alphasign call-character equivelent
    '''
    def replacer(color):
        color = constants.get_color(color)
        if color != '':
            return color
        
    return parse_generic(text, replacer)

def parse_labels(text, memory):
    '''This function scans the text for label flags (ie, {C}) and replaces
    them with their alphasign call-character equivelents. It depends on the
    current memory table of the sign.
    '''
    
    types = {'STRING': alphasign.String, 'DOTS': alphasign.Dots}
    memory_types = {entry['label']: types[entry['type']] 
                    for entry in memory if entry['type'] != 'TEXT'}
    
    def replacer(label):
        if label in memory_types:
            return memory_types[label](label=label).call()
        
    return parse_generic(text, replacer)

def inject_json():

################################################################################
# SERVER METHODS                                                               #
################################################################################

@app.get('/sign-direct/allocation-table')
def get_allocation_table():
    table = sign.read_memory_table()
    if table is False:
        raise HTTPError(500, 'Failed to read from memory table')
    return {'table': table}

@app.delete('/sign-direct/allocation-table')
def clear_allocation_table():
    sign.clear_memory()
    return {'result': 'Sign memory cleared'}
    
@app.put('/sign-direct/allocation-table')
def set_allocation_table():
    try:
        if bottle.request.json is None:
            raise HTTPError(400, 'Data must be json')
        table = bottle.request.json['table']
        allocation_objects = []
        used_labels = []
        for entry in table:
            try:
                label = entry['label']
                object_type = entry['type']
                
                validate_label(label)
                
                if label in used_labels:
                    raise HTTPError(400, 'Label %s has already appeared in entry')
                
                #TODO: check sizes
                if object_type == 'TEXT':
                    obj = alphasign.Text(label=label, size=entry['size'])
                elif object_type == 'STRING':
                    obj = alphasign.String(label=label, size=entry['size'])
                elif object_type == 'DOTS':
                    obj = alphasign.Dots(entry['rows'], entry['columns'], label=label)
                allocation_objects.append(obj)
                used_labels.append(label)
            except KeyError as e:
                raise HTTPError(400, 'Missing Field %s in entry\nEntry:\n%s' % (e.message, entry)), None, sys.exc_traceback
            except HTTPError as e:
                e.output += '\nEntry:\n%s' % entry
                raise
    except KeyError as e:
        raise HTTPError(400, 'Missing Field %s' % e.message), None, sys.exc_traceback
    
    sign.allocate(allocation_objects)
    
    return {'result': 'Memory allocated successfully'}

@app.put('/sign-direct/allocation-table/<label:re:[1-9A-Za-z]>')
def write_file(label):
    try:
        if bottle.request.json is None:
            raise HTTPError(400, 'Data must be json')
        
        memory_table = read_raw_memory_table()
        memory_entry = sign.read_memory_table(memory_table, label)
        memory_table = sign.read_memory_table(memory_table)
        
        file_type = memory_entry['type']
        request = bottle.request.json
        
        if request.get('type', file_type) != file_type:
            raise HTTPError(400, 'Mismatched type. Type in memory is %s.' % file_type)
        
        if file_type == 'TEXT' or file_type == 'STRING':
            data = request['text']
            
            #Prepend color. Ignore invalid colors.
            data = constants.get_color(request.get('color', 'NO_COLOR')) + data
            
            #parse colors
            data = parse_colors(data)
            
            #text-specific processing
            if file_type == 'TEXT':
                data = parse_labels(data, memory_table)
                
            #check size
            if len(data) > memory_entry['size']:
                raise HTTPError(400, 'Not enough memory allocated. Requires %s, only %s allocated.' % (len(data), memory_entry['size']))
            
            if file_type == 'TEXT':
                mode = constants.get_mode(request.get('mode', 'HOLD'))
                obj = alphasign.Text(data, label=label, mode=mode)
            elif file_type == 'STRING':
                obj = alphasign.String(data, label=label)
                
        elif file_type == 'DOTS':
            data = request['data']
            rows = memory_entry['rows']
            columns = memory_entry['columns']
            
            obj = alphasign.Dots(rows, columns, label=label)
            
            for i, row in enumerate(data[:rows]):
                obj.set_row(i, row)
                
        sign.write(obj)
    except KeyError as e:
        raise HTTPError(400, 'Missing Field %s' % e.message), None, sys.exc_traceback 
        
        
        