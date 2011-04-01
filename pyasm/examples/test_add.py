# -*- coding: utf-8 -*-

"""
    add
    ~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_int

from pyasm import Program
from pyasm.instructions import push, mov, ret, pop, add
from pyasm.registers import eax, ebx, esp, ebp

def test_reg_int():
    prog = Program(
        push(ebp),
        mov(ebp, esp),
        mov(eax, ebp.addr+8),
        add(eax, 10),
        pop(ebp),
        ret(),
    )
    fun = prog.compile(c_int, [c_int])
    assert fun(1234) == 1244

def test_reg_reg():
    prog = Program(
        push(ebp),
        mov(ebp, esp),
        mov(eax, ebp.addr+8),
        mov(ebx, ebp.addr+12),
        add(eax, ebx),
        pop(ebp),
        ret(),
    )
    fun = prog.compile(c_int, [c_int, c_int])
    assert fun(1234, 20) == 1254

if __name__ == '__main__':
    test_reg_int()
    test_reg_reg()
