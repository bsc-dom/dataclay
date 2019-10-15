
""" Class description goes here. """

'''
Created on 29 dic. 2017

@author: daniel
'''
from io import BytesIO

from dataclay.serialization.python.lang.VLQIntegerWrapper import VLQIntegerWrapper


# TODO: Finish byte buffer instead of using wrappers in code
class DataClayByteBuffer():
    
    buffer = BytesIO()
    
    def writeInt(self, i):
        VLQIntegerWrapper().write(buffer, i)
