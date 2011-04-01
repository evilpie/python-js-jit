# -*- coding: utf-8 -*-

"""
    copy
    ~~~~

    :copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import POINTER, c_float, c_int

from pyasm import Program, target
from pyasm.instructions import push, mov, add, ret, pop
from pyasm.registers import eax, edx, esp, ebp, rax, rdi, rsi

def test():
    a = (c_float*10)()
    a[2] = 2501.1
    b = (c_float*10)()
    b[2] = 1234.0

    prog = Program(
        push(ebp),
        mov(ebp, esp),
        mov(eax, ebp.addr+8),
        add(eax, 8),
        mov(edx, ebp.addr+12),
        add(edx, 8),
        mov(edx, edx.addr),
        mov(eax.addr, edx),
        pop(ebp),
        ret(),
    )
    fun = prog.compile(argtypes=[POINTER(c_float), POINTER(c_float)])
    fun(a, b)
    assert a[2] == b[2]

if __name__ == '__main__':
    test()
