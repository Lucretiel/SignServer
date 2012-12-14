'''
Created on Dec 6, 2012

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