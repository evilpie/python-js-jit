# -*- coding: utf-8 -*-

"""
    pyasm.instructions.string
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Instruction, AssemblyError
from pyasm.data import Data
from pyasm.base import Register, Address
from pyasm.registers import ByteRegister, DWordRegister, QWordRegister, esp

@Instruction.producer
def cmova(inst, target, source):
    if isinstance(target, Register):
        if isinstance(source, Register):
            inst.chr(0x0f)
            inst.chr(0x47)
            inst.modrm(3, target, source)
        else:
            raise AssemblyError('incompatible source type: %s' % type(source))
    else:
        raise AssemblyError('incompatible target type: %s' % type(source))

@Instruction.producer
def cmovb(inst, target, source):
    if isinstance(target, Register):
        if isinstance(source, Register):
            inst.chr(0x0f)
            inst.chr(0x42)
            inst.modrm(3, target, source)
        else:
            raise AssemblyError('incompatible source type: %s' % type(source))
    else:
        raise AssemblyError('incompatible target type: %s' % type(source))

@Instruction.producer
def mov(inst, target, source, width=32):
    source_is_addr = isinstance(source, Address)
    target_is_addr = isinstance(target, Address)

    if isinstance(target, QWordRegister) or isinstance(source, QWordRegister):
        #probably not correct as the REX byte is more complex
        inst.chr(0x48)

    if source_is_addr and target_is_addr:
        raise AssemblyError('cannot transfer address to address')

    if source_is_addr or target_is_addr:
        post = lambda: None
        if source_is_addr:
            if isinstance(target, ByteRegister):
                opcode = 0x8a
            elif isinstance(target, DWordRegister):
                opcode = 0x8b
            offset = source.offset
            arg1, arg2 = target, source
        elif target_is_addr:
            if isinstance(source, ByteRegister):
                opcode = 0x88
            elif isinstance(source, DWordRegister):
                opcode = 0x89
            elif isinstance(source, int):
                value = source
                source = 0
                if width == 32:
                    opcode = 0xc7
                    post = lambda: inst.pack('i', value)
                elif width == 8:
                    opcode = 0xc6
                    post = lambda: inst.chr(value)
            offset = target.offset
            arg1, arg2 = source, target

        inst.chr(opcode)
        inst.modrmoff(arg1, arg2, offset)
        post()
    else:
        if isinstance(source, int):
            if isinstance(target, ByteRegister):
                inst.chr(0xb0 + target.index)
                inst.chr(source)
            if isinstance(target, DWordRegister):
                inst.chr(0xb8 + target.index)
                inst.pack('i', source)

        elif isinstance(source, long):
            inst.chr(0xb8 + target.index)
            inst.pack('I', source)
        elif isinstance(source, Register):
            if isinstance(source, ByteRegister):
                inst.chr(0x88)
            elif isinstance(source, DWordRegister):
                inst.chr(0x89)
            inst.modrm(3, source, target)
        elif isinstance(source, Data):
            inst.chr(0xb8 + target.index)
            inst.pack('I', source.address)
        else:
            raise AssemblyError('incompatible source type: %s' % type(source))

@Instruction.producer
def lea(s, target, source, offset):
    if isinstance(target, Register):
        if isinstance(source, Register):
            s.chr(0x8d)
            s.modrmoff(target, source, offset)
        else:
            raise AssemblyError('incompatible source type: %s' % type(source))
        pass
    else:
        raise AssemblyError('incompatible target type: %s' % type(target))

