'''
Created on Dec 10, 2012

@author: nathan
'''

from ..base import BaseForwarder
from layers import SignDirect

class SignDirectForwarder(BaseForwarder):
    def __init__(self, sign):
        self.sign_direct = SignDirect(sign)