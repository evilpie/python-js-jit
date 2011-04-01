# -*- coding: utf-8 -*-

"""
    pyasm.instructions.math
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Instruction, AssemblyError
from pyasm.base import Register, Address
from pyasm.registers import QWordRegister, DWordRegister, ByteRegister, eax

def operation(name, eax_int, reg_int, reg_addr, reg_reg_32, reg_reg_8, addr_int, addr_reg):
    def _impl(inst, target, source, width=32):
        if isinstance(source, int):
            if target is eax and source > 255:
                inst.chr(eax_int)
                inst.pack('i', source)
            elif isinstance(target, Register):
                if source <= 255:
                    inst.chr(0x83)
                    inst.modrm(3, reg_int, target)
                    inst.pack('b', source)
                else:
                    inst.chr(0x81)
                    inst.modrm(3, reg_int, target)
                    inst.pack('i', source)
            elif isinstance(target, Address):
                if width == 8:
                    inst.chr(0x80)
                    inst.modrm(1, addr_int, target)
                    inst.chr(0)
                    inst.pack('b', source)
                elif width == 32:
                    inst.chr(0x81)
                    inst.modrm(1, addr_int, target)
                    inst.chr(0)
                    inst.pack('i', source)
            else:
                raise AssemblyError('incompatible target operand: %s' % source)
        elif isinstance(source, Address):
            inst.chr(reg_addr)
            inst.modrmoff(target, source, source.offset)
        elif isinstance(source, Register):
            if isinstance(target, Register):
                if isinstance(source, DWordRegister):
                    inst.chr(reg_reg_32)
                    inst.modrm(3, target, source)
                elif isinstance(source, ByteRegister):
                    inst.chr(reg_reg_8)
                    inst.modrm(3, source, target)
            elif isinstance(target, Address):
                if abs(target.offset) < 128:
                    inst.chr(addr_reg)
                    inst.modrm(1, source, target)
                    inst.pack('b', target.offset)
                else:
                    inst.chr(addr_reg+1)
                    inst.modrm(2, source, target)
                    inst.pack('i', target.offset)
            else:
                raise AssemblyError('incompatible target operand: %s' % target)
        else:
            raise AssemblyError('incompatible source operand: %s' % source)

    _impl.__name__ = name
    return Instruction.producer(_impl)

add = operation('add', 0x0f, 0, 0x03, 0x03, 0x00, 0, 0x00)
sub = operation('sub', 0x2d, 5, 0x2b, 0x2b, 0x28, 5, 0x28)

@Instruction.producer
def inc(inst, operand, width=32):
    if isinstance(operand, Register):
        if isinstance(operand, QWordRegister):
            inst.chr(0x48)
        inst.chr(0xff)
        inst.chr(0xc0 + operand.index)
    elif isinstance(operand, Address):
        if width == 8:
            inst.chr(0xfe)
        elif width == 32:
            inst.chr(0xff)

        inst.modrmoff(0, operand, operand.offset)

    else:
        raise AssemblyError('inc not implemented for non registers')

@Instruction.producer
def dec(inst, operand, width=32):
    if isinstance(operand, Register):
        if isinstance(operand, QWordRegister):
            inst.chr(0x48)
        inst.chr(0xff)
        inst.chr(0xc8 + operand.index)
    elif isinstance(operand, Address):
        if width == 8:
            inst.chr(0xfe)
        elif width == 32:
            inst.chr(0xff)

        inst.modrmoff(1, operand, operand.offset)

    else:
        raise AssemblyError('dec not implemented for non registers')

@Instruction.producer
def mul(inst, register, width=32):
    if width == 32:
        inst.chr(0xf7)
        inst.modrm(3, 4, register)
    elif width == 8:
        inst.chr(0xf6)
        inst.modrm(3, 4, register)
    else:
        raise AssemblyError('unsupported bit width: %s' % width)

@Instruction.producer
def neg(inst, register, width=32):
    if width == 32:
        inst.chr(0xf7)
        inst.modrm(3, 3, register)
    elif width == 8:
        inst.chr(0xf6)
        inst.modrm(3, 3, register)
    else:
        raise AssemblyError('unsupported bit width: %s' % width)


@Instruction.producer
def not_(inst, register, width=32):
    if width == 32:
        inst.chr(0xf7)
        inst.modrm(3, 2, register)
    elif width == 8:
        inst.chr(0xf6)
        inst.modrm(3, 2, register)
    else:
        raise AssemblyError('unsupported bit width: %s' % width)


@Instruction.producer
def shr(inst, target, source):
    if isinstance(source, int):
        if source == 1:
            inst.chr(0xd1)
            inst.modrm(3, 5, target)
        else:
            inst.chr(0xc1)
            inst.modrm(3, 2, target)
            inst.pack('b', source)

@Instruction.producer
def shl(inst, target, source):
    if isinstance(source, int):
        if source == 1:
            inst.chr(0xd1)
            inst.modrm(3, 4, target)
        else:
            inst.chr(0xc1)
            inst.modrm(5, 2, target)
            inst.pack('b', source)

@Instruction.producer
def xor(inst, target, source):
    if isinstance(target, Register):
        if target is eax:
            inst.chr(0x35)
            inst.pack('i', source)

        if isinstance(source, Register):
            inst.chr(0x31)
            inst.modrm(3, target, source)


