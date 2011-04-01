# -*- coding: utf-8 -*-

"""
    cmp
    ~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_int, c_float, c_float

from pyasm import Program, Label
from pyasm.macro import log
from pyasm.instructions import mov, cmp, ret, pushfd, popfd, pop, push, fld, fcomi, ja, fstp
from pyasm.registers import eax, ebp, esp, st

CF = 2**0 #on if less then 
OF = 2**11
SF = 2**7
ZF = 2**6 #on if equal
AF = 2**4
PF = 2**2

def test():
    prog = Program(
        push(ebp),
        mov(ebp, esp),
        mov(eax, ebp.addr+8),
        cmp(eax, 100),
        pushfd(),
        pop(eax),
        pop(ebp),
        ret(),
    )
    fun = prog.compile(c_int, [c_int])

    assert fun(99) & CF
    assert fun(100) & ZF
    assert not (fun(101) & CF  or fun(101) & ZF)

def test_float():
    label = Label()
    prog = Program(
        push(ebp),
        mov(ebp, esp),
        fld(ebp.addr+8),
        fld(ebp.addr+12),
        fcomi(st(1)),
        fstp(st(0)),
        fstp(st(0)),
        ja(label),
        mov(eax, 1),
        pop(ebp),
        ret(),
        label,
        mov(eax, 2),
        pop(ebp),
        ret(),
    )
    fun = prog.compile(c_int, [c_float, c_float])
    assert fun(10, 20) == 2
    assert fun(20, 10) == 1

if __name__ == '__main__':
    test_float()
