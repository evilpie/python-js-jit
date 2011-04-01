# -*- coding: utf-8 -*-

"""
    pyasm.instructions.control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Instruction, AssemblyError
from pyasm.base import Register, Address
from pyasm.registers import eax

@Instruction.producer
def cmp(inst, target, source, width=32):
    source_is_register = isinstance(source, Register)

    if target is eax and (not source_is_register):
        if isinstance(source, int):
            inst.chr(0x3d)
            inst.pack('i', source)
        else:
            raise AssemblyError('unsupported source operand: %s' % source)
    elif isinstance(target, Register):
        if source_is_register:
            inst.chr(0x39)
            inst.modrm(3, source, target)
        elif isinstance(source, int):
            if width == 32:
                inst.chr(0x81)
                inst.modrm(3, 7, target)
                inst.pack('i', source)
            elif width == 8:
                inst.chr(0x80)
                inst.modrm(3, 7, target)
                inst.chr(source)
        else:
            raise AssemblyError('unsupported source operand: %s' % source)
    elif isinstance(target, Address):
        if source_is_register:
            raise AssemblyError('unsupported source operand: %s' % target)
        elif isinstance(source, int):
            if width == 32:
                inst.chr(0x81)
            elif width == 8:
                inst.chr(0x80)

            inst.modrmoff(7, target, target.offset)

            if width == 32:
                inst.pack('i', source)
            elif width == 8:
                inst.pack('b', source)
        else:
            raise AssemblyError('unsupported source operand: %s' % target)

    else:
        raise AssemblyError('unsupported target operand: %s' % target)

@Instruction.producer
def test(inst, target, source):
    source_is_register = isinstance(source, Register)

    if target is eax and (not source_is_register):
        if isinstance(source, int):
            inst.chr(0xa9)
            inst.pack('i', source)
        else:
            raise('foo')
    elif isinstance(target, Register):
        if source_is_register:
            inst.chr(0x85)
            inst.modrm(3, target, source)

        if isinstance(source, int):

            inst.chr(0xf7)
            inst.modrm(3, 7, target)

            inst.pack('i', source)

