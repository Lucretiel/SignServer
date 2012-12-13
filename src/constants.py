'''
Created on Dec 6, 2012

@author: nathan

Fixed functionality related to sign file labels. Validation, etc
'''

from alphasign import colors, modes

valid_labels = [chr(i) for i in xrange(int('20', 16), int('7F', 16))]
priority_text_label = '0'
counter_labels = [str(i) for i in xrange(1, 6)]
dead_simple_string_labels = [chr(i) for i in xrange(ord('a'), ord('z') + 1)]

def get_from_module(name, module, default):
    if name not in dir(module):
        return default
    return module.__getattribute__(name)
 
def get_color(color):
    return get_from_module(color.upper(), colors, default='')

def get_mode(mode):
    return get_from_module(mode.upper(), modes, default=modes.ROTATE)