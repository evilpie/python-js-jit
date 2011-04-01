# -*- coding: utf-8 -*-
"""
    inc 
    ~~~

    :copyright: 2008 by Henri Tuhola <henri.tuhola@gmail.com>
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from ctypes import c_long

from pyasm import Program
from pyasm.instructions import mov, inc, ret
from pyasm.registers import rax, eax, rdi

if __name__ == '__main__':
    prog = Program(
        mov(rax, rdi),
        inc(rax),
        ret()
    )
    fun = prog.compile(c_long, [c_long])
    assert fun(1234) == 1235
