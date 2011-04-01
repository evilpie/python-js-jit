# -*- coding: utf-8 -*-
"""
    add
    ~~~

    :copyright: 2008 by Henri Tuhola <henri.tuhola@gmail.com>
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_long

from pyasm import Program
from pyasm.instructions import mov, add, ret
from pyasm.registers import rax, rdi

if __name__ == '__main__':
    prog = Program(
        mov(rax, rdi),
        add(rax, 10),
        ret()
    )

    fun = prog.compile(restype=c_long, argtypes=[c_long])
    assert fun(1234) == 1244
