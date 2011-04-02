# -*- coding: utf-8 -*-

"""
    pyasm.program
    ~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import cast, CFUNCTYPE, c_int, c_char, c_long, c_void_p, POINTER
import ctypes
import os

def iterable(obj):
    if isinstance(obj, list):
        return True
    elif isinstance(obj, tuple):
        return True

class Program(object):
    def __init__(self, *instructions):
        self.instructions = list()
        self.add(*instructions)

    def add(self, *instructions):
        for instruction in instructions:
            if iterable(instruction):
                self.add(*instruction)
            else:
                self.instructions.append(instruction)

    def __repr__(self):
        instructions ='\n'.join(
            '    %s' % instruction
            for instruction in self.instructions
        )
        return 'Program(\n%s\n)' % instructions

    def compile(self, restype=None, argtypes=()):
        return compile(self.instructions, restype, argtypes)

read_write_execute = 1 | 2 | 4
read_write = 1 | 2

class Executable(object):
    def __init__(self, buffer, restype=None, argtypes=()):
        self.buffer = buffer
        self.size = len(buffer)

        if os.name == 'nt':
            VirtualAlloc = ctypes.windll.kernel32.VirtualAlloc
            VirtualAlloc.argtypes = [c_void_p, c_long, c_long, c_long]
            VirtualAlloc.restype = c_void_p

            self.address = VirtualAlloc(0, self.size, 0x1000, 0x40)
        else:
            self.address = ctypes.pythonapi.valloc(self.size)
            ctypes.pythonapi.mprotect(self.address, self.size, read_write_execute)

        self.ptr = cast(c_void_p(self.address), POINTER(c_char * self.size))

        self.ptr.contents[:] = buffer
        functype = CFUNCTYPE(restype, *argtypes)
        self.fptr = functype(self.address)


    def __call__(self, *args):
        return self.fptr(*args)

    def __del__(self):
        if os.name == 'nt':
            VirtualFree = ctypes.windll.kernel32.VirtualFree
            VirtualFree.argtypes = [c_void_p, c_long, c_long]
            VirtualFree.restype = c_int

            VirtualFree(self.address, self.size, 0x8000)
        else:
            ctypes.pythonapi.mprotect(self.address, self.size, read_write)
            ctypes.pythonapi.free(self.address)


def compile(instructions, restype=None, argtypes=()):
    offset = 0
    for instruction in instructions:
        instruction.offset = offset
        bytes = instruction.compile()
        offset += len(bytes)

    buffer = ''.join(
        instruction.compile() for instruction in instructions
    )
    return Executable(buffer, restype, argtypes)
