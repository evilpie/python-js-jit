# -*- coding: utf-8 -*-

"""
    pyasm.data
    ~~~~~~~~~~ 

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import CFUNCTYPE, cast, c_void_p, c_char_p

class Data(object): pass

class Function(Data):
    def __init__(self, fun):
        self.fun = fun
    
    @property
    def address(self):
        return cast(self.fun, c_void_p).value

class String(Data):
    def __init__(self, value):
        self.value = value
        self.address = cast(c_char_p(value), c_void_p).value

def function(restype, *argtypes):
    type = CFUNCTYPE(restype, *argtypes)
    def _decorator(fun):
        return Function(type(fun))
    return _decorator
