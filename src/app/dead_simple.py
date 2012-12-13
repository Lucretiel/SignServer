'''
Created on Dec 13, 2012

@author: nathan
'''

from itertools import chain

from bottle import HTTPError
import bottle

from sign import sign, read_raw_memory_table
import general
import constants
import alphasign

app = bottle.Bottle()

def parse_labels(text):
    '''Custom parse_labels function. Only looks for a-z, and assumes string type
    '''
    def replacer(match):
        if match.lower() in constants.dead_simple_string_labels:
            return alphasign.String(label=match.lower()).call()
        return None
    
    return general.parse_generic(text, replacer)

@app.route('/reset')
def reset():
    params = bottle.request.query
    
    text_length = params.get('textsize', 128, type=int)
    string_length = params.get('stringsize', 128, type=int)
    
    text = alphasign.Text('%sREADY FOR DEAD-SIMPLE. TRY HITTING %s/dead-simple/send?text=<text>' % (alphasign.colors.RED, alphasign.colors.YELLOW), label='A', size=text_length, mode=alphasign.modes.COMPRESSED_ROTATE)
    strings = (alphasign.String(label=label, size=string_length) for label in constants.dead_simple_string_labels)
    
    sign.allocate(chain([text], strings))
    sign.set_run_sequence([text])
    sign.write(text)
    read_raw_memory_table.clear_cache()
    
    return {'result': 'Successfully reset sign for dead-simple API'}

@app.route('/send')
def send():
    params = bottle.request.query
    
    if 'label' in params:
        label = params.label.lower()
    else:
        label = 'A'
    
    if 'text' not in params:
        raise HTTPError(400, 'Need text to send!')
    
    text = params.text
    color = constants.get_color(params.get('color', 'NONE'))
    mode = constants.get_mode(params.get('mode', 'ROTATE'))
    
    text = color + text
    text = general.parse_colors(text)
    
    if label == 'A':
        text = parse_labels(text)
        
    memory_entry = sign.find_entry(read_raw_memory_table(), label)
    if len(text) > memory_entry['size']:
        raise HTTPError(400, 'Not enough space allocated. Need at least %s bytes.' % len(text))
    
    if label == 'A':
        sign.write(alphasign.Text(text, label=label, mode=mode))
    else:
        sign.write(alphasign.String(text, label=label))
    
    return {'result': 'Sucessfully sent text'}
    
    