# -*- coding: utf-8 -*-

"""
    pyasm.instructions.stack
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Instruction, AssemblyError
from pyasm.base import Register

@Instruction.producer
def push(inst, value):
    if isinstance(value, Register):
        inst.chr(0x50+value.index)
    elif isinstance(value, int):
        inst.chr(0x68)
        inst.pack('i', value)
    elif isinstance(value, float):
        inst.chr(0x68)
        inst.pack('f', value)
    else:
        raise AssemblyError('unsupported push argument: %s' % value)

@Instruction.producer
def pop(inst, value):
    if isinstance(value, Register):
        inst.chr(0x58+value.index)
    else:
        raise AssemblyError('unsupported pop argument: %s' % value)

@Instruction.producer
def pushfd(inst):
    inst.chr(0x9c)

@Instruction.producer
def popfd(inst):
    inst.chr(0x9d)
