
from pyasm import Instruction, AssemblyError
from pyasm.base import Register, Address
from pyasm.registers import Register, XMMRegister

@Instruction.producer
def movd(inst, target, source):

    if isinstance(target, XMMRegister) or isinstance(source, XMMRegister):
        inst.chr(0x66)

    inst.chr(0x0f)

    if isinstance(target, XMMRegister):
        inst.chr(0x6e)
        inst.modrm(3, target, source)

    if isinstance(source, XMMRegister):
        inst.chr(0x7e)
        inst.modrm(3, target, source)

@Instruction.producer
def movups(inst, target, source):

    inst.chr(0x0f)
    if isinstance(target, Address):
        inst.chr(0x11)
    else:
        inst.chr(0x10)
    inst.modrm(3, target, source)


@Instruction.producer
def cvtsi2sd(inst, target, source):
    #int to double
    inst.chr(0xf2)
    inst.chr(0x0f)
    inst.chr(0x2a)
    inst.modrm(3, target, source)

@Instruction.producer
def cvttsd2si(inst, target, source):
    #double to int
    inst.chr(0xf2)
    inst.chr(0x0f)
    inst.chr(0x2c)
    inst.modrm(3, target, source)

@Instruction.producer
def cvtsi2ss(inst, target, source):
    #int to float
    inst.chr(0xf3)
    inst.chr(0x0f)
    inst.chr(0x2a)
    inst.modrm(3, target, source)

@Instruction.producer
def addpd(inst, target, source):

    inst.chr(0x66)
    inst.chr(0x0f)
    inst.chr(0x58)
    inst.modrm(3, target, source)

@Instruction.producer
def addsd(inst, target, source):

    inst.chr(0xf2)
    inst.chr(0x0f)
    inst.chr(0x58)
    inst.modrm(3, target, source)

@Instruction.producer
def pxor(inst, target, source):

    inst.chr(0x66)
    inst.chr(0x0f)
    inst.chr(0xef)
    inst.modrm(3, target, source)

@Instruction.producer
def paddd(inst, target, source):

    inst.chr(0x66)
    inst.chr(0x0f)
    inst.chr(0xfe)
    inst.modrm(3, target, source)

@Instruction.producer
def psubd(inst, target, source):

    inst.chr(0x66)
    inst.chr(0x0f)
    inst.chr(0xfa)
    inst.modrm(3, target, source)

@Instruction.producer
def subps(inst, target, source):

    inst.chr(0x0f)
    inst.chr(0x5c)
    inst.modrm(3, target, source)

@Instruction.producer
def addps(inst, target, source):

    inst.chr(0x0f)
    inst.chr(0x58)
    inst.modrm(3, target, source)
