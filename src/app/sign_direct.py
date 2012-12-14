'''
Created on Dec 12, 2012

@author: nathan

Copyright 2012, 2013 Nathan G. West

This file is part of SignServer.

SignServer is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SignServer is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with SignServer.  If not, see <http://www.gnu.org/licenses/>.
'''
import sys

from bottle import HTTPError
import bottle
import alphasign
import constants

from sign import sign, read_raw_memory_table
import general

app = bottle.Bottle()

@app.get('/allocation-table')
def get_allocation_table():
    table = sign.read_memory_table()
    if table is False:
        raise HTTPError(500, 'Failed to read from memory table')
    return {'table': table}

@app.delete('/allocation-table')
def clear_allocation_table():
    sign.clear_memory()
    return {'result': 'Sign memory cleared'}
    
@app.put('/allocation-table')
@general.inject_json
def set_allocation_table(request):
    table = request['table']
    allocation_objects = []
    used_labels = []
    for entry in table:
        try:
            label = entry['label']
            object_type = entry['type'].upper()
            
            general.validate_label(label)
            
            if label in used_labels:
                raise HTTPError(400, 'Label %s has already appeared in entry')
            
            #TODO: check sizes
            if object_type == 'TEXT':
                obj = alphasign.Text(label=label, size=entry['size'])
            elif object_type == 'STRING':
                obj = alphasign.String(label=label, size=entry['size'])
            elif object_type == 'DOTS':
                obj = alphasign.Dots(entry['rows'], entry['columns'], label=label)
            else:
                raise HTTPError(400, '%s is not a valid type' % object_type)
            allocation_objects.append(obj)
            used_labels.append(label)
        except KeyError as e:
            raise HTTPError(400, 'Missing Field %s in entry\nEntry:\n%s' % (e.message, entry)), None, sys.exc_traceback
        except HTTPError as e:
            e.output += '\nEntry:\n%s' % entry
            raise
    
    sign.allocate(allocation_objects)
    read_raw_memory_table.clear_cache()
    
    return {'result': 'Memory allocated successfully'}

@app.put('/allocation-table/<label:re:[1-9A-Za-z]>')
@general.inject_json
def write_file(request, label):        
    memory_table = read_raw_memory_table()
    
    if 'type' in request:
        general.validate_label(label, request['type'], memory_table)
        
    memory_entry = sign.find_entry(memory_table, label)
    memory_table = sign.parse_raw_memory_table(memory_table)
    
    file_type = memory_entry['type']
    
    if file_type == 'TEXT' or file_type == 'STRING':
        data = request['text']
        
        #Prepend color. Ignore invalid colors.
        data = constants.get_color(request.get('color', 'NO_COLOR')) + data
        
        #parse colors
        data = general.parse_colors(data)
        
        #text-specific processing
        if file_type == 'TEXT':
            data = general.parse_labels(data, memory_table)
            
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
    return {'result': 'memory written successfully'}

@app.post('/show-text')
@general.inject_json
def show_text(data):
    label = data['label']
    memory_entry = sign.find_entry(read_raw_memory_table(), label)
    if memory_entry['type'] != 'TEXT':
        raise HTTPError(400, 'The data at label %s must be of type TEXT. It is of type %s' % (label, memory_entry['type']))
    sign.set_run_sequence([alphasign.Text(label=label)])
    return {'result': 'Sign showing text at %s' % label}
        
        