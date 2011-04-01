# -*- coding: utf-8 -*-

"""
    pyasm.base
    ~~~~~~~~~~ 

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

import struct
import sys

if sys.version_info[0] < 3:
    bytes = str

class Register(object):
    def __init__(self, name, index):
        self.name = name
        self.index = index

    @property
    def addr(self):
        return Address(self) 

    def __repr__(self):
        return self.name

class Address(object):
    def __init__(self, register, offset=0):
        self.register = register
        self.offset = offset
        self.index = register.index
        self.name = register.name
    
    def __add__(self, offset):
        return Address(self.register, offset)

    def __sub__(self, offset):
        return Address(self.register, -offset)

    def __repr__(self):
        if self.offset > 0:
            return '%s.addr+%i' % (self.register, self.offset)
        elif self.offset < 0:
            return '%s.addr%i' % (self.register, self.offset)
        else:
            return '%s.addr' % self.register

class Stream(object):
    def __init__(self):
        self.buffer = bytes()

    def chr(self, value):
        self.buffer += struct.pack('B', value)
    
    def modrm(self, mod, arg1, arg2):
        if isinstance(arg1, (Register, Address)):
            arg1 = arg1.index
        elif arg1 is None:
            arg1 = 0
            
        if isinstance(arg2, (Register, Address)):
            arg2 = arg2.index
        elif arg2 is None:
            arg2 = 0

        self.chr(mod<<6 | arg1<<3 | arg2)
    
    def pack(self, fmt, *values):
        self.buffer += struct.pack(fmt, *values)

    def modrmoff(self, target, source, offset):
        is_source_register = isinstance(source, (Register, Address))
        can_do_zero = not(is_source_register and source.name == 'ebp')

        if offset == 0 and can_do_zero:
            self.modrm(0, target, source)
            if is_source_register and source.name == 'esp':
                self.chr(0x24)
        elif abs(offset) < 128:
            self.modrm(1, target, source)
            self.pack('b', offset)
        else:
            self.modrm(2, target, source)
            self.pack('i', offset)

class Instruction(object):
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.name = fun.__name__
        self.args = args
        self.kwargs = kwargs
        self.offset = 0

    def __repr__(self):
        return '%-20s %s %s' % (
            ' '.join(c.encode('hex') for c in self.compile()),
            self.name,
            ', '.join(map(str, self.args)),
        )

    def compile(self):
        stream = Stream()
        self.fun(stream, *self.args, **self.kwargs)
        return stream.buffer

    @classmethod
    def producer(cls, fun):
        def _decorator(*args, **kwargs):
            instruction = cls(fun, *args, **kwargs)
            return instruction
        return _decorator

class OffsetSensitive(Instruction):
    def compile(self):
        stream = Stream()
        self.fun(stream, self.offset, *self.args, **self.kwargs)
        return stream.buffer
    
class Label(object):
    def __init__(self, name=None):
        self.name = name
        self.offset = 0

    def compile(self):
        return ''

    def __repr__(self):
        if self.name:
            return 'label %s' % self.name
        else:
            if self.offset:
                return 'label #%i' % self.offset
            else:
                return 'label %i' % id(self)

