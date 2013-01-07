'''
Created on Jan 5, 2013

@author: nathan
'''

import multiprocessing
import alphasign
import constants
from .. import general
from . import mongo_plugin
from sign import sign
from datetime import datetime

receive_message, send_message = multiprocessing.Pipe(False)

def send_request(command, clump_id):
    send_message.send({'command': command, 'id': clump_id})
    
def request_new_active(clump_id):
    '''Sets the active to the ID
    '''
    send_request('SET', clump_id)
    
def request_update_active(clump_id):
    '''Update the id.
    '''
    send_request('UPDATE', clump_id)
    
def request_previous_active(clump_id=None):
    '''Moves the active to the previous active. If clump_id is given, only move
    it if it is currently active
    '''
    send_request('PREVIOUS', clump_id)
    
def request_clear_active():
    '''Wipe the sign
    '''
    send_request('CLEAR', None)

def make_objects(clump, names=None):
    '''Given a clump, generate the objects to be written to the sign.
    '''
    labels = iter(constants.sign_controller_labels)
    text_label = next(labels)
    fields = clump['fields']
    text = clump['text']
    
    label_map = {name: (next(labels), 'STRING' if 'text' in field else 'DOTS')
                 for name, field in sorted(fields.iteritems())}
    
    #parse colors
    text = general.parse_colors(text)
    
    #parse labels
    def label_replacer(flag):
        if flag in label_map:
            label, type = label_map[flag]
            if type == 'STRING':
                return alphasign.String(label=label).call()
            elif type == 'DOTS':
                return alphasign.Dots(label=label).call()
        return None
    text = general.parse_generic(text, label_replacer)
    
    yield alphasign.Text(text, text_label,
                         mode=constants.get_mode(clump['mode']))
    
    if names is not None:
        label_map = {name: val for name, val in label_map.iteritems() if name in names}
        
    #Run through each named subfield
    for fieldname, (label, fieldtype) in label_map.iteritems():
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

class SignInteractor(multiprocessing.Process):
    def __init__(self, queue):
        super(SignInteractor, self).__init__()
        self.daemon = True
        self.queue = queue #This is actually a Pipe endpoint. Consider renaming.
        self.db = mongo_plugin.get_mongo()
        
    def run(self):
        try:
            while True:
                message = self.queue.recv()
                clump_id = message['id']
                if message['command'] == 'SET':
                    self.set_active(clump_id)
                
                elif message['command'] == 'UPDATE':
                    if self.db.active.find_one({'clump_id': clump_id}):
                        self.set_active(clump_id)
                        
                elif message['command'] == 'PREVIOUS':
                    if clump_id is None or self.db.active.find_one({'clump_id': clump_id}):
                        self.set_previous_active()
                
                elif message['command'] == 'CLEAR':
                    self.clear_active()
                    
        except EOFError:
            pass
        finally:
            self.queue.close()
            
    def delete_if_temporary(self, clump_id):
        self.db.clumps.find_and_modify({'_id': clump_id, 'temporary': True}, remove=True)
            
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
            self.write_to_sign(clump)
            old = self.db.active.find_one()['clump_id']
            self.db.active.insert({'clump_id': clump_id})
            if old != clump_id:
                self.delete_if_temporary(old)
            
    def clear_active(self):
        empty_clump = {'name': '', 'text': '', 'mode': 'HOLD', 'fields': {}}
        self.write_to_sign(empty_clump)
        old = self.db.active.find_one()['clump_id']
        self.delete_if_temporary(old)
        self.db.active.insert({'clump_id': None})
            
    def set_previous_active(self):
        '''Finds the last most recently displayed clump and displays it.
        '''
        current = self.db.active.find_one()['clump_id']
        self.db.clumps.update({'_id': current}, {'$unset': {'last_displayed': ''}})
                
        previous = self.db.clumps.find({'last_displayed': {'$exists': True}}).sort('last_displayed', -1).limit(1)
        if previous.count(True) > 0: #count(True) counts WITH limit(1)
            previous = previous[0]
            self.set_active(previous['_id'])
        else:
            self.clear_active()
        
    def write_to_sign(self, clump):
        objects = list(make_objects(clump))
        sign.allocate(objects)
        for obj in objects: sign.write(obj)
        sign.set_run_sequence([objects[0]])
        
sign_interactor_process = SignInteractor(receive_message)

def start():
    sign_interactor_process.start()