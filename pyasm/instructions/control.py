# -*- coding: utf-8 -*-

"""
    pyasm.instructions.control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Instruction, AssemblyError
from pyasm.base import Label, OffsetSensitive, Register

@Instruction.producer
def nop(inst):
    inst.chr(0x90)

@Instruction.producer
def ret(inst):
    inst.chr(0xc3)

@Instruction.producer
def interrupt(inst, code):
    inst.chr(0xcd)
    inst.chr(code)

@OffsetSensitive.producer
def jmp(inst, offset, operand):
    if isinstance(operand, Label):
        distance = operand.offset - offset - 5
        inst.chr(0xe9)
        inst.pack('i', distance)

@OffsetSensitive.producer
def call(inst, offset, operand):
    if isinstance(operand, Register):
        inst.chr(0xff)
        inst.modrm(3, 2, operand)
    else:
        raise AssemblyError('unsupported operand: %s' % operand)

def conditional_jump(name, opcode):
    def _impl(inst, offset, operand):
        if isinstance(operand, Label):
            distance = operand.offset - offset - 6
            inst.chr(0x0f)
            inst.chr(opcode)
            inst.pack('i', distance)
        else:
            raise AssemblyError('unsupported operand: %s' % operand)
    _impl.__name__ = name
    return OffsetSensitive.producer(_impl)

jl  = conditional_jump('jl'     , 0x8c)
jle = conditional_jump('jle'    , 0x8e)
jg  = conditional_jump('jg'     , 0x8f)
jb  = conditional_jump('jb'     , 0x82)
je  = conditional_jump('je'     , 0x84)
jne = conditional_jump('jne'    , 0x85)
jae = conditional_jump('jae'    , 0x83)
jbe = conditional_jump('jbe'    , 0x86)
ja  = conditional_jump('ja'     , 0x87)

jc  = conditional_jump('jc'     , 0x82)
jnc = conditional_jump('jnc'    , 0x83)

jz  = conditional_jump('jz'     , 0x84)
jnz = conditional_jump('jnz'    , 0x85)
