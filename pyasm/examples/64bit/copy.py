# -*- coding: utf-8 -*-
"""
    copy
    ~~~~

    :copyright: 2008 by Henri Tuhola <henri.tuhola@gmail.com>
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import POINTER, c_float, c_long

from pyasm import Program
from pyasm.instructions import mov, ret
from pyasm.registers import eax, rdi, rsi

if __name__ == '__main__':
    a = (c_float*10)()
    a[2] = 2501.1
    b = (c_float*10)()
    b[2] = 1234.0

    prog = Program(
        mov(eax, rsi.addr+8),
        mov(rdi.addr+8, eax),
        ret()
    )
    fun = prog.compile(argtypes=[POINTER(c_float),POINTER(c_float)])
    fun(a, b)
    assert a[2] == b[2]
