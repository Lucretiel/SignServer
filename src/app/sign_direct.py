'''
Created on Dec 12, 2012

@author: nathan
'''

from bottle import HTTPError, request
import alphasign
from app import sign, app
import labels

def validate_label(self, label, type_name = None):
    if label not in labels.valid_labels:
        raise HTTPError(400, 'label %s is invalid' % label)
    if label in labels.counter_labels:
        raise HTTPError(400, 'label cannot be a counter (1-5)')
    if type_name is not None:
        memory_entry = self.sign.read_memory_table(label=label)
        if memory_entry is None:
            raise HTTPError(400, 'label %s not in memory table' % label)
        if memory_entry['type'] == type_name:
            raise HTTPError(400, 'label %s is of type %s, not %s' % (label, type_name, memory_entry['type']))

@app.get('sign-direct/allocation-table')
def get_allocation_table():
    table = sign.read_memory_table()
    if table is False:
        raise HTTPError(500, 'Failed to read from memory table')
    return {'table': table}

@app.delete('sign-direct/allocation-table')
def clear_allocation_table():
    sign.clear_memory()
    return {'result': 'Sign memory cleared'}
    
@app.put('sign-direct/allocation-table')
def set_allocation_table():
    try:
        if request.json is None:
            raise HTTPError(400, 'Data must be json')
        table = request.json['table']
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
                raise HTTPError(400, 'Missing Field %s in entry\nEntry:\n%s' % (e.message, entry))
            except HTTPError as e:
                e.output += '\nEntry:\n%s' % entry
                raise
    except KeyError as e:
        raise HTTPError(400, 'Missing Field %s' % e.message)
    
    sign.allocate(allocation_objects)
    
    return {'result': 'Memory allocated successfully'}