# -*- coding: utf-8 -*-

"""
    pyasm.instructions.fpu
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from pyasm import Instruction, AssemblyError
from pyasm.base import Register, Address
from pyasm.registers import QWordRegister, eax, st

def transfer(name, opcode, st1, st2, modrm_target):
    def _impl(inst, operand):
        if isinstance(operand, Address):
            inst.chr(0xd9)
            inst.modrmoff(modrm_target, operand, operand.offset)
        elif isinstance(operand, st):
            inst.chr(st1)
            inst.chr(st2 + operand.index)
        else:
            raise AssemblyError('unsupported operand: %s: %s' % (name, operand))
    _impl.__name__ = name
    return Instruction.producer(_impl)

def operation(name, st0_target, st0_source, modrm_target):
    def _impl(inst, target, source=None):
        if source:
            if isinstance(target, st) and isinstance(source, st):
                if target.index == 0:
                    inst.chr(0xd8)
                    inst.chr(st0_target + source.index)
                elif source.index == 0:
                    inst.chr(0xdc)
                    inst.chr(st0_source + target.index)
                else:
                    raise AssemblyError('%s with registers must involve st(0)' % name)
            else:
                raise AssemblyError('unsupported operands: %s: %s %s' %  (name, target, source))
        else:
            operand = target
            if isinstance(operand, Address):
                inst.chr(0xd8)
                inst.modrmoff(modrm_target, operand, operand.offset)
            else:
                raise AssemblyError('unsupported operand: %s: %s' % (name, operand))
    _impl.__name__ = name
    return Instruction.producer(_impl)

def popping(name, opcode):
    def _impl(inst, operand=None):
        if operand: 
            if isinstance(operand, st):
                inst.chr(0xde)
                inst.chr(opcode+operand.index)
            else:
                raise AssemblyError('unsupported operand: %s: %s' % (name, operand))
        else:
            inst.chr(0xde)
            inst.chr(opcode+1)
    _impl.__name__ = name
    
    return Instruction.producer(_impl)

@Instruction.producer
def fcomi(inst, operand):
    if isinstance(operand, st):
        inst.chr(0xdb)
        inst.chr(0xf0 + operand.index)
    else:
        raise AssemblyError('unsupported operand: %s' % operand)

@Instruction.producer
def fdecstp(inst):
    inst.chr(0xd9)
    inst.chr(0xf6)

@Instruction.producer
def fsqrt(inst):
    inst.chr(0xd9)
    inst.chr(0xfa)

@Instruction.producer
def fcmovb(inst, register):
    if isinstance(register, st):
        inst.chr(0xda)
        inst.chr(0xc0 + register.index)
    else:
        raise AssemblyError('unsupported operand: fcmovbe: %s' % register)

fld     = transfer('fld'    , 0xc0, 0xd9, 0xc0, 0)
fst     = transfer('fst'    , 0xd0, 0xdd, 0xd0, 2)
fstp    = transfer('fstp'   , 0xd8, 0xdd, 0xd8, 3)

fadd    = operation('fadd'  , 0xc0, 0xc0, 0)
fsub    = operation('fsub'  , 0xe0, 0xe8, 4)
fsubr   = operation('fsubr' , 0xe8, 0xe0, 5)
fmul    = operation('fmul'  , 0xc8, 0xc8, 1)
fdiv    = operation('fdiv'  , 0xf0, 0xf8, 6)
fdivr   = operation('fdivr' , 0xf8, 0xf0, 7)

faddp   = popping('faddp'   , 0xc0)
fdivp   = popping('fdivp'   , 0xf8)
fmulp   = popping('fmulp'   , 0xc8)
