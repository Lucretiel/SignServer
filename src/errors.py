'''
Created on Dec 11, 2012

@author: nathan
'''

class SignServerException(Exception):
    '''Base class for all Sign Server errors'''
    pass
    
class HandlingError(SignServerException):
    '''Base class for errors associated with an HTTP error code. They should
    have an error code and enough data to create a reasonable data message'''
    def __init__(self, *args):
        if args:
            super(HandlingError, self).__init__(args)
        else:
            super(HandlingError, self).__init__(self.general_message)

class BadResource(HandlingError):
    general_message = 'The resource does not exist'
    code = 404

class BadMethod(HandlingError):
    general_message = 'The resource exists, but the method is invalid'
    code = 405
    
class BadData(HandlingError):
    general_message = 'The resource was presented unexpected data.'
    code = 400
    
class JSONParseError(BadData):
    general_message = 'Error parsing JSON'
    pass

class MissingField(BadData):
    general_message = 'Some expected field in the json was missing'
    pass

class BadLabel(BadData):
    general_message = 'A label was invalid somehow'
    pass

def convertKeyError(func):
    '''Function decorator to have any KeyErrors that escape the function
    converted into MissingField errors'''
    
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyError as e:
            raise MissingField('Expected field was missing', *e.args)
        
    return wrapper