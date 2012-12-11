'''
Created on Dec 6, 2012

@author: nathan

Fixed functionality related to sign file labels. Validation, etc
'''

valid_labels = [chr(i) for i in xrange(int('0x20', 0), int('0x7F', 0))]
priority_text_label = '0'
counter_labels = [str(i) for i in xrange(1, 6)]